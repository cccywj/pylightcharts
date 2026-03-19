# PyLightCharts

A high-performance, native PySide6 financial charting library with support for real-time tick data aggregation and technical indicators. Designed for trading applications with smooth interactions and low latency rendering.

## Features

- **High-Performance Rendering**: Native PySide6/Qt with optimized drawing layers
- **Real-Time Data**: Live tick aggregation into OHLCV candles with gapless buffering
- **Flexible Data Input**: Works with ib_async, plain dictionaries, or custom objects
- **Multi-Timeframe**: Switch between 1s, 5s, 1m, 5m, 15m, 1H, and daily candles
- **Technical Indicators**: Built-in SMA (Simple Moving Average) and VWAP (Volume Weighted Average Price)
- **Interactive UI**: Mouse-driven zoom/pan with auto-scaling, crosshair, and tooltips
- **Memory Efficient**: Configurable capacity limits with automatic FIFO management

## Installation

### Dependencies

```bash
pip install PySide6
```

### Usage

```bash
# Run the demo application
python main.py --symbol AAPL --timeframe 60 --seed 42

# Command-line options
python main.py --help
```

## Architecture

### Core Components

```
pylightcharts/
├── PyLightChartWidget          # Main public API
├── core/
│   ├── DataManager             # Data storage, tick aggregation, indicators
│   ├── Viewport                # Camera state (pan, zoom, scaling)
│   └── indicators.py           # Technical indicator calculations
├── views/                      # Rendering layers
│   ├── CandleView              # OHLC candlesticks
│   ├── GridView                # Price and time grids
│   ├── AxisView                # Axis labels and borders
│   ├── VolumeView              # Volume bars
│   ├── IndicatorLineView       # Indicator curves (SMA, VWAP)
│   ├── LivePriceView           # Current price line
│   ├── CrosshairView           # Mouse crosshair
│   └── TooltipView             # OHLC tooltip
├── math/
│   └── CoordinateEngine        # Pure math: data↔pixel transformations
├── toolbar.py                  # Timeframe and indicator controls
└── chart.py                    # Internal canvas + public widget
```

### Data Flow

```
External Data Source (Broker, websocket, etc)
         ↓
    Live Ticks → DataManager.update_tick()
         ↓
    [Buffered if historical data pending]
         ↓
    Historical Data → DataManager.apply_historical_data()
         ↓
    [Buffer merged with history]
         ↓
    Candle Data
         ↓
    Indicator Calculation
         ↓
    Rendering Layers (Grid, Candles, Indicators, Axis, etc)
         ↓
    PyLightChartWidget (UI)
```

## API Reference

### PyLightChartWidget

The main public widget you embed in your application.

```python
from PySide6.QtWidgets import QApplication, QMainWindow
from pylightcharts import PyLightChartWidget

class MyTradingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.chart = PyLightChartWidget()
        self.setCentralWidget(self.chart)
        
        # Connect to data requests
        self.chart.historical_data_requested.connect(self.on_need_history)
        
        # Change to a specific symbol
        self.chart.change_symbol("AAPL")
```

#### Public Methods

**`change_symbol(symbol: str) -> None`**
- Switch to a different trading symbol/asset
- Clears existing data and triggers a historical data request
- Emits: `historical_data_requested(symbol, timeframe)`

**`enable_buffering() -> None`**
- Enable buffering mode before requesting historical data
- Subsequent live ticks will be queued until `apply_historical_data()` is called
- Use this to prevent gaps when network latency causes historical data to arrive after some live ticks

**`apply_historical_data(bars: List[Dict]) -> None`**
- Load historical OHLCV bar data and merge with any buffered live ticks
- Argument `bars` should be a list of dicts or ib_async.BarData objects
- Triggers indicator recalculation and UI update

**`update_tick(tick: Union[Dict, Any]) -> None`**
- Process a single market tick and aggregate into the current candle
- Argument can be an ib_async.Ticker, a dict with bid/ask/volume, or similar object
- Invalid or zero prices are silently skipped
- Automatically updates if buffering is disabled, or queues if buffering is enabled

**`set_timeframe(seconds: int) -> None`**
- Programmatically change the candlestick timeframe
- Valid values: 1, 5, 60, 300, 900, 3600, 86400 (seconds)
- Equivalent to using the timeframe dropdown in the toolbar
- Clears existing data and triggers a new historical data request

**`toggle_indicator(code: str) -> None`**
- Enable/disable a technical indicator
- `code` options: "SMA" (Simple Moving Average), "VWAP" (Volume Weighted Average Price), "VOL" (Volume bars)

#### Signals (Qt)

**`historical_data_requested(symbol: str, timeframe: int)`**
- Emitted when the chart needs historical data
- Connect a slot to fetch and pass data to `apply_historical_data()`
- Arguments:
  - `symbol`: Trading symbol/asset name (e.g., "AAPL")
  - `timeframe`: Timeframe in seconds (e.g., 60 for 1 minute)

**`indicator_requested(code: str)`**
- Emitted when user selects an indicator from the toolbar
- Internally handled by default, but available if you need custom logic

### DataManager

Low-level data management (usually accessed through PyLightChartWidget).

```python
from pylightcharts.core.data_manager import DataManager

dm = DataManager(timeframe_seconds=60, max_capacity=10000)

# Add historical data
dm.apply_historical_data(bars_list)

# Process live ticks
dm.update_tick({"bid": 150.1, "ask": 150.3, "time": datetime.now()})

# Manage indicators
dm.add_indicator("SMA", {"period": 14})
dm.remove_indicator("SMA")

# Access data
candles = dm.get_data_list()
visible = dm.get_visible_data(left_idx, right_idx)
```

#### Public Methods

**`__init__(timeframe_seconds: int = 60, max_capacity: int = 10000)`**
- `timeframe_seconds`: Duration of each candlestick (default 60 = 1 minute)
- `max_capacity`: Maximum candles to keep in memory (default 10000)
- Older candles are automatically discarded when capacity is exceeded

**`apply_historical_data(bars: List) -> None`**
- Load and merge historical bars with any buffered live ticks
- Accepts list of dicts or ib_async.BarData objects

**`update_tick(tick) -> None`**
- Aggregate a single live tick into the current candle
- Converts tick midpoint (bid+ask)/2 into OHLC bar
- Skips invalid prices (0, None, NaN) silently

**`enable_buffering() -> None`**
- Start buffering mode for gapless data merging

**`get_data_list() -> List[Dict]`**
- Get all candles, newest at end of list

**`get_visible_data(left_idx: int, right_idx: int) -> List[Dict]`**
- Get a slice of candles for a specific range

**`add_indicator(name: str, params: Dict = None) -> None`**
- Enable a technical indicator
- `name`: "SMA" or "VWAP"
- `params`: For SMA, use `{"period": 14}` (or any period)

**`remove_indicator(name: str) -> None`**
- Disable a technical indicator

#### Properties

**`timeframe: int` (read-only)**
- Returns current timeframe in seconds

**`price_precision: int` (read-only)**
- Auto-detected number of decimal places for price display

### Viewport

Manages camera state (pan, zoom, auto-scale). Usually accessed through chart.viewport.

```python
from pylightcharts.core.viewport import Viewport

vp = chart.viewport
vp.zoom_x(1.0)
vp.reset_to_home()
vp.set_auto_scale(True)
```

#### Public Methods

**`zoom_x(step: float) -> None`**
- Adjust candle width by step (positive = zoom in, negative = zoom out)
- Step values: typically ±0.5 to ±2.0

**`pan_x(pixels: float, max_index: int) -> None`**
- Pan left/right by pixel amount
- `max_index`: Total number of candles (prevents panning beyond bounds)

**`zoom_y(pixels: float) -> None`**
- Adjust price scale (positive = zoom out, negative = zoom in)

**`pan_y(pixels: float, chart_height: int) -> None`**
- Pan price range up/down (Y-panning disabled if auto-scale is on)

**`apply_auto_scale(visible_data: List[Dict]) -> None`**
- Automatically fit Y-axis to visible candle range
- Called automatically by rendering engine if auto_scale is True

**`reset_to_home() -> None`**
- Snap to latest candle, enable auto-scale, reset zoom to default

**`set_auto_scale(state: bool) -> None`**
- Enable/disable automatic Y-axis scaling

**`update_crosshair(x: float, y: float) -> None`**
- Update crosshair position (called by mouse move events)

**`hide_crosshair() -> None`**
- Hide crosshair (called when mouse leaves widget)

## Data Formats

### Input Data: Historical Bars

The chart accepts historical bar data in two formats:

#### Format 1: Plain Dictionary

```python
bars = [
    {
        "time": datetime.datetime.now(datetime.timezone.utc),  # or just datetime.now()
        "open": 150.25,
        "high": 151.50,
        "low": 150.10,
        "close": 151.00,
        "volume": 1000000,  # float or int
    },
    # ... more bars
]
chart.apply_historical_data(bars)
```

**Key fields:**
- `time` or `date`: datetime object (naive or timezone-aware, converted to UTC)
- `open`, `high`, `low`, `close`: float price values
- `volume`: int or float (optional, defaults to 0)

#### Format 2: ib_async.BarData

```python
# From IB API
from ib_insync import ib, Stock

ib_app = ib.IB()
ib_app.connect("127.0.0.1", 7497, clientId=1)

contract = Stock("AAPL", "SMART")
bars = ib_app.reqHistoricalData(contract, endDateTime="", durationStr="30 D", barSizeSetting="1 min")

# Pass directly to chart
chart.apply_historical_data(bars)
```

The DataManager's `_parse_ib_bar()` method extracts OHLCV from ib_async objects automatically.

### Input Data: Live Ticks

Live ticks represent a single price point at a moment in time. The chart aggregates them into candles.

#### Format 1: Plain Dictionary

```python
tick = {
    "time": datetime.datetime.now(datetime.timezone.utc),
    "bid": 150.10,
    "ask": 150.15,
    "volume": 100,  # Optional: share volume
}
chart.update_tick(tick)
```

**Key fields:**
- `time`: datetime object
- `bid`, `ask`: float prices (used to calculate midpoint)
- `price`: Alternative single price if bid/ask unavailable
- `volume`: Optional share count

#### Format 2: ib_async.Ticker

```python
# From IB API
from ib_insync import ib, Stock
from PySide6.QtCore import QTimer

app = QApplication(sys.argv)
ib_app = ib.IB()
ib_app.connect("127.0.0.1", 7497, clientId=1)

contract = Stock("AAPL", "SMART")
ticker = ib_app.reqMktData(contract)

def on_tick():
    chart.update_tick(ticker)

timer = QTimer()
timer.timeout.connect(on_tick)
timer.start(250)  # Update every 250ms
app.exec()
```

The DataManager's `_parse_tick()` method extracts price and volume from ib_async.Ticker automatically.

### Custom Data Objects

The chart also accepts custom objects. The parsing methods use `getattr()` with fallbacks, so any object that has these attributes will work:

```python
class MyTickData:
    def __init__(self, time, bid, ask):
        self.time = time
        self.bid = bid
        self.ask = ask

tick = MyTickData(datetime.datetime.now(), 150.1, 150.15)
chart.update_tick(tick)
```

## Integration Examples

### Example 1: Real-time Stock Market

```python
from ib_insync import ib, Stock, IB
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer
import sys

from pylightcharts import PyLightChartWidget

class StockTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.chart = PyLightChartWidget()
        self.setCentralWidget(self.chart)
        
        # Connect to historical data request
        self.chart.historical_data_requested.connect(self.on_need_history)
        
        # Connect to IB
        self.ib = IB()
        self.ib.connect("127.0.0.1", 7497, clientId=1)
        
        # Subscribe to AAPL
        self.ticker = self.ib.reqMktData(Stock("AAPL", "SMART"))
        
        # Live tick timer
        self.tick_timer = QTimer()
        self.tick_timer.timeout.connect(self.on_live_tick)
        self.tick_timer.start(250)
        
        # Start with AAPL
        self.chart.change_symbol("AAPL")
    
    def on_need_history(self, symbol, timeframe):
        """Historical data request from chart"""
        print(f"Loading {symbol} history at {timeframe}s...")
        
        # Request from IB
        contract = Stock(symbol, "SMART")
        bars = self.ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr="30 D",
            barSizeSetting="1 min" if timeframe == 60 else "1 hour"
        )
        
        # Feed to chart
        self.chart.apply_historical_data(bars)
    
    def on_live_tick(self):
        """Live market tick"""
        self.chart.update_tick(self.ticker)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockTracker()
    window.show()
    sys.exit(app.exec())
```

### Example 2: Cryptocurrency with Websocket

```python
import asyncio
import json
import websockets
from datetime import datetime, timezone
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer, pyqtSignal, QObject
import sys

from pylightcharts import PyLightChartWidget

class CryptoTickBridge(QObject):
    """Bridge between websocket and Qt signals"""
    new_tick = pyqtSignal(dict)
    
    def __init__(self, symbol):
        super().__init__()
        self.symbol = symbol
        self.task = None
    
    async def fetch_ticks(self):
        uri = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@trade"
        async with websockets.connect(uri) as websocket:
            while True:
                msg = json.loads(await websocket.recv())
                tick = {
                    "time": datetime.fromtimestamp(msg["T"] / 1000, tz=timezone.utc),
                    "bid": float(msg["p"]),
                    "ask": float(msg["p"]),
                    "volume": float(msg["q"]),
                }
                self.new_tick.emit(tick)

class CryptoTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.chart = PyLightChartWidget()
        self.setCentralWidget(self.chart)
        
        self.chart.historical_data_requested.connect(self.on_need_history)
        
        # Websocket bridge
        self.ticker_bridge = CryptoTickBridge("btcusdt")
        self.ticker_bridge.new_tick.connect(self.chart.update_tick)
        
        self.chart.change_symbol("BTCUSDT")
    
    def on_need_history(self, symbol, timeframe):
        """Load from REST API, CCData, or file"""
        # Placeholder: load from your preferred source
        bars = []  # Load from API
        self.chart.apply_historical_data(bars)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CryptoTracker()
    window.show()
    sys.exit(app.exec())
```

### Example 3: Load from CSV

```python
import pandas as pd
from datetime import datetime
from pylightcharts import PyLightChartWidget

# Load historical data from CSV
df = pd.read_csv("AAPL_data.csv", parse_dates=["date"])

# Convert to chart format
bars = []
for _, row in df.iterrows():
    bars.append({
        "time": row["date"],
        "open": row["open"],
        "high": row["high"],
        "low": row["low"],
        "close": row["close"],
        "volume": row["volume"],
    })

chart = PyLightChartWidget()
chart.change_symbol("AAPL")
chart.apply_historical_data(bars)
```

## Performance Considerations

### Memory Usage

- Default max capacity: 10,000 candles
- Each candle: ~200-300 bytes in memory
- Total: ~2-3 MB for full history

```python
# Adjust capacity if needed
dm = DataManager(max_capacity=50000)  # Store more history
```

### Rendering Optimization

- Only visible candles are drawn
- Grid lines recalculate only when viewport changes
- Indicator calculations use efficient vectorization
- Double-buffering prevents flicker

### Data Input Rate

- Live tick processing: tested at 1000+ ticks/second
- Batching ticks: recommended for high-frequency feeds

```python
# For high-frequency data, batch updates
@pyqtSlot()
def flush_tick_batch(self):
    for tick in self.tick_queue:
        chart.update_tick(tick)
    self.tick_queue.clear()
```

## Troubleshooting

### Chart shows no data

1. Verify `apply_historical_data()` was called with valid bars
2. Check that bar time is timezone-aware (UTC)
3. Ensure bars are in chronological order (oldest first)

### Prices displayed with wrong precision

- Auto-detected based on latest price
- Override by setting: `chart.data_manager.price_precision = 4`

### Indicators not visible

1. Add the indicator: `chart.toggle_indicator("SMA")`
2. Ensure you have enough data points (SMA period + buffer)
3. Check that indicator calculation doesn't fail silently

### Pan/zoom issues

- Double-click the Y-axis margin to reset auto-scale
- Use toolbar dropdown to change timeframe
- Check mouse events are not being captured elsewhere

## Architecture Decisions

### Why separate DataManager and Viewport?

The chart's data and view state are deliberately decoupled:
- **DataManager**: Handles storage, parsing, aggregation, indicators (stateless math)
- **Viewport**: Manages pan, zoom, camera (stateful UI)
- **Views**: Rendering layers (reusable, testable)

This design allows you to:
- Test data logic without UI
- Swap rendering implementations
- Reuse DataManager for headless analysis

### Why gapless buffering?

When requesting historical data (latency 500ms–2s):
1. User clicks "new symbol"
2. Request sent to broker
3. Live ticks arrive immediately (go to buffer)
4. Historical data arrives
5. Buffer merged with history (gapless)
6. User sees continuous chart with no price gaps

### Why aggregate ticks into candles?

Rather than rendering individual ticks:
- Reduces drawing operations 1000:1
- Maintains OHLC information
- Enables technical indicators
- Standard financial data format

## License

This library is provided as-is for educational and commercial use.

## Contributing

To contribute improvements:
1. Ensure changes maintain backwards compatibility
2. Add docstrings following the existing format
3. Test with multiple data sources (ib_async, dicts, custom objects)
4. Run the demo with `--seed 42` for deterministic testing
