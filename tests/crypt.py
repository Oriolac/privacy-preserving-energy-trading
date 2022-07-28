import unittest as utest
from sage.all import ZZ
from sage.arith.misc import is_prime, gcd, xgcd
from sage.rings.finite_rings.integer_mod import mod

from data import PrivRSA, PubRSA



class TestRSA(utest.TestCase):

    def setUp(self) -> None:
        self.ps = [17]
        self.qs = [19]

    def test_ok(self):
        for p in self.ps:
            for q in self.qs:
                self.assert_rsa_validation(p, q)

    def assert_rsa_validation(self, p, q):
        n = p * q
        phi = (p - 1) * (q - 1)
        e = ZZ.random_element(phi)
        while gcd(e, phi) != 1:
            e = ZZ.random_element(phi)
        self.assertEqual(gcd(e, phi), 1)
        _, d, _ = xgcd(e, phi)
        if d < 0:
            d += phi
        self.assertEqual(1, mod(d * e, phi))
        privRSA = PrivRSA(n, d, e, phi)
        pubRSA = PubRSA(n, e, phi)
        self.assertEqual(privRSA.hash(3), pubRSA.hash(3))

