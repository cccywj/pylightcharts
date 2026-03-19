"""Axis view renders price (Y-axis) and time (X-axis) labels with grid dividers."""
import math

from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt

from pylightcharts.views.base_view import BaseView
from pylightcharts.core.data_manager import DataManager
from pylightcharts.core.viewport import Viewport
from pylightcharts.math.coordinate import CoordinateEngine


class AxisView(BaseView):
    """Renders Y-axis price labels and X-axis time labels with frame borders.
    
    This view handles two independent tasks:
    1. Right margin Y-axis: Price level labels with automatic tick spacing
    2. Bottom margin X-axis: Time labels with magnetic snapping to candle centers
    
    The axis uses "nice" step values to ensure labels are round numbers and
    don't overlap, providing a clean professional appearance.
    """

    def __init__(self) -> None:
        """Initialize the axis view with styling colors and fonts."""
        super().__init__()
        self.text_color = QColor("#B2B5BE")  # Light gray text
        self.axis_line_color = QColor("#2A2E39")  # Dark gray dividers
        self.font = QFont("Trebuchet MS", 9)  # TradingView-style font

    def _get_time_format(self, tf_seconds: int) -> str:
        """Return the appropriate datetime format string based on timeframe.
        
        Args:
            tf_seconds: Timeframe in seconds.
            
        Returns:
            A strftime-compatible format string (e.g., '%H:%M' for minute/hourly).
        """
        if tf_seconds >= 86400: # Daily
            return '%Y-%m-%d'
        elif tf_seconds >= 60:  # Minute/Hourly
            return '%H:%M'
        else:                   # Seconds
            return '%H:%M:%S'

    def draw(
        self,
        painter: QPainter,
        viewport: Viewport,
        data_manager: DataManager,
        chart_width: int,
        chart_height: int,
    ) -> None:
        """Render all axis labels and frame dividers.
        
        See BaseView.draw() for parameter documentation.
        """
        painter.setFont(self.font)
        v_mid = viewport.view_mid_price
        v_range = viewport.view_price_range

        # --- STEP 1: Draw Frame Borders (dividing chart from margins) ---
        painter.setPen(QPen(self.axis_line_color, 1, Qt.SolidLine))
        # Vertical divider line
        painter.drawLine(chart_width, 0, chart_width, chart_height)
        # Horizontal divider line (draws all the way across the widget including the margin)
        painter.drawLine(0, chart_height, chart_width + viewport.margin_right, chart_height)
        
        # --- STEP 2: Draw Y-Axis Text (Price levels on right margin) ---
        painter.setPen(self.text_color)
        display_min = v_mid - (v_range / 2.0)  # Bottom price of viewport
        display_max = v_mid + (v_range / 2.0)  # Top price of viewport

        # Choose tick spacing so labels don't overlap (50px minimum between ticks)
        desired_tick_px = 50
        max_ticks = max(2, min(10, int(chart_height / desired_tick_px)))

        # Calculate a "nice" step value (e.g., 0.5, 1.0, 5.0, 10.0)
        step = CoordinateEngine.calculate_nice_step(v_range, max_ticks)

        # Align ticks to multiples of the step value for professional appearance
        first_tick = math.floor(display_min / step) * step
        last_tick = math.ceil(display_max / step) * step
        num_ticks = int(round((last_tick - first_tick) / step)) + 1

        # Format labels using the data manager's price precision
        prec = data_manager.price_precision
        text_rect_width = max(0, viewport.margin_right - 10)

        for i in range(num_ticks):
            price = first_tick + (i * step)
            price = round(price, prec)  # Avoid floating point artifacts
            y_pixel = CoordinateEngine.price_to_y(price, v_mid, v_range, chart_height)

            if 0 <= y_pixel <= chart_height:
                # Draw price label right-aligned in the margin
                label_rect = (chart_width + 5, int(y_pixel) - 8, text_rect_width, 16)
                painter.drawText(
                    *label_rect,
                    Qt.AlignRight | Qt.AlignVCenter,
                    f"{price:.{prec}f}",
                )

        # --- STEP 3: Draw X-Axis Text (Time labels on bottom margin) ---
        data_list = data_manager.get_data_list()
        data_length = len(data_list)
        if data_length == 0:
            return

        # Get the visible range and viewport parameters for coordinate math
        left_idx, right_idx = viewport.get_visible_indices(chart_width, data_length)
        scroll = viewport.scroll_index_offset
        t_space = viewport.total_space
        r_blank = viewport.right_blank_space
        time_fmt = self._get_time_format(data_manager.timeframe)

        # Draw time labels at 80-pixel intervals to avoid crowding
        last_drawn_x = chart_width + 80

        for i in range(right_idx, left_idx - 1, -1):
            # Convert data index to pixel coordinate
            x_center = CoordinateEngine.index_to_x(
                i, data_length, scroll, t_space, r_blank, chart_width
            )

            # Stop when we scroll off the left edge
            if x_center < 0:
                break

            # Only draw if we have 80+ pixels since the last label
            if last_drawn_x - x_center >= 80:
                time_str = data_list[i]["time"].strftime(time_fmt)
                painter.drawText(int(x_center) - 25, chart_height + 20, time_str)
                last_drawn_x = x_center