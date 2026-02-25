import argparse
import os
from dotenv import load_dotenv

from src.config import DEFAULT_DAYS, DEFAULT_MODEL, DEFAULT_OUTPUT_DIR, API_BASE_URL
from src.benchmark.runner import run_benchmark


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="AutoBench: Bengaluru Auto-Rickshaw Agentic Benchmark"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Model name to use for LLM (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"Number of days to simulate (default: {DEFAULT_DAYS})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for results (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for LLM (default: from OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=API_BASE_URL,
        help=f"Base URL for LLM API (default: {API_BASE_URL})",
    )

    args = parser.parse_args()

    api_key = args.api_key or os.getenv("OPENAI_API_KEY") or os.getenv("SYNTHETIC_API_KEY")
    if not api_key:
        raise ValueError(
            "API key not provided. Set OPENAI_API_KEY or SYNTHETIC_API_KEY "
            "environment variable, or pass --api-key argument."
        )

    print("Starting AutoBenchmark...")
    print(f"Model: {args.model}")
    print(f"Days: {args.days}")
    print(f"Output: {args.output}")
    print("-" * 40)

    results = run_benchmark(
        model=args.model,
        api_key=api_key,
        days=args.days,
        base_url=args.base_url,
        output_dir=args.output,
    )

    print("\nFinal Results:")
    print(f"  Total Days: {results['total_days']}")
    print(f"  Final Balance: ₹{results['final_balance']:.0f}")
    print(f"  Total Rides: {results['total_rides']}")
    if results.get("best_day"):
        print(
            f"  Best Day: Day {results['best_day']['day']} (₹{results['best_day']['profit']:.0f})"
        )
    if results.get("worst_day"):
        print(
            f"  Worst Day: Day {results['worst_day']['day']} (₹{results['worst_day']['profit']:.0f})"
        )


if __name__ == "__main__":
    main()
