# sweep_switchcost.py -- how expensive can a context switch be before yield stops paying off?
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import config
import busywait
import yieldsys

COSTS = [0.02, 0.1, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]   # context switch cost in µs
OVERLOAD = 3.0      # offered load that saturates both systems (peak throughput)
MODERATE = 1.5      # load where both systems are stable (tail latency)

bw_peak = busywait.run(OVERLOAD)["throughput_mrps"]
bw_tail = busywait.run(MODERATE)["p999_us"]
print(f"busy-wait reference: peak={bw_peak:.2f} MRPS, P99.9 at {MODERATE} MRPS={bw_tail:.1f} us")

rows = []
for cs in COSTS:
    config.CONTEXT_SWITCH = cs
    peak = yieldsys.run(OVERLOAD, "rr")["throughput_mrps"]
    tail = yieldsys.run(MODERATE, "rr")["p999_us"]
    rows.append({"switch_us": cs, "yield_peak_mrps": peak, "yield_p999_us": tail})
    print(f"switch={cs:5.2f} us  yield peak={peak:.2f} MRPS  P99.9@{MODERATE}={tail:.1f} us")
config.CONTEXT_SWITCH = 0.02    # restore the default

df = pd.DataFrame(rows)
df.to_csv("results/switchcost_sweep.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

axes[0].plot(df["switch_us"], df["yield_peak_mrps"], marker="o", label="Yield")
axes[0].axhline(bw_peak, color="tab:blue", linestyle="--", label="Busy-wait")
axes[0].set_xscale("log")
axes[0].set_xlabel("Context switch cost (µs, log scale)")
axes[0].set_ylabel("Peak throughput (MRPS)")
axes[0].set_title("Peak throughput")
axes[0].grid(True, alpha=0.3)
axes[0].legend()

axes[1].plot(df["switch_us"], df["yield_p999_us"], marker="o", label="Yield")
axes[1].axhline(bw_tail, color="tab:blue", linestyle="--", label="Busy-wait")
axes[1].set_xscale("log")
axes[1].set_yscale("log")
axes[1].set_xlabel("Context switch cost (µs, log scale)")
axes[1].set_ylabel(f"P99.9 latency at {MODERATE} MRPS (µs, log scale)")
axes[1].set_title("Tail latency")
axes[1].grid(True, alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.savefig("results/switchcost_sweep.png", dpi=150)
print("saved results/switchcost_sweep.csv and results/switchcost_sweep.png")