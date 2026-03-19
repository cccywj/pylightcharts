"""Grid line rendering layer (horizontal price levels and vertical time intervals)."""
import math

from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import Qt

from pylightcharts.views.base_view import BaseView
from pylightcharts.core.data_manager import DataManager
from pylightcharts.core.viewport import Viewport
from pylightcharts.math.coordinate import CoordinateEngine


class GridView(BaseView):
    """Renders background grid lines for reference.
    
    The grid is used to provide visual reference for both price levels
    (horizontal lines) and time intervals (vertical lines). Grid spacing
    automatically adjusts based on zoom level to maintain clarity.
    """

    def __init__(self) -> None:
        """Initialize the grid view with a subtle dark gray color."""
        super().__init__()
        self.grid_color = QColor("#2A2E39")  # Dark gray, subtle

    def draw(
        self,
        painter: QPainter,
        viewport: Viewport,
        data_manager: DataManager,
        chart_width: int,
        chart_height: int,
    ) -> None:
        """Render all horizontal and vertical grid lines.
        
        See BaseView.draw() for parameter documentation.
        """
        painter.setPen(QPen(self.grid_color, 1, Qt.SolidLine))

        v_mid = viewport.view_mid_price
        v_range = viewport.view_price_range

        # --- STEP 1: Draw Horizontal Grid Lines (Price Levels) ---
        # These provide reference lines for reading price values
        display_min = v_mid - (v_range / 2.0)  # Bottom of visible area
        display_max = v_mid + (v_range / 2.0)  # Top of visible area

        # Choose tick spacing so grid lines don't crowd (50px minimum)
        desired_tick_px = 50
        max_ticks = max(2, min(10, int(chart_height / desired_tick_px)))

        # Calculate a nice step value (e.g., 1.0, 5.0, 10.0)
        step = CoordinateEngine.calculate_nice_step(v_range, max_ticks)

        # Start from the first nice number at or above the bottom
        current_y = math.ceil(display_min / step) * step

        while current_y <= display_max:
            y_pixel = CoordinateEngine.price_to_y(current_y, v_mid, v_range, chart_height)

            if 0 <= y_pixel <= chart_height:
                painter.drawLine(0, int(y_pixel), chart_width, int(y_pixel))

            current_y += step  # Move to next grid line

        # --- STEP 2: Draw Vertical Grid Lines (Time Intervals) ---
        # These provide reference lines for reading time/dates
        data_list = data_manager.get_data_list()
        data_length = len(data_list)
        if data_length == 0:
            return

        left_idx, right_idx = viewport.get_visible_indices(chart_width, data_length)

        # Cache viewport parameters for coordinate math
        scroll = viewport.scroll_index_offset
        t_space = viewport.total_space
        r_blank = viewport.right_blank_space

        # Space vertical lines every 80 pixels to avoid crowding
        last_drawn_x = chart_width + 80

        for i in range(right_idx, left_idx - 1, -1):
            x_center = CoordinateEngine.index_to_x(
                i, data_length, scroll, t_space, r_blank, chart_width
            )

            if x_center < 0:
                break

            if last_drawn_x - x_center >= 80:
                painter.drawLine(int(x_center), 0, int(x_center), chart_height)
                last_drawn_x = x_center