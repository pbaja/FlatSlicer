import time

class PerfTool:

    _timer = 0
    _history = []

    @staticmethod
    def tick():
        '''
        Returns time (in miliseconds, rounded to 2 places) elapsed since previous tick call
        '''
        # Calculate elapsed time
        elapsed = time.perf_counter() - PerfTool._timer
        result = round(elapsed*1000.0, 2)

        # Add to history
        PerfTool._history.append(result)
        while len(PerfTool._history) > 20:
            del PerfTool._history[0]

        # Update timer
        PerfTool._timer = time.perf_counter()
        return result

    @staticmethod
    def history(idx):
        return PerfTool._history[idx]