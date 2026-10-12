class DGIM:
    def __init__(self, window_size):
        if window_size <= 0:
            raise ValueError("window_size debe ser positivo")

        self.window_size = int(window_size)
        self.timestamp = 0
        self.buckets = []

    def update(self, bit):
        self.timestamp += 1

        if bit not in (0, 1):
            raise ValueError("bit debe ser 0 o 1")

        if bit == 1:
            self.buckets.insert(0, (1, self.timestamp))
            self._compress()

        self._expire()

    def _compress(self):
        size = 1

        while True:
            indices = [
                i
                for i, (bucket_size, _) in enumerate(self.buckets)
                if bucket_size == size
            ]

            if len(indices) <= 2:
                if not any(
                    bucket_size > size
                    for bucket_size, _ in self.buckets
                ):
                    break

                size *= 2
                continue

            idx_newer = indices[-2]
            idx_older = indices[-1]

            _, end_timestamp = self.buckets[idx_newer]

            self.buckets[idx_newer] = (
                size * 2,
                end_timestamp
            )

            del self.buckets[idx_older]

            size *= 2

    def _expire(self):
        cutoff = self.timestamp - self.window_size

        self.buckets = [
            bucket
            for bucket in self.buckets
            if bucket[1] > cutoff
        ]

    def query(self, k=None):
        if k is None:
            k = self.window_size

        if k <= 0 or k > self.window_size:
            raise ValueError(
                "k debe estar entre 1 y window_size"
            )

        cutoff = self.timestamp - k

        incluidos = [
            (size, end)
            for size, end in self.buckets
            if end > cutoff
        ]

        if not incluidos:
            return 0

        total = sum(size for size, _ in incluidos)

        oldest_size = incluidos[-1][0]

        return (
            total
            - oldest_size
            + oldest_size / 2
        )

    @property
    def n_buckets(self):
        return len(self.buckets)
