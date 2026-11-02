# busywait.py -- baseline: the worker busy-waits during a page fetch
import os
import random
import numpy as np
import pandas as pd
import simpy
import config
from rdma import Rdma
from cache import PageCache


def arrivals(env, queue, load_mrps, rng, cache):
    """Open-loop Poisson arrivals. 1 MRPS = 1 request per µs."""
    while True:
        yield env.timeout(rng.expovariate(load_mrps))
        req = {"arrival": env.now}
        if cache is not None:
            req["page"] = cache.sample_page()
        else:
            req["fault"] = rng.random() >= config.LOCAL_HIT_PROB
        queue.put(req)


def worker(env, queue, results, wid, rdma, cache):
    pre = config.REMOTE_CPU_TIME * config.FAULT_SPLIT
    post = config.REMOTE_CPU_TIME - pre
    while True:
        req = yield queue.get()
        if cache is not None:
            req["fault"] = not cache.access(req["page"])
        if req["fault"]:
            yield env.timeout(pre)
            yield env.process(rdma.fetch(wid))      # BUSY-WAIT: worker is blocked here
            if cache is not None:
                cache.insert(req["page"])
            yield env.timeout(post)
        else:
            yield env.timeout(config.LOCAL_TIME)
        results.append((req["arrival"], env.now))


def run(load_mrps, seed=config.SEED):
    rng = random.Random(seed)
    env = simpy.Environment()
    queue = simpy.Store(env)
    rdma = Rdma(env)
    cache = PageCache(rng) if config.USE_CACHE else None
    results = []

    env.process(arrivals(env, queue, load_mrps, rng, cache))
    for wid in range(config.NUM_WORKERS):
        env.process(worker(env, queue, results, wid, rdma, cache))
    env.run(until=config.SIM_DURATION)

    done = [(a, f) for (a, f) in results if a >= config.WARMUP]
    lat = np.array([f - a for (a, f) in done])
    window = config.SIM_DURATION - config.WARMUP
    finished = sum(1 for (a, f) in results if f >= config.WARMUP)
    return {
        "offered_mrps": load_mrps,
        "throughput_mrps": finished / window,
        "p50_us": np.percentile(lat, 50),
        "p99_us": np.percentile(lat, 99),
        "p999_us": np.percentile(lat, 99.9),
        "hit_rate": cache.hits / cache.accesses if cache else config.LOCAL_HIT_PROB,
    }


if __name__ == "__main__":
    loads = [0.2, 0.5, 0.8, 1.1, 1.4, 1.6, 1.8, 2.0]
    rows = []
    for load in loads:
        r = run(load)
        rows.append(r)
        print(f"load={r['offered_mrps']:.1f}  tput={r['throughput_mrps']:.2f}  "
              f"P50={r['p50_us']:.1f}  P99={r['p99_us']:.1f}  P99.9={r['p999_us']:.1f}")

    os.makedirs("results", exist_ok=True)
    pd.DataFrame(rows).to_csv("results/busywait.csv", index=False)
    print("saved results/busywait.csv")