# cache.py -- local page cache (LRU) and a Zipf page-access generator
import bisect
from collections import OrderedDict
import config


class PageCache:
    def __init__(self, rng):
        self.rng = rng
        n = config.NUM_PAGES
        self.capacity = int(n * config.CACHE_FRACTION)

        # cumulative distribution of page popularity (page 0 is the most popular)
        weights = [1.0 / (i + 1) ** config.ZIPF_S for i in range(n)]
        total = sum(weights)
        acc = 0.0
        self.cdf = []
        for w in weights:
            acc += w / total
            self.cdf.append(acc)

        # start with the most popular pages cached (last item = most recently used)
        self.lru = OrderedDict((p, None) for p in range(self.capacity - 1, -1, -1))
        self.hits = 0
        self.accesses = 0

    def sample_page(self):
        i = bisect.bisect_left(self.cdf, self.rng.random())
        return min(i, len(self.cdf) - 1)

    def access(self, page):
        """Return True on a hit and mark the page as recently used."""
        self.accesses += 1
        if page in self.lru:
            self.lru.move_to_end(page)
            self.hits += 1
            return True
        return False

    def insert(self, page):
        """Called when a fetched page arrives; evicts the LRU page if full."""
        if page in self.lru:
            self.lru.move_to_end(page)
            return
        if len(self.lru) >= self.capacity:
            self.lru.popitem(last=False)
        self.lru[page] = None