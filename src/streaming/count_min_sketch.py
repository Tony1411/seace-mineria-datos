import hashlib
from array import array


class CountMinSketch:
    def __init__(self, width, depth):
        if width <= 0:
            raise ValueError("width debe ser positivo")
        if depth <= 0:
            raise ValueError("depth debe ser positivo")

        self.width = int(width)
        self.depth = int(depth)

        self.table = [
            array("I", [0]) * self.width
            for _ in range(self.depth)
        ]

    def _indices(self, item):
        data = str(item).encode("utf-8")

        digest = hashlib.blake2b(
            data,
            digest_size=16
        ).digest()

        h1 = int.from_bytes(digest[:8], "big")
        h2 = int.from_bytes(digest[8:], "big")

        if h2 == 0:
            h2 = 1

        for i in range(self.depth):
            yield (h1 + i * h2) % self.width

    def update(self, item, count=1):
        for fila, columna in enumerate(self._indices(item)):
            self.table[fila][columna] += count

    def query(self, item):
        return min(
            self.table[fila][columna]
            for fila, columna in enumerate(self._indices(item))
        )

    @property
    def memory_bytes(self):
        return self.width * self.depth * 4
