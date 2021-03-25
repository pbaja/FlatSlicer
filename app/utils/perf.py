import time

class PerfTool:

    def __init__(self):
        self._timer = time.perf_counter()
        self._history = {}

    def __str__(self):
        return ", ".join(f'{k}: {v} ms' for k, v in self._history.items())

    def tick(self, tag=''):
        '''
        Returns time (in miliseconds, rounded to 2 places) elapsed since previous tick call
        '''
        # Calculate elapsed time
        elapsed = time.perf_counter() - self._timer
        result = round(elapsed*1000.0, 2)

        # Add to history
        self._history[tag] = result

        # Update timer
        self._timer = time.perf_counter()
        return result

    def history(self, tag):
        return self._history.get(tag, None)

    def total(self):
        return round(sum(self._history.values()), 2)

    @staticmethod
    def decorate(func):
        tool = PerfTool()
        def wrapper(*args, **kwargs):
            tool.tick()
            result = func(*args, **kwargs)
            tool.tick()
            print(f'Function {func.__name__} executed in {tool.history(-1)} ms')
            return result
        return wrapper