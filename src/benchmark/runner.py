import json
import random
from typing import Dict, Any, List, Optional, Callable

from src.config import DAY_NAMES, RAIN_PROBABILITY
from src.llm.client import LLMClient
from src.llm.prompts import (
    get_system_prompt,
    get_start_day_prompt,
    get_multi_ride_prompt,
    parse_llm_response,
)
from src.simulation.state import GameState
from src.simulation.dispatcher import generate_multiple_pings, get_idle_wait_minutes
from src.benchmark.history import compress_history
from src.output.logger import BenchmarkLogger

BENCHMARK_SEED = 42
OPTION_LABELS = ["A", "B", "C", "D", "E"]
MAX_CONSECUTIVE_FAILURES = 5


class ModelFailedError(Exception):
    pass


def _is_fallback_response(response: dict) -> bool:
    reasoning = response.get("reasoning", "")
    return any(tag in reasoning for tag in [
        "API error", "JSON parse failed", "LLM error",
        "Request failed", "Max retries exceeded",
    ])


def run_benchmark(
    model: str,
    api_key: str,
    days: int = 30,
    base_url: str = "https://api.synthetic.new/openai/v1",
    output_dir: str = "results",
    day_callback: Optional[Callable[[dict], None]] = None,
) -> Dict[str, Any]:
    rng = random.Random(BENCHMARK_SEED)

    client = LLMClient(api_key=api_key, model=model, base_url=base_url)
    state = GameState()
    logger = BenchmarkLogger(output_dir=output_dir)

    history_log = ""
    best_day = {"day": 0, "profit": float("-inf")}
    worst_day = {"day": 0, "profit": float("inf")}
    total_rides_all_days = 0
    daily_results = []
    consecutive_failures = 0

    for day in range(1, days + 1):
        day_of_week = (day - 1) % 7

        is_rainy = rng.random() < RAIN_PROBABILITY
        rain_tag = " 🌧️" if is_rainy else ""

        daily_log = logger.start_day(day, DAY_NAMES[day_of_week])

        system_msg = {"role": "system", "content": get_system_prompt(history_log)}
        day_messages: List[Dict[str, str]] = [system_msg]

        start_prompt = get_start_day_prompt(
            day=day,
            day_name=DAY_NAMES[day_of_week],
            bank_balance=state.bank_balance,
            is_rainy=is_rainy,
        )
        day_messages.append({"role": "user", "content": start_prompt})

        start_response = client.chat(messages=day_messages)

        if _is_fallback_response(start_response):
            consecutive_failures += 1
            print(f"LLM failed ({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})")
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                raise ModelFailedError(
                    f"Model failed {MAX_CONSECUTIVE_FAILURES} times in a row. Skipping."
                )
        else:
            consecutive_failures = 0

        day_messages.append({"role": "assistant", "content": json.dumps(start_response)})
        daily_log.start_time_response = start_response

        start_time = start_response.get("start_time", "07:00")
        if not _is_valid_time(start_time):
            start_time = "07:00"

        state.start_day(day, start_time)

        full_start_prompt = system_msg["content"] + "\n\n" + start_prompt
        daily_log.add_start_response(full_start_prompt, start_response, start_time)

        print(f"\nDay {day} ({DAY_NAMES[state.day_of_week]}{rain_tag}): Starting at {start_time}")

        shift_ended_by_llm = False

        while state.shift_remaining_minutes > 0:
            idle_wait = get_idle_wait_minutes(state.current_time, state.current_location)

            ride_requests = generate_multiple_pings(
                current_time=state.current_time,
                day_of_week=state.day_of_week,
                current_location=state.current_location,
                count=3,
                rng=rng,
                is_rainy=is_rainy,
            )

            if not ride_requests:
                state.advance_time(idle_wait)
                continue

            rides_for_prompt = []
            for req in ride_requests:
                rides_for_prompt.append({
                    "origin": req.origin,
                    "destination": req.destination,
                    "distance_km": req.distance_km,
                    "fare": req.expected_fare,
                    "eta_min": int(req.simulated_duration_min),
                })

            ride_prompt = get_multi_ride_prompt(
                current_time=state.current_time,
                current_location=state.current_location,
                rides=rides_for_prompt,
                shift_remaining=state.get_shift_remaining_str(),
                is_rainy=is_rainy,
            )

            day_messages.append({"role": "user", "content": ride_prompt})

            response = client.chat(messages=day_messages)

            if _is_fallback_response(response):
                consecutive_failures += 1
                print(f"LLM failed ({consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})")
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    raise ModelFailedError(
                        f"Model failed {MAX_CONSECUTIVE_FAILURES} times in a row. Skipping."
                    )
            else:
                consecutive_failures = 0

            day_messages.append({"role": "assistant", "content": json.dumps(response)})

            action, reasoning = parse_llm_response(response)
            action_upper = action.strip().upper()
            selected_ride = None
            selected_index = -1
            if action_upper in OPTION_LABELS[:len(ride_requests)]:
                selected_index = OPTION_LABELS.index(action_upper)
                selected_ride = ride_requests[selected_index]

            all_ride_details = []
            for i, req in enumerate(ride_requests):
                all_ride_details.append({
                    "label": OPTION_LABELS[i],
                    "origin": req.origin,
                    "destination": req.destination,
                    "distance_km": req.distance_km,
                    "fare": req.expected_fare,
                    "traffic_eta_min": int(req.simulated_duration_min),
                    "fuel_cost": req.fuel_cost,
                })

            ride_log_details = {
                "offered_rides": all_ride_details,
                "selected": action_upper,
            }

            if selected_ride is not None:
                if selected_ride.simulated_duration_min > state.shift_remaining_minutes:
                    action = "reject"
                    reasoning = "FORCED REJECT: Ride duration exceeds remaining shift time"
                    state.advance_time(idle_wait)
                    print(
                        f"  [{state.current_time}] FORCED REJECT: "
                        f"{selected_ride.origin} -> {selected_ride.destination} "
                        f"(exceeds shift)"
                    )
                    ride_log_details["forced_reject"] = True
                else:
                    ride = state.accept_ride(
                        destination=selected_ride.destination,
                        distance_km=selected_ride.distance_km,
                        base_duration_min=selected_ride.base_duration_min,
                        simulated_duration_min=selected_ride.simulated_duration_min,
                        fare=selected_ride.expected_fare,
                        fuel_cost=selected_ride.fuel_cost,
                    )
                    ride_log_details["actual_fare"] = ride.fare
                    ride_log_details["actual_fuel"] = ride.fuel_cost
                    ride_log_details["profit"] = ride.profit
                    action = f"accept_{action_upper}"

                    print(
                        f"  [{state.current_time}] ACCEPT ({action_upper}): "
                        f"{selected_ride.origin} -> {selected_ride.destination} "
                        f"(₹{ride.profit:.0f} profit)"
                    )

            elif action_upper == "REJECT":
                state.advance_time(idle_wait)
                dests = ", ".join(r.destination for r in ride_requests)
                print(
                    f"  [{state.current_time}] REJECT ALL: [{dests}] "
                    f"(reason: {reasoning})"
                )

            elif action_upper == "END_SHIFT":
                deadhead = state.end_shift(
                    idle_wait_min=0, is_rainy=is_rainy, rng=rng
                )
                shift_ended_by_llm = True
                print(
                    f"  [{state.current_time}] END SHIFT at {state.current_location} "
                    f"(deadhead: ₹{deadhead:.0f})"
                )
                daily_log.add_ride_prompt_response(
                    prompt=ride_prompt,
                    response=response,
                    action="end_shift",
                    ride_details=ride_log_details,
                )
                break
            else:
                state.advance_time(idle_wait)
                print(
                    f"  [{state.current_time}] INVALID ACTION '{action}' - treating as reject"
                )
                action = "reject"

            daily_log.add_ride_prompt_response(
                prompt=ride_prompt,
                response=response,
                action=action,
                ride_details=ride_log_details,
            )

        if not shift_ended_by_llm:
            deadhead = state.end_shift(
                idle_wait_min=0, is_rainy=is_rainy, rng=rng
            )
        else:
            deadhead = state.today_deadhead

        daily_log.finalize(state.current_time, state.current_location, deadhead)
        logger.finalize_day(state.current_time, state.current_location, deadhead)

        total_rides_all_days += state.today_rides

        net_profit = state.today_gross - state.today_fuel - state.today_deadhead
        if net_profit > best_day["profit"]:
            best_day = {"day": day, "profit": net_profit}
        if net_profit < worst_day["profit"]:
            worst_day = {"day": day, "profit": net_profit}

        daily_results.append({
            "day": day,
            "day_name": DAY_NAMES[state.day_of_week],
            "rides": state.today_rides,
            "gross": round(state.today_gross, 2),
            "fuel": round(state.today_fuel, 2),
            "deadhead": round(state.today_deadhead, 2),
            "net_profit": round(net_profit, 2),
            "cumulative_balance": round(state.bank_balance, 2),
            "is_rainy": is_rainy,
        })

        if day_callback is not None:
            day_callback(daily_results[-1])

        print(
            f"  Day {day} ended: {state.today_rides} rides, "
            f"₹{net_profit:.0f} profit, Balance: ₹{state.bank_balance:.0f}"
        )

        day_history = compress_history(
            day=day,
            day_of_week=state.day_of_week,
            shift_start=state.shift_start_time,
            shift_end=state.current_time,
            ended_location=state.current_location,
            rides=state.rides_history,
            today_gross=state.today_gross,
            today_fuel=state.today_fuel,
            today_deadhead=state.today_deadhead,
            total_bank_balance=state.bank_balance,
            is_rainy=is_rainy,
        )
        history_log = history_log + "\n" + day_history if history_log else day_history

    final_results = {
        "total_days": days,
        "final_balance": state.bank_balance,
        "total_rides": total_rides_all_days,
        "best_day": best_day if best_day["day"] > 0 else None,
        "worst_day": worst_day if worst_day["day"] > 0 else None,
        "daily_results": daily_results,
    }

    logger.log_summary(final_results)
    logger.log_daily_logs()
    logger.log_trace(final_results)

    print(f"\n{'=' * 50}")
    print("Benchmark Complete!")
    print(f"Final Balance: ₹{state.bank_balance:.0f}")
    print(f"Results saved to: {logger.get_run_dir()}")
    print(f"{'=' * 50}")

    return final_results


def _is_valid_time(time_str: str) -> bool:
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            return False
        hour = int(parts[0])
        minute = int(parts[1])
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except (ValueError, AttributeError):
        return False
