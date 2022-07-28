from random import randint

from data.actors import SmartMeter, Concentrator


def create_coins(sm: SmartMeter, agg: Concentrator, it=10):
    for payload in range(it):
        create_coin(agg, sm, payload=payload)


def create_coin(agg: Concentrator, sm: SmartMeter, payload=None):
    if payload is None:
        payload = randint(5, 40) % 40
    new_m = sm.get_pub_msg(payload)
    pseudo_sign = agg.pseudo_sign(new_m)
    sign = sm.get_sign(pseudo_sign)
    sm.add_coin(payload, sign)
