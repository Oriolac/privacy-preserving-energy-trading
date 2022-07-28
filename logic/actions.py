import asyncio
import logging

from data import InvalidationRequest
from data.actors import Concentrator, SmartMeter
from logic.acquisition import create_coin


class Locker:
    def __init__(self):
        self.lock = asyncio.Lock()

    async def send_invalidate_request(
        self, agg: Concentrator, meter: SmartMeter, last_coins: int
    ):
        for i in range(last_coins):
            logging.info("Invalidate request from", meter.id)
            invalidation: InvalidationRequest = meter.create_invalidation_request()
            async with self.lock:
                ack = agg.receive_invalidation_request(invalidation)
            meter.check_invalidation_request(invalidation, ack)

    async def send_invalidate_offer(
        self, agg: Concentrator, meter: SmartMeter, last_coins: int
    ):
        for i in range(last_coins):
            logging.info(f"Invalidate offer from {meter.id}")
            invalidation = meter.create_invalidation_offer()
            async with self.lock:
                ack = agg.receive_invalidation_offer(invalidation)
            meter.check_invalidation_offer(invalidation, ack)

    async def energy_matching(
        self, concentrator: Concentrator, producer: SmartMeter, consumer: SmartMeter
    ):
        logging.info(f"Energy Matching. Producer: {producer} // Consumer: {consumer}")
        async with self.lock:
            pairing = concentrator.generate_pairing()
            payment = consumer.do_payment(pairing)
            coin, receipt = producer.decrypt_payment(payment)
            concentrator.checks_receipt(payment.hashed_receipt, receipt.value)
            create_coin(concentrator, producer)

    async def energy_request(self, concentrator: Concentrator, consumer: SmartMeter):
        logging.info(f"Energy Request. {consumer}")
        async with self.lock:
            last_j = concentrator.get_last_request()
        request = consumer.generate_request(last_j + 1)
        async with self.lock:
            concentrator.add_request(request)

    async def energy_offer(self, concentrator: Concentrator, producer: SmartMeter):
        logging.info(f"Energy Offer. {producer}")
        async with self.lock:
            last_i = concentrator.get_last_offer()
        offer = producer.generate_offer(last_i + 1)
        async with self.lock:
            concentrator.add_offer(offer)

    async def write_coins(self, i, meter):
        async with self.lock:
            with open("coins.csv", "a") as file_coins:
                file_coins.write(
                    f"{meter.id},{i},{len(meter.coins)},{len(meter.current_offers)},{len(meter.current_requests)}\n"
                )
