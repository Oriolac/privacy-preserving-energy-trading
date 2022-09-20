import asyncio
import unittest as utest

from data.actors import Concentrator, SmartMeter
from logic.acquisition import create_coins
from logic.actions import Locker
from logic.crypt import get_pub_priv_keys


class GenerateOneOffer(utest.TestCase):

    def setUp(self) -> None:
        self.P = 17
        self.Q = 19
        self.privRSA, self.pubRSA = get_pub_priv_keys(self.P, self.Q)
        self.sms: dict[int, SmartMeter] = {i:SmartMeter(i, self.pubRSA) for i in range(19)}
        self.agg = Concentrator(self.privRSA)
        for sm in self.sms.values():
            create_coins(sm, self.agg, 10)
        self.locker = Locker()

    def test_generate_offer(self):
        async def run():
            await self.locker.energy_offer(self.agg, self.sms[1])
            self.assertEqual(1, len(self.sms[1].current_offers))
            self.assertEqual(0, len(self.sms[1].current_requests))
            self.assertEqual(1, self.sms[1].current_offers.popitem()[0])
        asyncio.run(run())

    def test_generate_request(self):
        async def run():
            await self.locker.energy_request(self.agg, self.sms[1])
            self.assertEqual(0, len(self.sms[1].current_offers))
            self.assertEqual(1, len(self.sms[1].current_requests))
            self.assertEqual(1, self.sms[1].current_requests.popitem()[0])
        asyncio.run(run())


    def test_pairing(self):
        async def run():
            await self.locker.energy_offer(self.agg, self.sms[0])
            await self.locker.energy_request(self.agg, self.sms[1])
            await self.locker.energy_matching(self.agg, self.sms[0], self.sms[1])
            self.assertEqual(0, len(self.sms[0].current_offers))
            self.assertEqual(0, len(self.sms[1].current_requests))
        asyncio.run(run())



