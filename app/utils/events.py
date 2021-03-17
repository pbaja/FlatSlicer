from typing import Callable

class Event:
    '''
    Contains list of callbacks that can be called with single function
    '''

    def __init__(self):
        self._callbacks = set()

    def __add__(self, other:Callable) -> 'Event':
        self._callbacks.add(other)
        return self

    def __sub__(self, other:Callable) -> 'Event':
        self._callbacks.remove(other)
        return self

    def __call__(self, *args, **kwargs) -> None:
        for callback in self._callbacks:
            callback(*args, **kwargs)