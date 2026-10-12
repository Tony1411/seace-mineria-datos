import hashlib


class BloomFilter:
    def __init__(self, m_bits, k_hashes):
        if m_bits <= 0:
            raise ValueError("m_bits debe ser positivo")
        if k_hashes <= 0:
            raise ValueError("k_hashes debe ser positivo")

        self.m = int(m_bits)
        self.k = int(k_hashes)
        self.bits = bytearray((self.m + 7) // 8)

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

        for i in range(self.k):
            yield (h1 + i * h2) % self.m

    def add(self, item):
        for idx in self._indices(item):
            byte_idx = idx // 8
            bit_idx = idx % 8
            self.bits[byte_idx] |= 1 << bit_idx

    def contains(self, item):
        for idx in self._indices(item):
            byte_idx = idx // 8
            bit_idx = idx % 8

            if not (self.bits[byte_idx] & (1 << bit_idx)):
                return False

        return True

    @property
    def memory_bytes(self):
        return len(self.bits)
