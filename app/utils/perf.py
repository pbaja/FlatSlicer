import time

class PerfTool:

    def __init__(self):
        self._timer = time.perf_counter()
        self._history = []

    def tick(self, ):
        '''
        Returns time (in miliseconds, rounded to 2 places) elapsed since previous tick call
        '''
        # Calculate elapsed time
        elapsed = time.perf_counter() - self._timer
        result = round(elapsed*1000.0, 2)

        # Add to history
        self._history.append(result)
        while len(self._history) > 20:
            del self._history[0]

        # Update timer
        self._timer = time.perf_counter()
        return result

    def history(self, idx):
        return self._history[idx]