import dataclasses as dto
from hashlib import sha256


@dto.dataclass
class PrivRSA:
    N: int
    priv: int
    pub: int
    phi: int

    def hash(self, value):
        hash_result = sha256(str(value).encode())
        return (int(hash_result.hexdigest(), 16)) % self.N


@dto.dataclass
class PubRSA:
    N: int
    pub: int
    phi: int

    def hash(self, value):
        hash_result = sha256(str(value).encode())
        return (int(hash_result.hexdigest(), 16)) % self.N
