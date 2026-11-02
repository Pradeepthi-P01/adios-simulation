# plots.py -- graphs from results/compare.csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("results/compare.csv")
labels = {"busywait": "Busy-wait", "yield_rr": "Yield (round-robin)",
          "yield_pf": "Yield (PF-aware)"}

# Graph 1: P99.9 latency vs offered load (log scale)
plt.figure(figsize=(7, 4.5))
for name, g in df.groupby("system"):
    plt.plot(g["offered_mrps"], g["p999_us"], marker="o", label=labels.get(name, name))
plt.yscale("log")
plt.xlabel("Offered load (MRPS)")
plt.ylabel("P99.9 latency (µs, log scale)")
plt.title("Tail latency: busy-wait vs yield")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("results/p999_vs_load.png", dpi=150)

# Graph 2: achieved throughput vs offered load
plt.figure(figsize=(7, 4.5))
# for name, g in df.groupby("system"):
#     plt.plot(g["offered_mrps"], g["throughput_mrps"], marker="o", label=labels.get(name, name))
# for name, g in df.groupby("system"):
#     style = "--" if name == "yield_pf" else "-"
#     plt.plot(g["offered_mrps"], g["p999_us"], style, marker="o", label=labels.get(name, name))
for name, g in df.groupby("system"):
    style = "--" if name == "yield_pf" else "-"
    plt.plot(g["offered_mrps"], g["throughput_mrps"], style, marker="o", label=labels.get(name, name))
plt.plot([0, 3], [0, 3], "k--", alpha=0.3, label="Ideal")
plt.xlabel("Offered load (MRPS)")
plt.ylabel("Achieved throughput (MRPS)")
plt.title("Throughput: busy-wait vs yield")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("results/throughput_vs_load.png", dpi=150)

print("saved results/p999_vs_load.png and results/throughput_vs_load.png")