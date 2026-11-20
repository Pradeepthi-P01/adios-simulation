# sweep_adaptive.py -- comprehensive evaluation of Load-Aware Adaptive Hybrid Yielding
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import config
import busywait
import yieldsys

os.makedirs("results", exist_ok=True)

# -------------------------------------------------------------
# Experiment 1: Load Sweep (0.2 to 2.5 MRPS)
# -------------------------------------------------------------
print("Running Experiment 1: Load Sweep for Adaptive Hybrid...")
LOADS = [0.2, 0.5, 0.8, 1.1, 1.4, 1.6, 1.8, 2.0, 2.5]
SYSTEMS = [
    ("busywait", lambda l: busywait.run(l)),
    ("yield_rr", lambda l: yieldsys.run(l, "rr")),
    ("yield_adaptive", lambda l: yieldsys.run(l, "adaptive")),
]

load_rows = []
for l in LOADS:
    for name, fn in SYSTEMS:
        r = fn(l)
        r["system"] = name
        load_rows.append(r)
        print(f"[{name:14s}] load={l:.1f}  tput={r['throughput_mrps']:.2f}  "
              f"P50={r['p50_us']:.2f}  P99={r['p99_us']:.2f}  P99.9={r['p999_us']:.1f}")

df_load = pd.DataFrame(load_rows)
df_load.to_csv("results/adaptive_load_sweep.csv", index=False)
print("Saved results/adaptive_load_sweep.csv")

# -------------------------------------------------------------
# Experiment 2: Context Switch Cost Sensitivity at Low Load (0.5 MRPS)
# -------------------------------------------------------------
print("\nRunning Experiment 2: Context Switch Cost Sweep at 0.5 MRPS...")
SWITCH_COSTS = [0.02, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5]
LOW_LOAD = 0.5

bw_ref = busywait.run(LOW_LOAD)

cost_rows = []
for cs in SWITCH_COSTS:
    config.CONTEXT_SWITCH = cs
    y_rr = yieldsys.run(LOW_LOAD, "rr")
    y_ad = yieldsys.run(LOW_LOAD, "adaptive")
    cost_rows.append({
        "switch_cost_us": cs,
        "busywait_p50": bw_ref["p50_us"],
        "yield_rr_p50": y_rr["p50_us"],
        "adaptive_p50": y_ad["p50_us"],
        "yield_rr_p999": y_rr["p999_us"],
        "adaptive_p999": y_ad["p999_us"],
    })
    print(f"switch={cs:4.2f} us | P50: BW={bw_ref['p50_us']:.2f}  "
          f"RR={y_rr['p50_us']:.2f}  Adaptive={y_ad['p50_us']:.2f}")

config.CONTEXT_SWITCH = 0.02  # restore default

df_cost = pd.DataFrame(cost_rows)
df_cost.to_csv("results/adaptive_cost_sweep.csv", index=False)
print("Saved results/adaptive_cost_sweep.csv")

# -------------------------------------------------------------
# Generate Comprehensive Visualizations
# -------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(13, 10))

labels = {
    "busywait": "Busy-wait (DiLOS)",
    "yield_rr": "Pure Yield (Adios RR)",
    "yield_adaptive": "Adaptive Hybrid (Ours)",
}
colors = {
    "busywait": "tab:red",
    "yield_rr": "tab:blue",
    "yield_adaptive": "tab:green",
}
styles = {
    "busywait": "--",
    "yield_rr": "-",
    "yield_adaptive": "-.",
}

# Subplot 1: Median Latency (P50) vs Load
for name, g in df_load.groupby("system"):
    axes[0, 0].plot(g["offered_mrps"], g["p50_us"], linestyle=styles[name],
                    color=colors[name], marker="o", label=labels[name])
axes[0, 0].set_yscale("log")
axes[0, 0].set_xlabel("Offered Load (MRPS)")
axes[0, 0].set_ylabel("Median Latency P50 (µs, log scale)")
axes[0, 0].set_title("Median Latency: Low-Load Overhead Elimination")
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()

# Subplot 2: Tail Latency (P99.9) vs Load
for name, g in df_load.groupby("system"):
    axes[0, 1].plot(g["offered_mrps"], g["p999_us"], linestyle=styles[name],
                    color=colors[name], marker="o", label=labels[name])
axes[0, 1].set_yscale("log")
axes[0, 1].set_xlabel("Offered Load (MRPS)")
axes[0, 1].set_ylabel("Tail Latency P99.9 (µs, log scale)")
axes[0, 1].set_title("Tail Latency: Resilience to Head-of-Line Blocking")
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].legend()

# Subplot 3: Throughput vs Load
for name, g in df_load.groupby("system"):
    axes[1, 0].plot(g["offered_mrps"], g["throughput_mrps"], linestyle=styles[name],
                    color=colors[name], marker="o", label=labels[name])
axes[1, 0].plot([0, 2.5], [0, 2.5], "k:", alpha=0.4, label="Offered = Achieved")
axes[1, 0].set_xlabel("Offered Load (MRPS)")
axes[1, 0].set_ylabel("Achieved Throughput (MRPS)")
axes[1, 0].set_title("Throughput Scalability")
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].legend()

# Subplot 4: P50 vs Context Switch Cost at 0.5 MRPS
axes[1, 1].plot(df_cost["switch_cost_us"], df_cost["yield_rr_p50"], "o-",
                color="tab:blue", label="Pure Yield (Adios RR)")
axes[1, 1].plot(df_cost["switch_cost_us"], df_cost["adaptive_p50"], "o-.",
                color="tab:green", label="Adaptive Hybrid (Ours)")
axes[1, 1].axhline(bw_ref["p50_us"], color="tab:red", linestyle="--",
                   label="Busy-wait baseline")
axes[1, 1].set_xlabel("Context Switch Cost (µs)")
axes[1, 1].set_ylabel("P50 Latency at 0.5 MRPS (µs)")
axes[1, 1].set_title("Sensitivity to Context-Switch Cost (0.5 MRPS)")
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].legend()

plt.tight_layout()
plt.savefig("results/adaptive_eval.png", dpi=150)
print("Saved results/adaptive_eval.png")
