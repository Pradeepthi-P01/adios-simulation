# yieldsys.py -- yield-based page fault handling (Adios-like)
import itertools
import random
from collections import deque

import numpy as np
import simpy

import config
from rdma import Rdma
from cache import PageCache


class Worker:
    def __init__(self, env, wid):
        self.id = wid
        self.inbox = simpy.PriorityStore(env)   # priority 0 = resume, 1 = new request
        self.idle = False


class YieldSystem:
    def __init__(self, env, policy, cache=None):
        self.env = env
        self.policy = policy                    # "rr" or "pf"
        self.cache = cache
        self.rdma = Rdma(env)
        self.workers = [Worker(env, i) for i in range(config.NUM_WORKERS)]
        self.pending = deque()                  # the central queue
        self.wake = env.event()
        self.seq = itertools.count()
        self.rr_next = 0
        self.inflight = 0
        self.results = []
        env.process(self.dispatcher())
        for w in self.workers:
            env.process(self.worker(w))

    def notify(self):
        if not self.wake.triggered:
            self.wake.succeed()

    def submit(self, req):
        self.pending.append(req)
        self.notify()

    def finish(self, req):
        self.results.append((req["arrival"], self.env.now))
        self.inflight -= 1
        self.notify()

    def choose(self, idle):
        n = config.NUM_WORKERS
        order = lambda w: (w.id - self.rr_next) % n
        if self.policy == "pf":      # fewest outstanding page fetches first
            w = min(idle, key=lambda w: (self.rdma.outstanding[w.id], order(w)))
        else:                        # round-robin
            w = min(idle, key=order)
        self.rr_next = (w.id + 1) % n
        return w

    def dispatcher(self):
        while True:
            yield self.wake
            self.wake = self.env.event()
            while self.pending:
                idle = [w for w in self.workers if w.idle]
                if not idle or self.inflight >= config.MAX_INFLIGHT:
                    break
                w = self.choose(idle)
                w.idle = False
                self.inflight += 1
                w.inbox.put((1, next(self.seq), ("new", self.pending.popleft())))

    def fetch_and_resume(self, w, req):
        yield self.env.process(self.rdma.fetch(w.id))
        if self.cache is not None:
            self.cache.insert(req["page"])
        w.idle = False
        w.inbox.put((0, next(self.seq), ("resume", req)))

    def worker(self, w):
        pre = config.REMOTE_CPU_TIME * config.FAULT_SPLIT
        post = config.REMOTE_CPU_TIME - pre
        while True:
            w.idle = len(w.inbox.items) == 0
            if w.idle:
                self.notify()
            _, _, (kind, req) = yield w.inbox.get()
            if kind == "new":
                if self.cache is not None:
                    req["fault"] = not self.cache.access(req["page"])
                if req["fault"]:
                    yield self.env.timeout(pre)
                    self.env.process(self.fetch_and_resume(w, req))   # issue fetch...
                    yield self.env.timeout(config.CONTEXT_SWITCH)     # ...and yield
                else:
                    yield self.env.timeout(config.LOCAL_TIME)
                    self.finish(req)
            else:   # page arrived: switch back, finish the request
                yield self.env.timeout(config.CONTEXT_SWITCH + post)
                self.finish(req)


def arrivals(env, system, load_mrps, rng, cache):
    while True:
        yield env.timeout(rng.expovariate(load_mrps))
        req = {"arrival": env.now}
        if cache is not None:
            req["page"] = cache.sample_page()
        else:
            req["fault"] = rng.random() >= config.LOCAL_HIT_PROB
        system.submit(req)


def run(load_mrps, policy="rr", seed=config.SEED):
    rng = random.Random(seed)
    env = simpy.Environment()
    cache = PageCache(rng) if config.USE_CACHE else None
    system = YieldSystem(env, policy, cache)
    env.process(arrivals(env, system, load_mrps, rng, cache))
    env.run(until=config.SIM_DURATION)

    done = [(a, f) for (a, f) in system.results if a >= config.WARMUP]
    lat = np.array([f - a for (a, f) in done])
    window = config.SIM_DURATION - config.WARMUP
    finished = sum(1 for (a, f) in system.results if f >= config.WARMUP)
    return {
        "offered_mrps": load_mrps,
        "throughput_mrps": finished / window,
        "p50_us": np.percentile(lat, 50),
        "p99_us": np.percentile(lat, 99),
        "p999_us": np.percentile(lat, 99.9),
        "hit_rate": cache.hits / cache.accesses if cache else config.LOCAL_HIT_PROB,
    }