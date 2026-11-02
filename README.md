# Adios Simulation: Busy-wait vs Yield-based Page Fault Handling

A discrete-event simulation (Python + SimPy) of the core mechanism from the paper on **Adios**: when a request hits a page fault on remote (disaggregated) memory, should the worker **busy-wait** for the RDMA fetch, or **yield** to another request while the page is in flight?

> **Scope:** This is a simulation-based study of the paper's core mechanism. It is **not** an implementation of Adios. The unithreads, unikernel, real RDMA hardware, polling delegation and reclaimer thread are not built.

## What is modelled

- **Busy-wait system** (`busywait.py`): 8 workers share one central queue. On a page fault, the worker blocks until the RDMA fetch finishes.
- **Yield system** (`yieldsys.py`): a dispatcher assigns requests to idle workers. On a fault, the worker issues the fetch, pays a context switch, and serves other work. A bounded pool of in-flight requests (`MAX_INFLIGHT`) models the paper's fixed unithread pool.
  - Round-robin dispatching (`rr`)
  - Page-fault-aware dispatching (`pf`): prefers the worker with the fewest outstanding fetches
- **RDMA model** (`rdma.py`): one queue pair per worker plus one shared link. Both systems use the same model, so the comparison is fair.
- **Page cache** (`cache.py`): optional LRU cache with a Zipf access pattern, so the hit rate comes from cache size and access skew instead of a fixed probability.

All times are in microseconds. Offered load is in MRPS (million requests per second).

## Files

| File | Purpose |
|---|---|
| `config.py` | All parameters (workers, times, hit rate, cache settings, in-flight pool) |
| `rdma.py` | RDMA queue-pair and link model |
| `cache.py` | LRU page cache and Zipf page generator |
| `busywait.py` | Busy-wait baseline |
| `yieldsys.py` | Yield-based system (round-robin and PF-aware) |
| `run_experiments.py` | Busy-wait vs yield across offered loads |
| `plots.py` | Tail-latency and throughput graphs |
| `pf_vs_rr.py` | PF-aware vs round-robin comparison |
| `sweep_hitrate.py` | Peak throughput vs local-memory hit rate |
| `sweep_switchcost.py` | Context-switch cost sweep |
| `sweep_cache.py` | LRU cache + Zipf skew and cache-size sweeps |
| `results/` | CSV files and PNG graphs |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install simpy numpy pandas matplotlib
```

## How to run

Run in this order from the project folder:

```bash
python busywait.py          # quick sanity check
python run_experiments.py   # writes results/compare.csv
python plots.py             # writes results/p999_vs_load.png, throughput_vs_load.png
python pf_vs_rr.py          # writes results/pf_vs_rr.csv
python sweep_hitrate.py     # writes results/hitrate_sweep.csv/png
python sweep_switchcost.py  # writes results/switchcost_sweep.csv/png
python sweep_cache.py       # writes results/cache_sweep.csv/png
```

The sweeps run many simulations and can take several minutes each.

## Main results

| Result | Value |
|---|---|
| Peak throughput, busy-wait | 1.77 MRPS |
| Peak throughput, yield | 2.50 MRPS (about 1.4x busy-wait; the paper reports about 1.5 to 1.6x) |
| P99.9 latency at 1.5 MRPS | yield 8.9 µs vs busy-wait 17.2 µs (about 1.9x lower) |
| P99.9 latency at 1.8 MRPS | yield 10.6 µs vs busy-wait 3,014 µs (busy-wait is past saturation) |
| PF-aware vs round-robin | at most about 1.2% better P99.9, fading near saturation (not tested for statistical significance) |
| Context-switch cost | yield beats busy-wait only while a switch costs under about 1.5 µs |
| LRU cache validation | uniform access with a 20% cache gives a 19.9% hit rate, matching the fixed 20% model |

Throughput values equal to the offered load (for example 4.00 or 5.01 in the sweeps) mean the system kept up, so read them as "at least", not as capacity.

## Notes and limitations

- Peak throughput is counted by **completion time** and the yield system uses a **bounded in-flight pool**. Without these two fixes, the measured throughput depended on the offered load.
- The absolute ceilings differ from the paper's; the comparison is of trends, not exact values.
- Concurrent misses on the same page each issue a fetch (no merging), which slightly overstates network traffic for hot pages.
- The PF-aware gain is much smaller than the paper's because the fixed-time model has less bursty RDMA queues than real hardware.
- Each result comes from one run with a fixed seed (`SEED = 42`), with no confidence intervals.

## Reference

The paper on Adios (yield-based page fault handling for memory disaggregation) that this project's core mechanism is based on.
