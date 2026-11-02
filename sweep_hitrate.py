# sweep_hitrate.py -- peak throughput as the local-memory hit rate changes
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import config
import busywait
import yieldsys

HIT_RATES = [0.1, 0.2, 0.4, 0.6, 0.8]
OFFERED = 4.0   # high enough to saturate at low hit rates

rows = []
for h in HIT_RATES:
    config.LOCAL_HIT_PROB = h
    for name, fn in [("busywait", lambda: busywait.run(OFFERED)),
                     ("yield", lambda: yieldsys.run(OFFERED, "rr"))]:
        r = fn()
        rows.append({"hit_rate": h, "system": name,
                     "throughput_mrps": r["throughput_mrps"]})
        print(f"hit={h:.1f}  {name:8s}  tput={r['throughput_mrps']:.2f}")

df = pd.DataFrame(rows)
df.to_csv("results/hitrate_sweep.csv", index=False)

plt.figure(figsize=(7, 4.5))
for name, g in df.groupby("system"):
    plt.plot(g["hit_rate"] * 100, g["throughput_mrps"], marker="o",
             label="Busy-wait" if name == "busywait" else "Yield")
plt.xlabel("Local memory hit rate (%)")
plt.ylabel("Peak throughput (MRPS)")
plt.title("Throughput vs local memory hit rate")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("results/hitrate_sweep.png", dpi=150)
print("saved results/hitrate_sweep.csv and results/hitrate_sweep.png")