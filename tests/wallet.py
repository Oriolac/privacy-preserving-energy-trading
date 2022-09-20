import asyncio
import unittest as utest

from logic.wallet import get_num_coins_from_pos_total, get_num_coins_from_neg_total


class Coins(utest.TestCase):

    def setUp(self) -> None:
        self.values = [10, 20, 50, 34, 23, 102.343, 43]
        self.production_coins = [1, 2, 5, 3, 2, 10, 4]
        self.consumption_coins = [1, 2, 5, 4, 3, 11, 5]

    async def with_coins(self, values, coins, assertion):
        for production, expected_coin in zip(values, coins):
            current_coin = await assertion(production)
            self.assertEqual(current_coin, expected_coin)

    def test_production_coins(self):
        asyncio.run(self.with_coins(self.values, self.production_coins, get_num_coins_from_pos_total))

    def test_consumption_coins(self):
        asyncio.run(self.with_coins(list(map(lambda x: -x, self.values)), self.consumption_coins, get_num_coins_from_neg_total))
