import math

from logic.acquisition import create_coins


async def get_num_coins_from_pos_total(total) -> int:
    """
    Get the coins whose energy the household could give
    :param total: energy
    :return:
    """
    assert total >= 0, total
    return int(total // 10)


async def get_num_coins_from_neg_total(total) -> int:
    """
    Get the coins whose energy the household needed
    :param total: energy that the houeshold needed
    :return:
    """
    assert total <= 0, total
    return int(math.ceil((-total) / 10))


def add_coins_to_smart_meter(sm, concentrator, it):
    create_coins(sm, concentrator, it=it)
    return sm
