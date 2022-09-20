import asyncio
import logging
from functools import reduce
from typing import List

import pandas as pd

import toml

from data import PubRSA
from data.actors import SmartMeter, Concentrator
from logic.actions import Locker
from logic.crypt import get_pub_priv_keys
from logic.wallet import (
    get_num_coins_from_pos_total,
    get_num_coins_from_neg_total,
    add_coins_to_smart_meter,
)


def smart_meters(pubRSA: PubRSA):
    i = 0
    while True:
        yield SmartMeter(i, pubRSA)
        i += 1


async def meter_thread(concentrator, meter: SmartMeter, df, type_: str, locker: Locker):
    isize = 1 if type_ == "small" else 2
    last_total_energy = 0

    for i in range(df.shape[0] // 10):
        total_energy = await get_total_energy(df, i, isize)
        await manage_requests_and_offers(
            locker, concentrator, meter, total_energy, last_total_energy
        )
        last_total_energy = total_energy
        await locker.write_coins(i, meter)
        await asyncio.sleep(1.5)


async def manage_requests_and_offers(
        locker, concentrator, meter: SmartMeter, total_energy, last_total_energy
):
    """
    Total energy can be positive (production > consumption), negative (production < consumption) or 0 (do nothing).
    the same as last_total_energy.

    When it changes the state from being a producer to a consumer and viceversa, the smart meter must send a message
    through the concentrator since it must cancel production or consumption packages respectively.

    When the meter is a consumer, the concentrator should definitely deliver electricity although the neighbours
    cannot afford to do it so.

    :param locker:
    :param concentrator:
    :param meter:
    :param total_energy:
    :param last_total_energy:
    :return:
    """
    if total_energy > 0:
        if last_total_energy < 0:
            last_coins = await get_num_coins_from_neg_total(
                last_total_energy
            )  # TODO get_num_coins could be called only  once (?)
            await locker.send_invalidate_request(concentrator, meter, last_coins)
            last_total_energy = total_energy
        diff_energy = ((total_energy // 10) - (last_total_energy // 10)) * 10
        if diff_energy > 0:
            for _ in range(await get_num_coins_from_pos_total(diff_energy)):
                await locker.energy_offer(concentrator, meter)
        elif diff_energy < 0:
            coins_to_invalid = await get_num_coins_from_neg_total(diff_energy)
            logging.info(f"Invalidate {coins_to_invalid} offers from {meter.id} as diff energy {diff_energy}")
            await locker.send_invalidate_offer(concentrator, meter, coins_to_invalid)
    elif total_energy < 0:
        if last_total_energy > 0:
            last_coins = await get_num_coins_from_pos_total(last_total_energy)
            await locker.send_invalidate_offer(concentrator, meter, last_coins)
            last_total_energy = total_energy
        diff_energy = ((total_energy // 10) - (last_total_energy // 10)) * 10
        if diff_energy > 0:
            num_requests_to_invalid = await get_num_coins_from_pos_total(diff_energy)
            logging.info(f"Invalidate {num_requests_to_invalid} requests from {meter.id} as diff energy {diff_energy} = {total_energy} - {last_total_energy}")
            await locker.send_invalidate_request(
                concentrator, meter, num_requests_to_invalid
            )
        else:
            for _ in range(await get_num_coins_from_neg_total(diff_energy)):
                await locker.energy_request(concentrator, meter)


async def get_total_energy(df, i, isize):
    current = df.iloc[i * 10: (i + 1) * 10]
    consumption = current["power_consumption"].sum()
    production = current.iloc(axis=1)[isize].sum()
    total = production - consumption
    return total


# check num of offers perdudes, que no passen a ser enllaçades
# temps mitjà que una offer passa a ser enllaçada a un .csv

# al no invalidar, s'ha de mirar quantes offerts has demanat


def tasks_generator(DATAFRAME, METERS, TYPE_METERS, agg: Concentrator, locker: Locker):
    """
    It creates the meter threads by giving the aggregator, meter instance, dataframe, type and locker.
    :param DATAFRAME: df
    :param METERS: Dict[i, Meter]
    :param TYPE_METERS: List[str]
    :param agg:
    :param locker:
    :return:
    """
    res = []
    for ((i, meter), type_) in zip(METERS.items(), TYPE_METERS):
        res.append(
            asyncio.create_task(meter_thread(agg, meter, DATAFRAME, type_, locker))
        )
    return res


def flatten(xs):
    return reduce(lambda x, y: list(x) + list(y), xs)


async def main(locker: Locker):
    logging.basicConfig(filename="example.log", encoding="utf-8", level=logging.DEBUG)
    CONFIG = toml.load("config.toml")
    TYPE_METERS: List[str] = flatten(
        map(lambda x: [x[0] for _ in range(x[1])], CONFIG["environment"].items()),
    )
    NUM_METERS = len(TYPE_METERS)
    DATAFRAME = pd.read_csv(CONFIG["consumption"], index_col=0)

    privRSA, pubRSA = get_pub_priv_keys(*CONFIG["crypt"].values())
    concentrator = Concentrator(privRSA)
    METERS = dict(
        map(
            lambda x: (x[0], add_coins_to_smart_meter(x[1], concentrator, 5)),
            zip(range(NUM_METERS), smart_meters(pubRSA)),
        )
    )
    sms = list(METERS.values())

    for task in tasks_generator(DATAFRAME, METERS, TYPE_METERS, concentrator, locker):
        await task

    """ Energy offer """
    print("\nEnergy offer")
    meter = sms[0]
    await locker.energy_offer(concentrator, meter)
    print(concentrator)

    """ Energy Request """
    print("\nEnergy request")
    consumer = sms[1]
    await locker.energy_request(concentrator, consumer)
    print(concentrator)

    """ Energy Matching """
    print("\nEnergy Matching")
    await locker.energy_matching(concentrator, meter, consumer)
    print("producer", sms[0])
    print("consumer", sms[1])


if __name__ == "__main__":
    locker = Locker()
    asyncio.run(main(locker))
