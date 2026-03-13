import sys
import random
import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QHBoxLayout, QWidget
from PySide6.QtCore import QTimer

from pylightcharts import PyLightChartWidget

def generate_mock_data(num_candles=200, tf_seconds=60, base_price=150.00):
    data = []
    price = base_price
    now = datetime.datetime.now(datetime.UTC)
    base_time = now - datetime.timedelta(seconds=num_candles * tf_seconds)
    volatility = 0.05 * (tf_seconds ** 0.5)
    
    for i in range(num_candles):
        move = random.uniform(-volatility, volatility)
        open_p = price
        close_p = open_p + move
        high_p = max(open_p, close_p) + random.uniform(0, volatility/2)
        low_p = min(open_p, close_p) - random.uniform(0, volatility/2)
        data.append({
            "time": base_time + datetime.timedelta(seconds=i * tf_seconds),
            "open": round(open_p, 5), "high": round(high_p, 5),
            "low": round(low_p, 5), "close": round(close_p, 5),
            "volume": random.randint(100, 1000)
        })
        price = close_p
    return data

class TradingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyLightCharts - Gapless Buffer Test")
        self.resize(1100, 700)
        
        self.chart = PyLightChartWidget()
        self.setCentralWidget(self.chart)
        
        # Connect to the new Data Hook
        self.chart.historical_data_requested.connect(self.on_chart_requested_data)
        
        self.current_price = 150.00
        
        # Simulate Live Tick Stream (fires 4 times a second, continuously)
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self.on_live_tick)
        self.tick_timer.start(250)

        # Trigger the initial load!
        self.chart.change_symbol("AAPL")

    def on_chart_requested_data(self, symbol, timeframe):
        print(f"[Main App] Hook fired! Requesting history for {symbol} at {timeframe}s")
        
        # Change our mock base price so we can see the symbol changed
        self.current_price = random.uniform(10.0, 500.0)
        print(f"[Main App] Waiting 2 seconds for historical data... (Live ticks are buffering!)")
        
        # Simulate a 2-second network delay from IBKR
        QTimer.singleShot(2000, lambda: self._simulate_ibkr_response(timeframe))

    def _simulate_ibkr_response(self, timeframe):
        print("[Main App] Historical data arrived! Pushing to chart.")
        history = generate_mock_data(300, timeframe, base_price=self.current_price)
        self.current_price = history[-1]['close']
        
        # Hand it to the chart. It will auto-merge with the 2 seconds of buffered live ticks.
        self.chart.apply_historical_data(history)

    def on_live_tick(self):
        volatility = 0.05 * (self.chart.data_manager.timeframe ** 0.5)
        self.current_price += random.uniform(-volatility, volatility)
        
        live_bar = {
            "time": datetime.datetime.now(datetime.UTC),
            "open": self.current_price,
            "high": self.current_price + 0.01,
            "low": self.current_price - 0.01,
            "close": self.current_price,
            "volume": random.randint(1, 15)
        }
        
        # Feed exactly as you would an ib_async bar
        self.chart.update_live_bar(live_bar)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = TradingApp()
    window.show()
    sys.exit(app.exec())