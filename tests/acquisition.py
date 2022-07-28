import unittest as utest

from logic.acquisition import create_coin, create_coins
from logic.crypt import get_pub_priv_keys
from data.actors import SmartMeter, Concentrator


class TestOneSmartMeter(utest.TestCase):
    def setUp(self):
        self.P = 17
        self.Q = 19
        self.privRSA, self.pubRSA = get_pub_priv_keys(self.P, self.Q)
        self.sm = SmartMeter(1, self.pubRSA)
        self.agg = Concentrator(self.privRSA)

    def test_create_coin(self):
        create_coin(self.agg, self.sm, 1)
        self.assertEqual(1, self.sm.coins.pop().value)
        create_coin(self.agg, self.sm, 20)
        self.assertEqual(20, self.sm.coins.pop().value)

    def test_create_coins(self):
        create_coins(self.sm, self.agg, 10)
        self.assertEqual(10, len(self.sm.coins))


class TestNeighborhoodSmartMeters(utest.TestCase):
    def setUp(self):
        self.P = 17
        self.Q = 19
        self.privRSA, self.pubRSA = get_pub_priv_keys(self.P, self.Q)
        self.sms = []
        for i in range(10):
            self.sms.append(SmartMeter(i, self.pubRSA))
        self.agg = Concentrator(self.privRSA)

    def test_create_coin(self):
        for sm in self.sms:
            create_coin(self.agg, sm, 1)
        for sm in self.sms:
            self.assertEqual(1, sm.coins.pop().value)
        for sm in self.sms:
            create_coin(self.agg, sm, 20)
        for sm in self.sms:
            self.assertEqual(20, sm.coins.pop().value)

    def test_create_coins(self):
        for sm in self.sms:
            create_coins(sm, self.agg, 10)
        for sm in self.sms:
            self.assertEqual(10, len(sm.coins))
