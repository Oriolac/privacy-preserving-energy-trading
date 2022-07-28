import unittest as utest

from data.actors import Concentrator, SmartMeter
from logic.acquisition import create_coins
from logic.crypt import get_pub_priv_keys


class GenerateOneOffer(utest.TestCase):

    def setUp(self) -> None:
        self.P = 17
        self.Q = 19
        self.privRSA, self.pubRSA = get_pub_priv_keys(self.P, self.Q)
        self.sm = SmartMeter(1, self.pubRSA)
        self.agg = Concentrator(self.privRSA)
        create_coins(self.sm, self.agg, 10)
