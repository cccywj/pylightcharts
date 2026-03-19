"""Live price display showing the latest closing price on the Y-axis."""
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt

from pylightcharts.views.base_view import BaseView
from pylightcharts.core.data_manager import DataManager
from pylightcharts.core.viewport import Viewport
from pylightcharts.math.coordinate import CoordinateEngine


class LivePriceView(BaseView):
    """Renders a dashed line at the latest closing price with a price label.
    
    This view always shows the most recent candle's closing price as a
    horizontal dashed line across the entire chart, with the price value
    displayed in a colored tag on the right margin. The color reflects
    whether the latest candle is bullish (green) or bearish (red).
    
    This is useful for quickly identifying the current market price at a glance.
    """

    def __init__(self) -> None:
        """Initialize the live price view with styling."""
        super().__init__()
        self.bull_color = QColor("#089981")  # Green for up
        self.bear_color = QColor("#F23645")  # Red for down
        self.text_color = QColor(Qt.white)  # White text on colored label
        self.font = QFont("Trebuchet MS", 9, QFont.Bold)

    def draw(
        self,
        painter: QPainter,
        viewport: Viewport,
        data_manager: DataManager,
        chart_width: int,
        chart_height: int,
    ) -> None:
        """Render the live price indicator.
        
        See BaseView.draw() for parameter documentation.
        """
        data_list = data_manager.get_data_list()
        if not data_list:
            return

        # Get the absolute latest candle
        latest_candle = data_list[-1]
        last_price = latest_candle["close"]

        # Convert price to pixel Y coordinate
        y = CoordinateEngine.price_to_y(
            last_price,
            viewport.view_mid_price,
            viewport.view_price_range,
            chart_height,
        )

        # Only draw if the price is vertically visible
        if 0 <= y <= chart_height:
            # Determine color based on bull/bear
            is_bull = latest_candle["close"] >= latest_candle["open"]
            color = self.bull_color if is_bull else self.bear_color

            # --- STEP 1: Draw dashed line across the chart ---
            painter.setPen(QPen(color, 1, Qt.DashLine))
            painter.drawLine(0, int(y), chart_width, int(y))

            # --- STEP 2: Draw colored background tag on right margin ---
            label_width = viewport.margin_right - 8
            painter.fillRect(chart_width, int(y) - 10, label_width, 20, color)

            # --- STEP 3: Draw the price text ---
            prec = data_manager.price_precision
            painter.setPen(QPen(self.text_color))
            painter.setFont(self.font)
            painter.drawText(
                chart_width + 5, int(y) + 4, f"{last_price:.{prec}f}"
            )