import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.config import API_BASE_URL
from src.benchmark.runner import run_benchmark, ModelFailedError

MODELS = [
    "hf:MiniMaxAI/MiniMax-M2.5",
    "hf:zai-org/GLM-4.7",
    "hf:nvidia/Kimi-K2.5-NVFP4",
    "hf:openai/gpt-oss-120b",
    "hf:Qwen/Qwen3-Coder-480B-A35B-Instruct",
]

DAYS = 7
CSV_PATH = Path("benchmark_comparison.csv")
CSV_HEADERS = [
    "model",
    "day",
    "day_name",
    "rides",
    "gross",
    "fuel",
    "deadhead",
    "net_profit",
    "cumulative_balance",
    "is_rainy",
]


def load_existing_results() -> dict[str, set[int]]:
    completed: dict[str, set[int]] = {}
    if not CSV_PATH.exists():
        return completed

    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            model = row["model"]
            day = int(row["day"])
            if model not in completed:
                completed[model] = set()
            completed[model].add(day)

    return completed


def append_day_to_csv(model: str, day_data: dict):
    file_exists = CSV_PATH.exists()

    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "model": model,
                "day": day_data["day"],
                "day_name": day_data["day_name"],
                "rides": day_data["rides"],
                "gross": day_data["gross"],
                "fuel": day_data["fuel"],
                "deadhead": day_data["deadhead"],
                "net_profit": day_data["net_profit"],
                "cumulative_balance": day_data["cumulative_balance"],
                "is_rainy": day_data["is_rainy"],
            }
        )


def get_model_short_name(model: str) -> str:
    return model.split("/")[-1]


def main():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("SYNTHETIC_API_KEY")
    if not api_key:
        print("No API key found. Set OPENAI_API_KEY or SYNTHETIC_API_KEY.")
        sys.exit(1)

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    completed = load_existing_results()

    total_models = len(MODELS)
    for model_idx, model in enumerate(MODELS, 1):
        short_name = get_model_short_name(model)

        done_days = completed.get(model, set())
        if len(done_days) >= DAYS:
            print(f"\n{'=' * 60}")
            print(
                f"[{model_idx}/{total_models}] OK {short_name} — already completed, skipping"
            )
            print(f"{'=' * 60}")
            continue

        start_from = max(done_days) + 1 if done_days else 1
        if start_from > 1:
            print(f"\n{'=' * 60}")
            print(
                f"[{model_idx}/{total_models}] REF {short_name} — "
                f"resuming from day {start_from} (days {sorted(done_days)} done)"
            )
            print(f"{'=' * 60}")
        else:
            print(f"\n{'=' * 60}")
            print(f"[{model_idx}/{total_models}] RUN {short_name} — starting fresh")
            print(f"{'=' * 60}")

        def on_day_complete(day_data, _model=model, _done=done_days):
            day_num = day_data["day"]
            if day_num not in _done:
                append_day_to_csv(_model, day_data)
                print(
                    f"Saved Day {day_num} to CSV: "
                    f"₹{day_data['net_profit']:.0f} profit, "
                    f"₹{day_data['cumulative_balance']:.0f} balance"
                )

        try:
            results = run_benchmark(
                model=model,
                api_key=api_key,
                days=DAYS,
                base_url=API_BASE_URL,
                output_dir=f"results/{short_name}",
                day_callback=on_day_complete,
            )

            print(f"\n{short_name} complete! Balance: ₹{results['final_balance']:.0f}")

        except KeyboardInterrupt:
            print(f"\n\nInterrupted during {short_name}. Progress saved to CSV.")
            print("Run this script again to resume.")
            sys.exit(0)

        except ModelFailedError as e:
            print(f"\nSkipping {short_name}: {e}")
            print("Continuing to next model...")
            continue

        except Exception as e:
            print(f"\nError running {short_name}: {e}")
            print("Continuing to next model...")
            continue

    print(f"\n{'=' * 60}")
    print("All models complete!")
    print(f"Results saved to: {CSV_PATH}")
    print("Run 'uv run python visualizer.py' to see the comparison chart.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
