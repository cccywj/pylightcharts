"""Crosshair overlay showing price/time at cursor position with snapping."""
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QRect

from pylightcharts.views.base_view import BaseView
from pylightcharts.core.data_manager import DataManager
from pylightcharts.core.viewport import Viewport
from pylightcharts.math.coordinate import CoordinateEngine


class CrosshairView(BaseView):
    """Renders an interactive crosshair overlay that follows the mouse.
    
    The crosshair consists of:
    1. Dashed cross lines (horizontal and vertical) at the cursor position
    2. Price label on the Y-axis margin showing hovered price
    3. Time label on the X-axis margin showing hovered candle time
    
    The crosshair X position automatically snaps to the nearest candle center
    for precise price/time reading ("magnetic snapping"). The crosshair is
    hidden when the mouse leaves the chart area.
    """

    def __init__(self) -> None:
        """Initialize the crosshair view with styling."""
        super().__init__()
        self.crosshair_color = QColor("#9598A1")  # Gray crosshair lines
        self.label_bg_color = QColor("#2A2E39")  # Dark gray label background
        self.text_color = QColor(Qt.white)  # White text on labels
        self.font = QFont("Trebuchet MS", 9)

    def _get_time_format(self, tf_seconds: int) -> str:
        """Return appropriate time format based on timeframe.
        
        Args:
            tf_seconds: Timeframe in seconds.
            
        Returns:
            A strftime format string suitable for the timeframe.
        """
        if tf_seconds >= 86400:
            return "%Y-%m-%d"  # Daily and above: full date
        elif tf_seconds >= 60:
            return "%H:%M"  # Hourly and above: hour:minute
        else:
            return "%H:%M:%S"  # Seconds: full time

    def draw(
        self,
        painter: QPainter,
        viewport: Viewport,
        data_manager: DataManager,
        chart_width: int,
        chart_height: int,
    ) -> None:
        """Render the crosshair overlay with price and time labels.
        
        See BaseView.draw() for parameter documentation.
        """
        # Exit early if crosshair is hidden or outside chart bounds
        if not viewport.crosshair_visible:
            return
        if viewport.crosshair_x > chart_width or viewport.crosshair_y > chart_height:
            return

        data_list = data_manager.get_data_list()
        data_length = len(data_list)
        if data_length == 0:
            return

        # --- STEP 1: Determine which candle is hovered (reverse coordinate math) ---
        # Convert mouse X pixel back to a data index
        hovered_idx = CoordinateEngine.x_to_index(
            viewport.crosshair_x,
            data_length,
            viewport.scroll_index_offset,
            viewport.total_space,
            viewport.right_blank_space,
            chart_width,
        )

        # Clamp to valid data range
        hovered_idx = max(0, min(data_length - 1, hovered_idx))

        # --- STEP 2: Snap the X position to the bar time (same as candles / grid) ---
        snap_x = CoordinateEngine.time_to_x(
            data_list[hovered_idx]["time"],
            data_list,
            data_manager.timeframe,
            data_length,
            viewport.scroll_index_offset,
            viewport.total_space,
            viewport.right_blank_space,
            chart_width,
        )

        painter.setFont(self.font)

        # --- STEP 3: Draw the crosshair lines (dashed cross) ---
        painter.setPen(QPen(self.crosshair_color, 1, Qt.DashLine))
        painter.drawLine(int(snap_x), 0, int(snap_x), chart_height)  # Vertical line
        painter.drawLine(
            0, int(viewport.crosshair_y), chart_width, int(viewport.crosshair_y)
        )  # Horizontal line

        # --- STEP 4: Draw Y-Axis Price Label ---
        # Convert Y pixel back to price
        hover_price = CoordinateEngine.y_to_price(
            viewport.crosshair_y,
            viewport.view_mid_price,
            viewport.view_price_range,
            chart_height,
        )

        # Draw price label in the right margin
        label_width = viewport.margin_right - 8
        painter.fillRect(
            chart_width,
            int(viewport.crosshair_y) - 10,
            label_width,
            20,
            self.label_bg_color,
        )
        prec = data_manager.price_precision
        painter.setPen(QPen(self.text_color))
        painter.drawText(
            chart_width + 5,
            int(viewport.crosshair_y) + 4,
            f"{hover_price:.{prec}f}",
        )

        # --- STEP 5: Draw X-Axis Time Label ---
        # Get the time from the hovered candle
        time_fmt = self._get_time_format(data_manager.timeframe)
        time_str = data_list[hovered_idx]["time"].strftime(time_fmt)

        # Draw time label in the bottom margin
        painter.fillRect(
            int(snap_x) - 35,
            chart_height,
            70,
            viewport.margin_bottom,
            self.label_bg_color,
        )
        painter.setPen(QPen(self.text_color))
        painter.drawText(int(snap_x) - 30, chart_height + 18, time_str)