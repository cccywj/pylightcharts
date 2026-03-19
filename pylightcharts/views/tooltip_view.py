"""Data tooltip showing OHLC values for the active candle."""
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt, QRect

from pylightcharts.views.base_view import BaseView
from pylightcharts.core.data_manager import DataManager
from pylightcharts.core.viewport import Viewport
from pylightcharts.math.coordinate import CoordinateEngine


class TooltipView(BaseView):
    """Renders a data tooltip showing OHLC values in the top-left corner.
    
    The tooltip displays the Open, High, Low, and Close prices for the active
    candle. By default it shows the latest (rightmost) candle, but when the
    crosshair is active, it switches to show the hovered candle. The text
    color reflects the candle direction (green for bull, red for bear).
    """

    def __init__(self) -> None:
        """Initialize the tooltip view with styling."""
        super().__init__()
        self.bull_color = QColor("#089981")  # Green for up candles
        self.bear_color = QColor("#F23645")  # Red for down candles
        self.bg_color = QColor(19, 23, 34, 220)  # Semi-transparent dark background
        self.font = QFont("Trebuchet MS", 10, QFont.Bold)

    def draw(
        self,
        painter: QPainter,
        viewport: Viewport,
        data_manager: DataManager,
        chart_width: int,
        chart_height: int,
    ) -> None:
        """Render the OHLC tooltip for the active candle.
        
        See BaseView.draw() for parameter documentation.
        """
        data_list = data_manager.get_data_list()
        data_length = len(data_list)
        if data_length == 0:
            return

        # Default to the latest (rightmost) candle
        target_idx = data_length - 1

        # If crosshair is active, show the hovered candle instead
        if viewport.crosshair_visible and viewport.crosshair_x <= chart_width:
            hovered_idx = CoordinateEngine.x_to_index(
                viewport.crosshair_x,
                data_length,
                viewport.scroll_index_offset,
                viewport.total_space,
                viewport.right_blank_space,
                chart_width,
            )
            if 0 <= hovered_idx < data_length:
                target_idx = hovered_idx

        # Extract OHLC data and determine color
        d = data_list[target_idx]
        color = self.bull_color if d["close"] >= d["open"] else self.bear_color
        prec = data_manager.price_precision
        info_text = (
            f"O: {d['open']:.{prec}f}  H: {d['high']:.{prec}f}  "
            f"L: {d['low']:.{prec}f}  C: {d['close']:.{prec}f}"
        )

        # Draw the text box with background
        painter.setFont(self.font)
        painter.setPen(color)
        painter.fillRect(QRect(10, 5, 260, 25), self.bg_color)
        painter.drawText(15, 22, info_text)