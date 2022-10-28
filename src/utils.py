from datetime import timedelta
import asyncio
import functools
from operator import ge
from time import monotonic

from lib.logger.structlog import get_logger

_logger = get_logger('utils')


def create_counter(start=0):
    def counter():
        nonlocal start
        counter.current = start
        start += 1
        return counter.current

    counter.current = start
    return counter


def make_periodic(delay, coro, logger=None):
    """Возвращает новую корутину, которая будет запускать себя снова и снова.

    Если delay не положительный (False, 0, '', -1), то функция выполнится
    один раз. Даже в таком случае функция полезна, т.к. логи будут
    вестись с контекстом.

    :param delay: Интервал, через который будет запускаться coro.
    :type delay: int, double, timedelta
    """

    if isinstance(delay, timedelta):
        delay = delay.total_seconds()

    logger = logger or _logger.with_fields(coro=coro.__name__)

    @functools.wraps(coro)
    async def periodic():
        nonlocal delay
        cycle = create_counter()

        logger.info('started')
        while True:
            try:
                logger.set_fields(coro_cycle=cycle(), func=coro.__name__)
                logger.debug('started cycle')
                start = monotonic()
                await coro(ctx=logger.context())
                logger.debug('finished cycle', time=monotonic() - start)
            except asyncio.CancelledError:
                delay = 0  # stop
            except Exception as e:
                logger.exception('failed', error=e)

            if not delay:
                logger.info('stopped')
                return

            try:
                logger.debug('sleep', delay=delay)
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                logger.info('stopped')
                return

    return periodic