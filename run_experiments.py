# run_experiments.py -- busy-wait vs yield, same loads
import os
import pandas as pd
import busywait
import yieldsys

LOADS = [0.5, 1.0, 1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0]
SYSTEMS = {
    "busywait": lambda load: busywait.run(load),
    "yield_rr": lambda load: yieldsys.run(load, "rr"),
    "yield_pf": lambda load: yieldsys.run(load, "pf"),
}

rows = []
for load in LOADS:
    for name, fn in SYSTEMS.items():
        r = fn(load)
        r["system"] = name
        rows.append(r)
        print(f"{name:9s} load={load:.1f}  tput={r['throughput_mrps']:.2f}  "
              f"P50={r['p50_us']:.1f}  P99={r['p99_us']:.1f}  P99.9={r['p999_us']:.1f}")

os.makedirs("results", exist_ok=True)
pd.DataFrame(rows).to_csv("results/compare.csv", index=False)
print("saved results/compare.csv")