# pf_vs_rr.py -- round-robin vs PF-aware dispatching, averaged over seeds
import numpy as np
import pandas as pd
import config
import yieldsys

LOADS = [1.8, 2.0, 2.2, 2.3, 2.4]
SEEDS = [1, 2, 3, 4, 5]


def experiment(qp_service, label):
    # keep an unloaded fetch at 3.0 us: QP + link + network latency
    config.QP_SERVICE = qp_service
    config.NET_LATENCY = config.RDMA_FETCH_TIME - qp_service - config.LINK_TIME
    rows = []
    for load in LOADS:
        row = {"setting": label, "offered_mrps": load}
        for policy in ["rr", "pf"]:
            runs = [yieldsys.run(load, policy, seed=s) for s in SEEDS]
            row[policy + "_p999"] = np.mean([r["p999_us"] for r in runs])
        row["p999_gain_pct"] = 100 * (row["rr_p999"] - row["pf_p999"]) / row["rr_p999"]
        rows.append(row)
        print(f"{label:14s} load={load}  RR={row['rr_p999']:.2f}  "
              f"PF={row['pf_p999']:.2f}  gain={row['p999_gain_pct']:.1f}%")
    return rows


rows = experiment(1.0, "QP 1.0 us") + experiment(2.0, "QP 2.0 us")
pd.DataFrame(rows).to_csv("results/pf_vs_rr.csv", index=False)
print("saved results/pf_vs_rr.csv")