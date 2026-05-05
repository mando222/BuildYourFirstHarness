import statistics
from typing import Optional


def calculate_average(numbers: list[float]) -> float:
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    span = hi - lo
    if span == 0:
        return [0.0] * len(values)
    return [(v - lo) / span for v in values]


def moving_average(values: list[float], window: int) -> list[float]:
    if window <= 0 or window > len(values):
        return []
    return [
        statistics.mean(values[i : i + window])
        for i in range(len(values) - window + 1)
    ]


def filter_outliers(values: list[float], z_threshold: float = 2.0) -> list[float]:
    if len(values) < 2:
        return values
    mean = statistics.mean(values)
    stdev = statistics.stdev(values)
    if stdev == 0:
        return values
    return [v for v in values if abs((v - mean) / stdev) <= z_threshold]


class DataPipeline:
    def __init__(self, data: list[float], window: int = 3):
        self.raw = data
        self.window = window
        self._processed: Optional[list[float]] = None

    def run(self) -> list[float]:
        clean = filter_outliers(self.raw)
        smoothed = moving_average(clean, self.window)
        self._processed = normalize(smoothed)
        return self._processed

    def summary(self) -> dict:
        if self._processed is None:
            self.run()
        return {
            "count": len(self._processed),
            "mean": calculate_average(self._processed),
            "min": min(self._processed),
            "max": max(self._processed),
        }
