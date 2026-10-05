"""
EcoTravel Advisor – Response Latency Measurement Script
========================================================
MSc Assignment: Stage 3 – Performance Evaluation

Measures chatbot response latency through the Rasa REST webhook
endpoint used by the actual frontend.

Design decisions:
- Uses time.perf_counter() for high-resolution wall-clock timing
- Performs warm-up requests (excluded from statistics)
- Runs 10 measured iterations per scenario
- Records every individual measurement
- Separates local interactions from external-API-dependent ones
- Does NOT discard slow measurements
- Does NOT expose API credentials

Usage:
    python scratch/test_latency.py
"""

import csv
import json
import os
import statistics
import sys
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Optional: matplotlib for chart generation
try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Try requests from venv or system
try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not available. Install it first.")
    sys.exit(1)


# ── CONFIGURATION ────────────────────────────────────────────────

RASA_WEBHOOK_URL = "http://127.0.0.1:5005/webhooks/rest/webhook"
REQUEST_TIMEOUT = 30  # seconds
WARMUP_REQUESTS = 2   # number of warm-up requests before measured runs
MEASURED_ITERATIONS = 10  # number of timed runs per scenario
TARGET_LATENCY_S = 3.0    # requirement: under 3 seconds

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


# ── SCENARIO DEFINITIONS ────────────────────────────────────────

LOCAL_SCENARIOS = [
    {
        "name": "A. Greeting",
        "message": "hello",
        "category": "local",
        "description": "Simple greeting – Rasa NLU + response template",
    },
    {
        "name": "B. Start trip planning",
        "message": "/plan_trip",
        "category": "local",
        "description": "Intent trigger for trip planning form activation",
    },
    {
        "name": "C. Sustainable activities request",
        "message": "recommend sustainable activities",
        "category": "local",
        "description": "Triggers action_recommend_activities (local JSON data, no external API)",
    },
    {
        "name": "D. Carbon offset programmes",
        "message": "recommend carbon offset programmes",
        "category": "local",
        "description": "Triggers action_recommend_carbon_offsets (local JSON data, no external API)",
    },
    {
        "name": "E. Bot challenge",
        "message": "are you a bot?",
        "category": "local",
        "description": "Simple utter_iamabot response – pure Rasa response",
    },
    {
        "name": "F. Fallback (ambiguous input)",
        "message": "xyzzy flurble nonsense 12345",
        "category": "local",
        "description": "Deliberately unsupported input to trigger fallback mechanism",
    },
]

EXTERNAL_SCENARIOS = [
    {
        "name": "G. Flight search (external-dependent)",
        "message": "/ask_flights",
        "category": "external-dependent",
        "description": "Triggers action_search_flights – attempts Amadeus API then falls back to local data",
    },
    {
        "name": "H. Eco accommodation (external-dependent)",
        "message": "/ask_accommodation",
        "category": "external-dependent",
        "description": "Triggers action_recommend_accommodation – attempts Amadeus API then falls back",
    },
]


# ── MEASUREMENT FUNCTIONS ────────────────────────────────────────

def send_rasa_message(
    message: str,
    sender_id: str,
    timeout: int = REQUEST_TIMEOUT,
) -> Tuple[Optional[List[Dict]], float, Optional[str]]:
    """
    Send a message to the Rasa REST webhook and measure response time.

    Returns:
        (response_data, elapsed_seconds, error_message)
    """
    payload = {
        "sender": sender_id,
        "message": message,
    }

    start = time.perf_counter()
    try:
        resp = requests.post(
            RASA_WEBHOOK_URL,
            json=payload,
            timeout=timeout,
        )
        elapsed = time.perf_counter() - start

        if resp.ok:
            data = resp.json()
            return data, elapsed, None
        else:
            return None, elapsed, f"HTTP {resp.status_code}"

    except requests.exceptions.Timeout:
        elapsed = time.perf_counter() - start
        return None, elapsed, "Request timed out"
    except requests.exceptions.ConnectionError:
        elapsed = time.perf_counter() - start
        return None, elapsed, "Connection refused – is Rasa server running?"
    except requests.exceptions.RequestException as e:
        elapsed = time.perf_counter() - start
        return None, elapsed, f"Request error: {str(e)}"


def get_response_summary(data: Optional[List[Dict]]) -> str:
    """Extract a brief summary of the bot response."""
    if not data:
        return "No response"
    texts = []
    for msg in data:
        text = msg.get("text", "")
        if text:
            preview = text[:80].replace("\n", " ")
            if len(text) > 80:
                preview += "..."
            texts.append(preview)
    return " | ".join(texts) if texts else "Empty response"


def calculate_statistics(times: List[float]) -> Dict[str, Any]:
    """Calculate min, mean, median, max, p95 from a list of elapsed times."""
    if not times:
        return {
            "min": None, "mean": None, "median": None,
            "max": None, "p95": None, "count": 0,
        }

    sorted_times = sorted(times)
    n = len(sorted_times)
    p95_idx = int(n * 0.95)
    if p95_idx >= n:
        p95_idx = n - 1

    return {
        "min": round(min(sorted_times), 4),
        "mean": round(statistics.mean(sorted_times), 4),
        "median": round(statistics.median(sorted_times), 4),
        "max": round(max(sorted_times), 4),
        "p95": round(sorted_times[p95_idx], 4),
        "count": n,
    }


def assess_compliance(stats: Dict[str, Any]) -> str:
    """Assess whether measured latency meets the <3s target."""
    if stats["count"] == 0:
        return "NO DATA"
    if stats["max"] is not None and stats["max"] > TARGET_LATENCY_S:
        if stats["p95"] is not None and stats["p95"] <= TARGET_LATENCY_S:
            return f"CONDITIONAL PASS (p95 OK, max {stats['max']:.3f}s exceeded)"
        return "FAIL"
    return "PASS"


# ── MAIN TEST RUNNER ─────────────────────────────────────────────

def run_scenarios(
    scenarios: List[Dict],
    label: str,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Run all scenarios with warm-up and measured iterations.
    Returns (raw_results, summary_results).
    """
    raw_results: List[Dict] = []
    summary_results: List[Dict] = []

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

    for scenario in scenarios:
        name = scenario["name"]
        message = scenario["message"]
        category = scenario["category"]
        desc = scenario["description"]

        print(f"\n  Testing: {name}")
        print(f"  Message: \"{message}\"")
        print(f"  Category: {category}")

        # ── Warm-up ──
        print(f"  Warm-up ({WARMUP_REQUESTS} requests)...", end=" ", flush=True)
        for w in range(WARMUP_REQUESTS):
            warmup_sender = f"warmup_{uuid.uuid4().hex[:8]}"
            data, elapsed, err = send_rasa_message(message, warmup_sender)
            if err:
                print(f"\n    Warm-up {w+1} error: {err}")
            else:
                print(f"{elapsed:.3f}s", end=" ", flush=True)
        print("done.")

        # ── Measured runs ──
        success_times: List[float] = []
        fail_count = 0

        for i in range(MEASURED_ITERATIONS):
            # Use a unique sender for each iteration for isolation
            sender_id = f"latency_{uuid.uuid4().hex[:8]}"
            data, elapsed, err = send_rasa_message(message, sender_id)

            status = "success" if err is None else "failed"
            response_summary = get_response_summary(data) if err is None else err

            raw_results.append({
                "scenario": name,
                "iteration": i + 1,
                "elapsed_seconds": round(elapsed, 4),
                "status": status,
                "response_summary": response_summary,
                "category": category,
            })

            if err is None:
                success_times.append(elapsed)
                marker = "✓" if elapsed < TARGET_LATENCY_S else "✗SLOW"
                print(f"    Run {i+1:2d}: {elapsed:.4f}s [{marker}]")
            else:
                fail_count += 1
                print(f"    Run {i+1:2d}: FAILED ({err})")

        # ── Per-scenario statistics ──
        stats = calculate_statistics(success_times)
        compliance = assess_compliance(stats)

        summary = {
            "scenario": name,
            "description": desc,
            "category": category,
            "message": message,
            "warmup_requests": WARMUP_REQUESTS,
            "measured_iterations": MEASURED_ITERATIONS,
            "successful_runs": len(success_times),
            "failed_runs": fail_count,
            "statistics": stats,
            "compliance_assessment": compliance,
            "target_seconds": TARGET_LATENCY_S,
        }
        summary_results.append(summary)

        if stats["count"] > 0:
            print(f"  ── Results: min={stats['min']:.3f}s  mean={stats['mean']:.3f}s  "
                  f"median={stats['median']:.3f}s  max={stats['max']:.3f}s  p95={stats['p95']:.3f}s")
            print(f"  ── Assessment: {compliance}")
        else:
            print(f"  ── All runs failed.")

    return raw_results, summary_results


def generate_chart(
    local_summaries: List[Dict],
    external_summaries: List[Dict],
    output_path: str,
) -> bool:
    """Generate a bar chart of mean response times with 3s reference line."""
    if not HAS_MATPLOTLIB:
        print("  matplotlib not available – skipping chart generation.")
        return False

    # Combine all scenarios for the chart
    all_summaries = local_summaries + external_summaries
    names = []
    means = []
    colors = []
    categories = []

    for s in all_summaries:
        stats = s["statistics"]
        if stats["mean"] is not None:
            # Short name for chart label
            short_name = s["scenario"].split(". ", 1)[-1] if ". " in s["scenario"] else s["scenario"]
            if len(short_name) > 25:
                short_name = short_name[:22] + "..."
            names.append(short_name)
            means.append(stats["mean"])
            cat = s["category"]
            categories.append(cat)
            if cat == "external-dependent":
                colors.append("#e74c3c")  # Red for external
            elif stats["mean"] < TARGET_LATENCY_S:
                colors.append("#27ae60")  # Green for local pass
            else:
                colors.append("#f39c12")  # Orange for local slow

    if not names:
        print("  No data for chart.")
        return False

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(names)), means, color=colors, edgecolor="black", linewidth=0.5)

    # Add value labels
    for bar, val in zip(bars, means):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}s", va="center", fontsize=9)

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("Mean Response Time (seconds)", fontsize=11)
    ax.set_title("EcoTravel Advisor – Response Latency Measurement", fontsize=13, fontweight="bold")

    # 3-second reference line
    ax.axvline(x=TARGET_LATENCY_S, color="red", linestyle="--", linewidth=1.5, label=f"Target: {TARGET_LATENCY_S}s")
    ax.legend(loc="lower right")

    # Category legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#27ae60", edgecolor="black", label="Local (PASS)"),
        Patch(facecolor="#f39c12", edgecolor="black", label="Local (SLOW)"),
        Patch(facecolor="#e74c3c", edgecolor="black", label="External-dependent"),
    ]
    ax2 = ax.twinx()
    ax2.set_yticks([])
    ax2.legend(handles=legend_elements, loc="lower right", fontsize=8)

    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Chart saved: {output_path}")
    return True


def main():
    print("=" * 60)
    print("  EcoTravel Advisor – Response Latency Measurement")
    print("  Stage 3 Performance Evaluation")
    print("=" * 60)
    print(f"\n  Rasa REST endpoint: {RASA_WEBHOOK_URL}")
    print(f"  Timing method:     time.perf_counter()")
    print(f"  Warm-up requests:  {WARMUP_REQUESTS} (excluded from statistics)")
    print(f"  Measured runs:     {MEASURED_ITERATIONS} per scenario")
    print(f"  Target latency:    < {TARGET_LATENCY_S} seconds")
    print(f"  Request timeout:   {REQUEST_TIMEOUT} seconds")

    # ── Verify Rasa server is reachable ──
    print("\n  Verifying Rasa server connectivity...", end=" ", flush=True)
    test_sender = f"connectivity_test_{uuid.uuid4().hex[:8]}"
    data, elapsed, err = send_rasa_message("hi", test_sender)
    if err:
        print(f"\n\n  ERROR: Cannot reach Rasa server at {RASA_WEBHOOK_URL}")
        print(f"  Detail: {err}")
        print("\n  Please ensure:")
        print("    1. Rasa server is running:  rasa run --enable-api --cors \"*\"")
        print("    2. Action server is running: rasa run actions")
        sys.exit(1)
    print(f"OK ({elapsed:.3f}s)")

    # ── Run local scenarios ──
    local_raw, local_summary = run_scenarios(LOCAL_SCENARIOS, "LOCAL INTERACTIONS")

    # ── Run external-dependent scenarios ──
    ext_raw, ext_summary = run_scenarios(EXTERNAL_SCENARIOS, "EXTERNAL-DEPENDENT INTERACTIONS")

    # ── Ensure results directory exists ──
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # ── Save raw CSV ──
    csv_path = os.path.join(RESULTS_DIR, "latency_results.csv")
    all_raw = local_raw + ext_raw
    fieldnames = ["scenario", "iteration", "elapsed_seconds", "status", "response_summary", "category"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_raw)
    print(f"\n  Raw results saved: {csv_path}")

    # ── Save summary JSON ──
    json_path = os.path.join(RESULTS_DIR, "latency_summary.json")
    summary_data = {
        "test_metadata": {
            "rasa_endpoint": RASA_WEBHOOK_URL,
            "timing_method": "time.perf_counter()",
            "warmup_requests": WARMUP_REQUESTS,
            "measured_iterations": MEASURED_ITERATIONS,
            "target_latency_seconds": TARGET_LATENCY_S,
            "request_timeout_seconds": REQUEST_TIMEOUT,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
        "local_interactions": local_summary,
        "external_dependent_interactions": ext_summary,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    print(f"  Summary saved:     {json_path}")

    # ── Generate chart ──
    chart_path = os.path.join(RESULTS_DIR, "latency_summary.png")
    chart_created = generate_chart(local_summary, ext_summary, chart_path)

    # ── Print final summary table ──
    print(f"\n{'='*80}")
    print("  FINAL RESULTS SUMMARY")
    print(f"{'='*80}")

    header = f"{'Scenario':<40} {'Runs':>5} {'Mean':>8} {'Median':>8} {'Min':>8} {'Max':>8} {'P95':>8} {'<3s?':>12}"
    print(f"\n  LOCAL INTERACTIONS:")
    print(f"  {header}")
    print(f"  {'-'*len(header)}")
    for s in local_summary:
        st = s["statistics"]
        if st["count"] > 0:
            print(f"  {s['scenario']:<40} {st['count']:>5} {st['mean']:>7.3f}s {st['median']:>7.3f}s "
                  f"{st['min']:>7.3f}s {st['max']:>7.3f}s {st['p95']:>7.3f}s {s['compliance_assessment']:>12}")
        else:
            print(f"  {s['scenario']:<40} {'FAIL':>5} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'NO DATA':>12}")

    if ext_summary:
        print(f"\n  EXTERNAL-DEPENDENT INTERACTIONS:")
        print(f"  {header}")
        print(f"  {'-'*len(header)}")
        for s in ext_summary:
            st = s["statistics"]
            if st["count"] > 0:
                print(f"  {s['scenario']:<40} {st['count']:>5} {st['mean']:>7.3f}s {st['median']:>7.3f}s "
                      f"{st['min']:>7.3f}s {st['max']:>7.3f}s {st['p95']:>7.3f}s {s['compliance_assessment']:>12}")
            else:
                print(f"  {s['scenario']:<40} {'FAIL':>5} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'NO DATA':>12}")

    # ── Overall local compliance ──
    local_pass = sum(1 for s in local_summary if "PASS" in s["compliance_assessment"])
    local_total = len(local_summary)
    local_all_pass = all("PASS" in s["compliance_assessment"] for s in local_summary if s["statistics"]["count"] > 0)

    print(f"\n  {'='*60}")
    print(f"  LOCAL COMPLIANCE: {local_pass}/{local_total} scenarios meet <{TARGET_LATENCY_S}s target")
    if local_all_pass:
        print(f"  OVERALL: All local interactions meet the under-{TARGET_LATENCY_S}-second requirement.")
    else:
        slow = [s["scenario"] for s in local_summary
                if s["statistics"]["count"] > 0 and "PASS" not in s["compliance_assessment"]]
        print(f"  ATTENTION: The following scenarios did NOT fully meet the target: {', '.join(slow)}")
    print(f"  {'='*60}")

    print(f"\n  Files created:")
    print(f"    {csv_path}")
    print(f"    {json_path}")
    if chart_created:
        print(f"    {chart_path}")

    print("\n  Stage 3 latency measurement complete.\n")


if __name__ == "__main__":
    main()
