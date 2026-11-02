# rdma.py -- a simple RDMA model: one queue pair per worker, one shared link
import simpy
import config


class Rdma:
    def __init__(self, env):
        self.env = env
        self.qps = [simpy.Resource(env, capacity=1) for _ in range(config.NUM_WORKERS)]
        self.link = simpy.Resource(env, capacity=1)
        self.outstanding = [0] * config.NUM_WORKERS

    def fetch(self, qp):
        """SimPy process: fetch one 4KB page through worker `qp`'s queue pair."""
        self.outstanding[qp] += 1
        with self.qps[qp].request() as r:
            yield r
            yield self.env.timeout(config.QP_SERVICE)
        with self.link.request() as r:
            yield r
            yield self.env.timeout(config.LINK_TIME)
        yield self.env.timeout(config.NET_LATENCY)
        self.outstanding[qp] -= 1