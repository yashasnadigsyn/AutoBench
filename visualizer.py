import csv
import sys
from pathlib import Path

CSV_PATH = Path("benchmark_comparison.csv")

MODEL_DISPLAY_NAMES = {
    "hf:MiniMaxAI/MiniMax-M2.5": "MiniMax-M2.5",
    "hf:Qwen/Qwen3-Coder-480B-A35B-Instruct": "Qwen3-Coder",
    "hf:nvidia/Kimi-K2.5-NVFP4": "Kimi-K2.5",
    "hf:zai-org/GLM-4.7": "GLM-4.7",
    "hf:openai/gpt-oss-120b": "GPT-oss-120B",
}

MODEL_LOGOS = {
    "hf:MiniMaxAI/MiniMax-M2.5": "logos/minimax.png",
    "hf:Qwen/Qwen3-Coder-480B-A35B-Instruct": "logos/qwen.png",
    "hf:nvidia/Kimi-K2.5-NVFP4": "logos/kimi.png",
    "hf:zai-org/GLM-4.7": "logos/zai.png",
    "hf:openai/gpt-oss-120b": "logos/openai.png",
}

MODEL_COLORS = {
    "hf:MiniMaxAI/MiniMax-M2.5": "#E84393",
    "hf:Qwen/Qwen3-Coder-480B-A35B-Instruct": "#6C5CE7",
    "hf:nvidia/Kimi-K2.5-NVFP4": "#00B894",
    "hf:zai-org/GLM-4.7": "#E17055",
    "hf:openai/gpt-oss-120b": "#0984E3",
}

FALLBACK_COLORS = [
    "#E84393",
    "#6C5CE7",
    "#00B894",
    "#E17055",
    "#0984E3",
    "#FDCB6E",
    "#636E72",
    "#D63031",
    "#00CEC9",
    "#A29BFE",
]


def load_data() -> dict[str, list[dict]]:
    if not CSV_PATH.exists():
        print(f"CSV not found: {CSV_PATH}")
        print("Run 'uv run python benchmark_all.py' first.")
        sys.exit(1)

    models: dict[str, list[dict]] = {}
    with open(CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            model = row["model"]
            if model not in models:
                models[model] = []
            models[model].append(
                {
                    "day": int(row["day"]),
                    "day_name": row["day_name"],
                    "rides": int(row["rides"]),
                    "gross": float(row["gross"]),
                    "fuel": float(row["fuel"]),
                    "deadhead": float(row["deadhead"]),
                    "net_profit": float(row["net_profit"]),
                    "cumulative_balance": float(row["cumulative_balance"]),
                    "is_rainy": row["is_rainy"] == "True",
                }
            )

    for model in models:
        models[model].sort(key=lambda x: x["day"])

    return models


def get_display_name(model: str) -> str:
    return MODEL_DISPLAY_NAMES.get(model, model.split("/")[-1])


def get_color(model: str, idx: int) -> str:
    return MODEL_COLORS.get(model, FALLBACK_COLORS[idx % len(FALLBACK_COLORS)])


def plot_chart(models_data: dict[str, list[dict]]):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        import matplotlib.image as mpimg
        from matplotlib.offsetbox import OffsetImage, AnnotationBbox
    except ImportError:
        print("matplotlib not installed. Install with: uv add matplotlib")
        sys.exit(1)

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    model_summaries = []
    endpoints: list[tuple] = []

    for idx, (model, days) in enumerate(models_data.items()):
        display_name = get_display_name(model)
        x = [d["day"] for d in days]
        y = [d["cumulative_balance"] for d in days]
        color = get_color(model, idx)

        ax.plot(
            x,
            y,
            linewidth=2.5,
            label=display_name,
            color=color,
            zorder=3,
            solid_capstyle="round",
        )

        logo_path = MODEL_LOGOS.get(model)
        endpoint = y[-1] if y else 0
        endpoints.append(
            (model, endpoint, color, logo_path, x[-1] if x else 0, display_name)
        )

        total_rides = sum(d["rides"] for d in days)
        model_summaries.append(
            {
                "name": display_name,
                "balance": y[-1] if y else 0,
                "rides": total_rides,
                "days": len(days),
            }
        )

    endpoints.sort(key=lambda e: e[1])
    MIN_GAP_PT = 28
    offsets_y: list[float] = []
    for i, (model_key, yval, color_e, lpath, xval, dname) in enumerate(endpoints):
        desired = 0.0
        if offsets_y:
            prev_yval = endpoints[i - 1][1]
            if abs(yval - prev_yval) < (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.04:
                desired = offsets_y[-1] + MIN_GAP_PT
        offsets_y.append(desired)

    for i, (model_key, yval, color_e, lpath, xval, dname) in enumerate(endpoints):
        if lpath and Path(lpath).exists():
            try:
                logo_img = mpimg.imread(lpath)
                imagebox = OffsetImage(logo_img, zoom=0.10)
                imagebox.image.axes = ax
                ab = AnnotationBbox(
                    imagebox,
                    (xval, yval),
                    xybox=(35, offsets_y[i]),
                    xycoords="data",
                    boxcoords="offset points",
                    frameon=True,
                    bboxprops=dict(
                        boxstyle="circle,pad=0.3",
                        facecolor="white",
                        edgecolor=color_e,
                        linewidth=2.5,
                    ),
                    arrowprops=dict(arrowstyle="-", color=color_e, lw=1.5),
                    zorder=5,
                )
                ax.add_artist(ab)
            except Exception as e:
                print(f"  Warning: Could not load logo for {dname}: {e}")
                ax.plot(xval, yval, "o", color=color_e, markersize=10, zorder=5)
        else:
            ax.plot(xval, yval, "o", color=color_e, markersize=10, zorder=5)

    ax.set_xlabel("Day", fontsize=13, color="#333333", fontweight="medium", labelpad=10)
    ax.set_ylabel(
        "Cumulative Bank Balance (₹)",
        fontsize=13,
        color="#333333",
        fontweight="medium",
        labelpad=10,
    )
    ax.set_title(
        "AutoBench: Cumulative Profit Over 7 Days",
        fontsize=18,
        color="#222222",
        fontweight="bold",
        loc="center",
        pad=25,
    )
    ax.text(
        0.5,
        1.01,
        "Simulated auto-rickshaw earnings across LLM drivers",
        transform=ax.transAxes,
        ha="center",
        fontsize=11,
        color="#888888",
    )

    ax.tick_params(colors="#555555", labelsize=11, length=0)
    ax.spines["bottom"].set_color("#DDDDDD")
    ax.spines["left"].set_color("#DDDDDD")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, _: f"₹{val:,.0f}"))

    max_days = max(len(days) for days in models_data.values())
    ax.set_xticks(range(1, max_days + 1))
    ax.set_xticklabels(
        [str(i) for i in range(1, max_days + 1)],
        fontsize=11,
        color="#555555",
    )
    ax.set_xlim(0.5, max_days + 1.5)

    ax.set_axisbelow(True)
    ax.grid(
        True,
        axis="both",
        alpha=0.5,
        color="#D5D5D5",
        linewidth=0.8,
        linestyle="--",
        zorder=0,
    )

    ax.legend(
        fontsize=11,
        loc="upper right",
        frameon=False,
        labelcolor="#333333",
    )

    plt.tight_layout(pad=2.0)

    output_path = Path("benchmark_results.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    print(f"Chart saved to: {output_path}")

    model_summaries.sort(key=lambda x: x["balance"], reverse=True)
    print(f"\n{'=' * 55}")
    print("AutoBench Leaderboard (7 Days)")
    print(f"{'=' * 55}")
    print(f"{'Rank':<6}{'Model':<22}{'Balance':>12}{'Rides':>8}")
    print(f"{'-' * 55}")
    for i, m in enumerate(model_summaries, 1):
        rank = f"  {i}" if i > 3 else f" {i}"
        print(f"{rank:<6}{m['name']:<22}₹{m['balance']:>10,.0f}{m['rides']:>8}")
    print(f"{'=' * 55}")


def main():
    print("Loading benchmark results...")
    models_data = load_data()
    print(f"Found {len(models_data)} models with data")

    for model, days in models_data.items():
        name = get_display_name(model)
        print(f"  {name}: {len(days)} days completed")

    plot_chart(models_data)


if __name__ == "__main__":
    main()
