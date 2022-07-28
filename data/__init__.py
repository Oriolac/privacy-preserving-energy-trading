import dataclasses as dto
from typing import Any, Tuple

from .crypt import PrivRSA, PubRSA


@dto.dataclass
class InvalidationRequest:
    request_id: int


@dto.dataclass
class InvalidationOffer:
    offer_id: int


@dto.dataclass
class Offer:
    id: int
    N: int
    public_key: Any

    def encrypt_coin(self, coin) -> Tuple[int, int]:
        return (
            coin.value**self.public_key % self.N,
            coin.sign**self.public_key % self.N,
        )

    def encrypt_tuple(self, coin, receipt) -> Tuple[Tuple[int, int], int]:
        cipher = self.encrypt_coin(coin)
        return cipher, receipt.value**self.public_key % self.N


@dto.dataclass
class Request:
    id: int


@dto.dataclass
class Pairing:
    offer: Offer
    request: Request


@dto.dataclass
class Producer:
    N: int
    private_key: int
    public_key: int

    def encrypt_coin(self, coin):
        return (
            coin.value**self.public_key % self.N,
            coin.sign**self.public_key % self.N,
        )

    def decrypt_coin(self, a, b):
        return Coin(a**self.private_key % self.N, b**self.private_key % self.N)

    def encrypt_tuple(self, coin, receipt):
        cipher = self.encrypt_coin(coin)
        return cipher, receipt.value**self.public_key % self.N

    def decrypt_tuple(self, a, b):
        coin = self.decrypt_coin(*a)
        return coin, Receipt(b**self.private_key % self.N)


@dto.dataclass
class Coin:
    value: int  # it is a string but it has been relaxed
    sign: int


@dto.dataclass
class Receipt:
    value: int


@dto.dataclass
class Payment:
    i: int
    j: int
    cipher: Tuple[Tuple[int, int], int]
    hashed_receipt: int
