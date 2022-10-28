from lib.logger.structlog import get_logger
import builtins
import traceback
import itertools
import sys

_logger = get_logger('wrappers')


def extend_ctx(logger=_logger):
    """Расширяет контекст ошибок трейсбеком."""
    extend_with = dict()
    try:
        *_, tb = sys.exc_info()
        if tb:
            frames = []
            while tb:
                frames.append(tb.tb_frame)
                tb = tb.tb_next
            last_frame = frames[-1]
            frames = list(map(format_frame, frames))

            # Из-за оберток в трейсбеке накапливается много лишней информации, которую нужно вычистить
            filtered_frames = list(itertools.takewhile(lambda x: x != 'target@bot.metrics.wrappers', reversed(frames)))
            tb_info = ' > '.join(reversed(filtered_frames))
            extend_with['tb'] = tb_info
            last_frame_summary = traceback.extract_stack(last_frame, 1)[0]
            extend_with['line'] = f'{last_frame_summary.lineno}:{last_frame_summary.line}'
    except Exception as e:
        logger.error('cannot extend exception ctx', error=e)
    return extend_with

def format_frame(frame):
    module = frame.f_globals.get('__name__')
    func_name = frame.f_code.co_name
    frame_cls = frame.f_locals.get('self', frame.f_locals.get('cls'))
    if frame_cls:
        if not isinstance(frame_cls, builtins.type):
            frame_cls = frame_cls.__class__
        cls_module = frame_cls.__module__
        cls_name = frame_cls.__name__
        if cls_module != module:
            cls_name = f'{cls_module}.{cls_name}'
        func_name = f'{cls_name}.{func_name}'
    return f'{func_name}@{module}'
