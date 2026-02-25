import json
import re
import time
from datetime import datetime, timezone
from typing import Any

import requests

from src.config import API_BASE_URL, API_QUOTA_URL


class LLMError(Exception):
    pass


class QuotaExceededError(LLMError):
    pass


class LLMClient:
    def __init__(self, api_key: str, model: str, base_url: str = API_BASE_URL):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def check_quota(self) -> dict[str, Any] | None:
        try:
            response = self.session.get(API_QUOTA_URL, timeout=30)
            if response.status_code == 200:
                data = response.json()
                sub = data.get("subscription", {})
                limit = sub.get("limit", 0)
                used = sub.get("requests", 0)
                renews_at = sub.get("renewsAt", "")
                if used < limit:
                    return {"available": limit - used, "renewsAt": renews_at}
                return None
            return {"available": 1, "renewsAt": ""}
        except requests.RequestException:
            return {"available": 1, "renewsAt": ""}

    def wait_for_quota(self, max_wait_minutes: int = 360) -> bool:
        quota_info = self.check_quota()
        if quota_info is not None:
            return True

        try:
            response = self.session.get(API_QUOTA_URL, timeout=30)
            data = response.json()
            renews_at_str = data.get("subscription", {}).get("renewsAt", "")
            if renews_at_str:
                renews_at = datetime.fromisoformat(renews_at_str.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                wait_seconds = (renews_at - now).total_seconds()
                if 0 < wait_seconds <= max_wait_minutes * 60:
                    print(
                        f"Quota exceeded. Waiting {wait_seconds/60:.0f} minutes "
                        f"until renewal at {renews_at_str}..."
                    )
                    time.sleep(wait_seconds + 10)
                    return True
        except Exception:
            pass

        start_time = time.time()
        while time.time() - start_time < max_wait_minutes * 60:
            if self.check_quota() is not None:
                print("Quota renewed! Resuming...")
                return True
            elapsed = (time.time() - start_time) / 60
            print(f"Quota still exceeded, waiting... ({elapsed:.0f}min elapsed)")
            time.sleep(60)
        return False

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_retries: int = 5,
    ) -> dict[str, Any]:
        if self.check_quota() is None:
            if not self.wait_for_quota():
                print("Quota wait timed out, attempting request anyway...")

        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                    },
                    timeout=180,
                )

                if response.status_code == 429:
                    wait_time = min(2 ** (attempt + 1), 120)
                    print(
                        f"Rate limited (attempt {attempt+1}/{max_retries}). "
                        f"Waiting {wait_time}s..."
                    )
                    time.sleep(wait_time)

                    if attempt >= 2:
                        self.wait_for_quota()
                    continue

                if response.status_code != 200:
                    print(
                        f"API error {response.status_code} "
                        f"(attempt {attempt+1}/{max_retries})"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return {"action": "reject", "reasoning": "API error, defaulting to reject"}

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_json_response(content)

            except json.JSONDecodeError:
                print(
                    f"Bad JSON from LLM (attempt {attempt+1}/{max_retries}), retrying..."
                )
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return {"action": "reject", "reasoning": "JSON parse failed, defaulting to reject"}

            except LLMError as e:
                print(
                    f"LLM error: {e} (attempt {attempt+1}/{max_retries}), retrying..."
                )
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {"action": "reject", "reasoning": f"LLM error: {e}"}

            except requests.RequestException as e:
                print(
                    f"Request error: {e} (attempt {attempt+1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {"action": "reject", "reasoning": f"Request failed: {e}"}

        return {"action": "reject", "reasoning": "Max retries exceeded"}

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[^{}]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            raise LLMError(f"Failed to parse JSON response. Content: {content[:200]}")
