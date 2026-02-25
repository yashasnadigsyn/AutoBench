import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class PromptResponseLog:
    def __init__(
        self,
        day: int,
        prompt: str,
        response: Optional[Dict[str, Any]],
        action_taken: str,
        ride_details: Optional[Dict[str, Any]] = None,
    ):
        self.day = day
        self.timestamp = datetime.now().isoformat()
        self.prompt = prompt
        self.response = response
        self.action_taken = action_taken
        self.ride_details = ride_details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "timestamp": self.timestamp,
            "prompt": self.prompt,
            "response": self.response,
            "action_taken": self.action_taken,
            "ride_details": self.ride_details,
        }


class DailyLog:
    def __init__(self, day: int, day_of_week: str):
        self.day = day
        self.day_of_week = day_of_week
        self.shift_start: Optional[str] = None
        self.shift_end: Optional[str] = None
        self.ended_location: str = "Majestic"
        self.start_time_response: Optional[Dict[str, Any]] = None
        self.prompt_response_logs: List[PromptResponseLog] = []
        self.rides_accepted: List[Dict[str, Any]] = []
        self.rides_rejected: List[Dict[str, Any]] = []
        self.gross: float = 0.0
        self.fuel: float = 0.0
        self.deadhead: float = 0.0

    def add_start_response(
        self, prompt: str, response: Dict[str, Any], start_time: str
    ):
        self.shift_start = start_time
        self.prompt_response_logs.append(
            PromptResponseLog(
                day=self.day,
                prompt=prompt,
                response=response,
                action_taken="start_shift",
            )
        )

    def add_ride_prompt_response(
        self,
        prompt: str,
        response: Dict[str, Any],
        action: str,
        ride_details: Optional[Dict[str, Any]] = None,
    ):
        self.prompt_response_logs.append(
            PromptResponseLog(
                day=self.day,
                prompt=prompt,
                response=response,
                action_taken=action,
                ride_details=ride_details,
            )
        )

        if ride_details:
            if action == "accept":
                self.rides_accepted.append(ride_details)
                self.gross += ride_details.get("fare", 0)
                self.fuel += ride_details.get("fuel_cost", 0)
            elif action == "reject":
                self.rides_rejected.append(ride_details)

    def finalize(self, shift_end: str, ended_location: str, deadhead: float):
        self.shift_end = shift_end
        self.ended_location = ended_location
        self.deadhead = deadhead

    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "day_of_week": self.day_of_week,
            "shift_start": self.shift_start,
            "shift_end": self.shift_end,
            "ended_location": self.ended_location,
            "start_time_response": self.start_time_response,
            "rides_accepted": self.rides_accepted,
            "rides_rejected": self.rides_rejected,
            "gross": self.gross,
            "fuel": self.fuel,
            "deadhead": self.deadhead,
            "net_profit": self.gross - self.fuel - self.deadhead,
            "prompt_response_logs": [
                log.to_dict() for log in self.prompt_response_logs
            ],
        }


class BenchmarkLogger:
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.run_dir = (
            self.output_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.daily_logs: List[DailyLog] = []
        self.current_daily_log: Optional[DailyLog] = None

    def start_day(self, day: int, day_of_week: str) -> DailyLog:
        self.current_daily_log = DailyLog(day, day_of_week)
        return self.current_daily_log

    def finalize_day(self, shift_end: str, ended_location: str, deadhead: float):
        if self.current_daily_log:
            self.current_daily_log.finalize(shift_end, ended_location, deadhead)
            self.daily_logs.append(self.current_daily_log)
            self.current_daily_log = None

    def log_summary(self, final_results: Dict[str, Any]):
        summary_path = self.run_dir / "summary.json"
        with open(summary_path, "w") as f:
            json.dump(final_results, f, indent=2)

    def log_daily_logs(self):
        daily_logs_path = self.run_dir / "daily_logs.json"
        logs_data = [log.to_dict() for log in self.daily_logs]
        with open(daily_logs_path, "w") as f:
            json.dump(logs_data, f, indent=2)

    def log_trace(self, final_results: Dict[str, Any]):
        trace_path = self.run_dir / "trace.txt"
        with open(trace_path, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("AutoBench Execution Trace\n")
            f.write("=" * 60 + "\n\n")

            for log in self.daily_logs:
                f.write(f"\n--- Day {log.day} ({log.day_of_week}) ---\n")
                f.write(f"Shift: {log.shift_start} to {log.shift_end}\n")
                f.write(f"Ended at: {log.ended_location}\n")
                f.write(f"Rides accepted: {len(log.rides_accepted)}\n")
                f.write(f"Rides rejected: {len(log.rides_rejected)}\n")
                f.write(f"Gross: ₹{log.gross:.0f}\n")
                f.write(f"Fuel: ₹{log.fuel:.0f}\n")
                f.write(f"Deadhead: ₹{log.deadhead:.0f}\n")
                f.write(f"Net: ₹{log.gross - log.fuel - log.deadhead:.0f}\n")

                f.write("\n--- Prompt/Response Log ---\n")
                for pr_log in log.prompt_response_logs:
                    f.write(f"\n[{pr_log.timestamp}] Action: {pr_log.action_taken}\n")
                    f.write(f"PROMPT:\n{pr_log.prompt}\n")
                    f.write(f"RESPONSE:\n{json.dumps(pr_log.response, indent=2)}\n")
                    if pr_log.ride_details:
                        f.write(
                            f"RIDE DETAILS: {json.dumps(pr_log.ride_details, indent=2)}\n"
                        )
                    f.write("-" * 40 + "\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write("FINAL RESULTS\n")
            f.write("=" * 60 + "\n")
            f.write(f"Total Days: {final_results.get('total_days', 0)}\n")
            f.write(f"Final Balance: ₹{final_results.get('final_balance', 0):.0f}\n")
            f.write(f"Total Rides: {final_results.get('total_rides', 0)}\n")
            f.write(
                f"Best Day: Day {final_results.get('best_day', {}).get('day', 'N/A')} (₹{final_results.get('best_day', {}).get('profit', 0):.0f})\n"
            )
            f.write(
                f"Worst Day: Day {final_results.get('worst_day', {}).get('day', 'N/A')} (₹{final_results.get('worst_day', {}).get('profit', 0):.0f})\n"
            )

    def get_run_dir(self) -> Path:
        return self.run_dir
