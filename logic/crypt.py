from sage.all import ZZ
from sage.arith.misc import is_prime, gcd, xgcd
from sage.rings.finite_rings.integer_mod import mod

from data import PrivRSA, PubRSA


def get_pub_priv_keys(p, q):
    assert is_prime(p) and is_prime(q)
    n = p * q
    phi = (p - 1) * (q - 1)
    e = get_e(phi)
    assert gcd(e, phi) == 1
    d = get_d(e, phi)
    assert mod(d * e, phi) == 1
    privRSA = PrivRSA(n, d, e, phi)
    pubRSA = PubRSA(n, e, phi)
    assert privRSA.hash(3) == pubRSA.hash(3)
    return privRSA, pubRSA


def get_d(e, phi):
    _, d, _ = xgcd(e, phi)
    if d < 0:
        d += phi
    return d


def get_e(phi):
    e = ZZ.random_element(phi)
    while gcd(e, phi) != 1:
        e = ZZ.random_element(phi)
    return e
