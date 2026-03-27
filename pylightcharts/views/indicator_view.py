"""Indicator line rendering layer for technical analysis overlays."""
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPointF

from pylightcharts.views.base_view import BaseView
from pylightcharts.core.data_manager import DataManager
from pylightcharts.core.viewport import Viewport
from pylightcharts.math.coordinate import CoordinateEngine


class IndicatorLineView(BaseView):
    """Renders a single technical indicator as a continuous line overlay.
    
    Indicators are price-based overlays (like moving averages, VWAP, RSI, etc.)
    that are drawn as smooth lines on top of the candlestick chart. This view
    automatically handles gaps in indicator data (None values) by breaking the
    line, allowing for indicators with warm-up periods.
    
    Multiple instances can be created for different indicators with different
    colors and line widths.
    """

    def __init__(
        self,
        indicator_name: str,
        color: str = "#2962FF",
        thickness: float = 1.5,
    ) -> None:
        """Initialize the indicator line view.
        
        Args:
            indicator_name: The name of the indicator in data_manager.indicator_data
                (e.g., 'SMA', 'VWAP', 'RSI').
            color: Hex color code for the line (default: blue).
            thickness: Line thickness in pixels (default: 1.5).
        """
        super().__init__()
        self.indicator_name = indicator_name
        self.color = QColor(color)
        self.thickness = thickness

    def draw(
        self,
        painter: QPainter,
        viewport: Viewport,
        data_manager: DataManager,
        chart_width: int,
        chart_height: int,
    ) -> None:
        """Render the indicator line for all visible values.
        
        See BaseView.draw() for parameter documentation.
        """
        # Check if this indicator exists in the data manager
        if self.indicator_name not in data_manager.indicator_data:
            return

        values = data_manager.indicator_data[self.indicator_name]
        data_list = data_manager.get_data_list()
        data_length = len(data_list)
        if not values or data_length == 0:
            return

        painter.setPen(QPen(self.color, self.thickness, Qt.SolidLine))

        left_idx, right_idx = viewport.get_visible_indices(chart_width, data_length)
        v_mid = viewport.view_mid_price
        v_range = viewport.view_price_range
        scroll = viewport.scroll_index_offset
        t_space = viewport.total_space
        r_blank = viewport.right_blank_space
        tf_sec = data_manager.timeframe

        i_lo = max(0, left_idx)
        i_hi = min(data_length - 1, right_idx)
        if i_lo > i_hi:
            return

        last_point = None

        # Draw line segments left to right for visible data
        for i in range(i_lo, i_hi + 1):
            val = values[i]
            if val is None:
                # Break the line at gaps (warm-up periods, missing data)
                last_point = None
                continue

            x = CoordinateEngine.time_to_x(
                data_list[i]["time"],
                data_list,
                tf_sec,
                data_length,
                scroll,
                t_space,
                r_blank,
                chart_width,
            )
            y = CoordinateEngine.price_to_y(val, v_mid, v_range, chart_height)

            current_point = QPointF(x, y)

            # Draw line from previous point if it exists
            if last_point is not None:
                painter.drawLine(last_point, current_point)

            last_point = current_point