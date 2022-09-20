import dataclasses as dto
from random import randint
from typing import List, Any, Tuple, Dict

from sage.all import ZZ
from sage.arith.misc import xgcd, gcd

from data import (
    PubRSA,
    Coin,
    Producer,
    Offer,
    Request,
    Pairing,
    Receipt,
    Payment,
    PrivRSA,
    InvalidationRequest,
    InvalidationOffer,
)


@dto.dataclass
class SmartMeter:
    id: int
    rsa: PubRSA
    coins: List[Coin] = dto.field(default_factory=list)
    prod: Dict[int, Producer] = dto.field(default_factory=dict)
    current_offers: Dict[int, Offer] = dto.field(default_factory=dict)
    current_requests: Dict[int, Request] = dto.field(default_factory=dict)
    randint: Any = None

    def get_pub_msg(self, message):
        self.randint = (randint(3, 50)) % self.rsa.N
        return self.rsa.hash(message) * (self.randint ** self.rsa.pub) % self.rsa.N

    def get_sign(self, pseudo_sign):
        _, inv_int, _ = xgcd(self.randint, self.rsa.N)
        if inv_int < 0:
            inv_int += self.rsa.N
        return (pseudo_sign * inv_int) % self.rsa.N

    def add_coin(self, payload: int, signature: int):
        """
        Adds the payload and the signature from the aggregator to the smart meter.
        :param payload: int
        :param signature: int
        :return:
        """
        self.coins.append(Coin(payload, signature))
        return self.coins

    def generate_offer(self, i):
        private = ZZ.random_element(self.rsa.phi)
        while gcd(private, self.rsa.phi) != 1:
            private = ZZ.random_element(self.rsa.phi)
        _, public, _ = xgcd(private, self.rsa.phi)
        if public < 0:
            public += self.rsa.phi
        assert (public * private) % self.rsa.phi == 1
        # Must save producer as a dict of (i, prod)
        self.prod[i] = Producer(self.rsa.N, private, public)
        offer = Offer(i, self.rsa.N, public, self.id)
        self.current_offers[offer.id] = offer
        return offer

    def generate_request(self, j):
        req = Request(j, self.id)
        self.current_requests[req.id] = req
        return req

    def do_payment(self, pairing: Pairing):
        """
        Action of consumer
        :param pairing:
        :return:
        """
        # Receipt has got relaxed
        receipt = Receipt(self.rsa.hash(randint(0, 321)))
        coin = self.coins.pop(0)
        cipher = pairing.offer.encrypt_tuple(coin, receipt)
        payment = Payment(pairing.offer.id, pairing.request.id, cipher, receipt.value)
        self.current_requests.pop(pairing.request.id)
        return payment

    def decrypt_payment(self, payment: Payment) -> Tuple[Coin, Receipt]:
        res = self.prod.pop(payment.i).decrypt_tuple(*payment.cipher)
        self.current_offers.pop(payment.i)
        return res

    def create_invalidation_request(self) -> InvalidationRequest:
        key: int = set(self.current_requests.keys()).pop()
        invalid_request: Request = self.current_requests[key]
        return InvalidationRequest(invalid_request.id)

    def check_invalidation_request(self, invalidation: InvalidationRequest, ack: bool):
        if not ack:
            raise KeyError("Request not found in concentrator!")
        self.current_requests.pop(invalidation.request_id)

    def create_invalidation_offer(self) -> InvalidationOffer:
        key: int = set(self.current_offers.keys()).pop()
        invalid_offer: Offer = self.current_offers[key]
        return InvalidationOffer(invalid_offer.id)

    def check_invalidation_offer(self, invalidation: InvalidationOffer, ack: bool):
        if not ack:
            raise KeyError("Offer not found in concentrator!")
        self.current_offers.pop(invalidation.offer_id)


@dto.dataclass
class Concentrator:
    rsa: PrivRSA
    offers: dict[int, Offer] = dto.field(default_factory=dict)
    requests: dict[int, Request] = dto.field(default_factory=dict)
    last_offer_id = 0
    last_request_id = 0

    def pseudo_sign(self, m):
        return (m ** self.rsa.priv) % self.rsa.N

    def get_last_offer(self) -> int:
        return self.last_offer_id

    def get_last_request(self) -> int:
        return self.last_request_id

    def add_offer(self, offer: Offer):
        # Check offer.id is not in offers
        self.offers[offer.id] = offer
        self.last_offer_id += 1

    def add_request(self, request: Request):
        # Check request.id is not in requests
        self.requests[request.id] = request
        self.last_request_id += 1
    
    def generate_pairing(self):
        if len(self.offers) == 0 and len(self.requests) == 0:
            return None
        offer_id = set(self.offers).pop()
        request_id = set(self.requests).pop()
        return Pairing(self.offers[offer_id], self.requests[request_id])

    def checks_receipt(self, payment_receipt, offer_receipt):
        res = payment_receipt == offer_receipt
        assert res
        return res

    def receive_invalidation_request(self, invalidation: InvalidationRequest) -> bool:
        if invalidation.request_id not in self.requests.keys():
            return False
        self.requests.pop(invalidation.request_id)
        return True

    def receive_invalidation_offer(self, invalidation: InvalidationOffer) -> bool:
        if invalidation.offer_id not in self.offers.keys():
            return False
        self.offers.pop(invalidation.offer_id)
        return True
