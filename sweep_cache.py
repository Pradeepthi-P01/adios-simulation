# sweep_cache.py -- LRU page cache + Zipf access pattern instead of a fixed hit probability
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import config
import busywait
import yieldsys

config.USE_CACHE = True
OFFERED = 5.0       # high enough to saturate at low hit rates (results are capped at this value)
rows = []


def measure(part, zipf_s, cache_frac):
    config.ZIPF_S = zipf_s
    config.CACHE_FRACTION = cache_frac
    b = busywait.run(OFFERED)
    y = yieldsys.run(OFFERED, "rr")
    row = {"part": part, "zipf_s": zipf_s, "cache_frac": cache_frac,
           "hit_rate": (b["hit_rate"] + y["hit_rate"]) / 2,
           "busywait_mrps": b["throughput_mrps"], "yield_mrps": y["throughput_mrps"]}
    rows.append(row)
    print(f"{part}  skew={zipf_s:<4}  cache={cache_frac:.0%}  hit rate={row['hit_rate']:.1%}  "
          f"busy-wait={row['busywait_mrps']:.2f}  yield={row['yield_mrps']:.2f} MRPS")


print("Part B: access skew sweep, 20% cache (skew 0 = uniform = the original fixed-20% model)")
for s in [0.0, 0.5, 0.8, 0.99, 1.2]:
    measure("B", s, 0.20)

print("Part C: cache size sweep, skew 0.8")
for frac in [0.05, 0.10, 0.20, 0.40, 0.60]:
    measure("C", 0.8, frac)

df = pd.DataFrame(rows)
df.to_csv("results/cache_sweep.csv", index=False)

c = df[df["part"] == "C"]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

axes[0].plot(c["cache_frac"] * 100, c["hit_rate"] * 100, marker="o", label="LRU, Zipf skew 0.8")
axes[0].plot(c["cache_frac"] * 100, c["cache_frac"] * 100, "k--", alpha=0.4,
             label="Uniform access (hit rate = cache size)")
axes[0].set_xlabel("Local cache size (% of all pages)")
axes[0].set_ylabel("Measured hit rate (%)")
axes[0].set_title("Hit rate vs cache size")
axes[0].grid(True, alpha=0.3)
axes[0].legend()

axes[1].plot(c["cache_frac"] * 100, c["busywait_mrps"], marker="o", label="Busy-wait")
axes[1].plot(c["cache_frac"] * 100, c["yield_mrps"], marker="o", label="Yield")
axes[1].axhline(OFFERED, color="gray", linestyle=":", label="Offered load (cap)")
axes[1].set_xlabel("Local cache size (% of all pages)")
axes[1].set_ylabel("Peak throughput (MRPS)")
axes[1].set_title("Throughput vs cache size")
axes[1].grid(True, alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.savefig("results/cache_sweep.png", dpi=150)
print("saved results/cache_sweep.csv and results/cache_sweep.png")