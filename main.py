import sys
import random
import datetime
from PySide6.QtWidgets import QApplication, QMainWindow
from pylightcharts import PyLightChartWidget

def generate_mock_data(num_candles=200, tf_seconds=60):
    data = []
    price = 150.00
    now = datetime.datetime.now()
    base_time = now - datetime.timedelta(seconds=num_candles * tf_seconds)
    
    for i in range(num_candles):
        move = random.uniform(-0.5, 0.5)
        open_p = price
        close_p = open_p + move
        high_p = max(open_p, close_p) + random.uniform(0, 0.2)
        low_p = min(open_p, close_p) - random.uniform(0, 0.2)
        
        data.append({
            "time": base_time + datetime.timedelta(seconds=i * tf_seconds),
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": random.randint(100, 1000)
        })
        price = close_p
    return data

class TradingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyLightCharts Library Test")
        self.resize(1100, 700)
        
        # Instantiate using your preferred class name
        self.chart = PyLightChartWidget()
        self.setCentralWidget(self.chart)
        
        # Load test data
        history = generate_mock_data(300, 60)
        self.chart.apply_new_data(history)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradingApp()
    window.show()
    sys.exit(app.exec())