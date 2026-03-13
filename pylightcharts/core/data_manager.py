import datetime
from PySide6.QtCore import QObject, Signal
from .indicators import IndicatorMath # Assumes the math file exists in core/

class DataManager(QObject):
    """
    Manages the OHLCV data array, time-bucketing, and data size limits.
    Completely decoupled from the UI and rendering logic.
    """
    
    # Signal emitted whenever data is added or a live tick modifies a candle.
    # The UI will connect to this signal to trigger a repaint().
    data_changed = Signal() 

    def __init__(self, timeframe_seconds: int = 60, max_capacity: int = 10000):
        super().__init__()
        self._data_list = []
        self._timeframe_seconds = timeframe_seconds
        self._max_capacity = max_capacity

        self.active_indicators = {} # e.g. {"SMA": {"period": 14}}
        self.indicator_data = {}    # e.g. {"SMA": [None, 150, 151...]}

    @property
    def timeframe(self) -> int:
        return self._timeframe_seconds

    def set_timeframe(self, tf_seconds: int):
        """Changes the timeframe resolution and clears the current data."""
        self._timeframe_seconds = tf_seconds
        self._data_list.clear()
        self.indicator_data.clear() # Ensure indicator cache is cleared too
        self.data_changed.emit()

    def get_data_list(self) -> list[dict]:
        """Returns the active list of OHLC dictionaries."""
        return self._data_list

    # --- NEW: Indicator API ---
    def add_indicator(self, name: str, params: dict = None):
        """Registers an indicator and triggers an initial calculation."""
        self.active_indicators[name] = params or {}
        self._recalculate_indicators()
        self.data_changed.emit()

    def remove_indicator(self, name: str):
        """Unregisters an indicator and clears its cached data."""
        if name in self.active_indicators:
            del self.active_indicators[name]
            if name in self.indicator_data:
                del self.indicator_data[name]
            self.data_changed.emit()

    def _recalculate_indicators(self):
        """Runs the math for all active indicators. Called automatically on tick/data load."""
        if not self._data_list:
            return
        
        if "SMA" in self.active_indicators:
            period = self.active_indicators["SMA"].get("period", 14)
            self.indicator_data["SMA"] = IndicatorMath.calculate_sma(self._data_list, period)
            
        if "VWAP" in self.active_indicators:
            self.indicator_data["VWAP"] = IndicatorMath.calculate_vwap(self._data_list)

    def apply_new_data(self, data_list: list[dict]):
        """
        Replaces the current data with a new historical dataset (e.g., from an API fetch).
        Expects a list of dicts with standard keys: 'time', 'open', 'high', 'low', 'close', 'volume'
        """
        # Ensure we only store up to our max capacity to prevent RAM bloat
        self._data_list = data_list[-self._max_capacity:] if len(data_list) > self._max_capacity else data_list
        self._recalculate_indicators() # Update indicators for the new dataset
        self.data_changed.emit()

    def update_tick(self, price: float, timestamp: datetime.datetime, volume: float = 0.0):
        """
        Processes a live tick from a network stream (like ib_async).
        Aggregates the tick into the current candle or creates a new one.
        """
        # 1. Floor timestamp to the nearest timeframe boundary
        ts = timestamp.timestamp()
        floored_ts = (ts // self._timeframe_seconds) * self._timeframe_seconds
        bucket_time = datetime.datetime.fromtimestamp(floored_ts, tz=datetime.timezone.utc)

        # 2. If list is empty, start the first candle
        if not self._data_list:
            self._data_list.append({
                "time": bucket_time,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": volume
            })
            self._recalculate_indicators()
            self.data_changed.emit()
            return

        current_candle = self._data_list[-1]

        # 3. Aggregate or Append
        if bucket_time > current_candle["time"]:
            # Start a brand new candle
            self._data_list.append({
                "time": bucket_time,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": volume
            })
            
            # Enforce max capacity
            if len(self._data_list) > self._max_capacity:
                self._data_list.pop(0)
        else:
            # Update the existing current candle
            current_candle["close"] = price
            current_candle["high"] = max(current_candle["high"], price)
            current_candle["low"] = min(current_candle["low"], price)
            current_candle["volume"] += volume
            
        # 4. Notify the UI
        self._recalculate_indicators() # Update indicators for the live tick
        self.data_changed.emit()

    def get_visible_data(self, left_index: int, right_index: int) -> list[dict]:
        """
        Helper method to slice only the data currently visible on the screen.
        Bounds checking is handled safely.
        """
        left_index = max(0, left_index)
        right_index = min(len(self._data_list) - 1, right_index)
        
        if left_index > right_index or not self._data_list:
            return []
            
        return self._data_list[left_index : right_index + 1]