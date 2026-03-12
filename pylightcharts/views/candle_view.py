from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt

from pylightcharts.views.base_view import BaseView
from pylightcharts.core.data_manager import DataManager
from pylightcharts.core.viewport import Viewport
from pylightcharts.math.coordinate import CoordinateEngine

class CandleView(BaseView):
    """
    Responsible purely for rendering the green and red candlesticks.
    """
    def __init__(self):
        super().__init__()
        # In a fully fleshed out library, these would come from an Options/Theme manager.
        self.bull_color = QColor("#089981") # Up (Green)
        self.bear_color = QColor("#F23645") # Down (Red)

    def draw(self, painter: QPainter, viewport: Viewport, data_manager: DataManager, 
             chart_width: int, chart_height: int):
        
        data_list = data_manager.get_data_list()
        data_length = len(data_list)
        if data_length == 0:
            return

        # 1. Ask the Viewport what data is currently on screen
        left_idx, right_idx = viewport.get_visible_indices(chart_width, data_length)
        visible_data = data_manager.get_visible_data(left_idx, right_idx)
        
        if not visible_data:
            return

        # 2. Tell the Viewport to Auto-Scale the Y-Axis based on what we are about to draw
        viewport.apply_auto_scale(visible_data)

        # Cache viewport state for fast math lookups inside the loop
        v_mid = viewport.view_mid_price
        v_range = viewport.view_price_range
        scroll = viewport.scroll_index_offset
        t_space = viewport.total_space
        r_blank = viewport.right_blank_space
        c_width = viewport.candle_width

        # 3. Draw the Candles (Right to Left)
        for i in range(right_idx, left_idx - 1, -1):
            if i < 0 or i >= data_length:
                continue
                
            d = data_list[i]
            
            # --- Math Translation ---
            # Get physical exact center X pixel for this index
            x_center = CoordinateEngine.index_to_x(i, data_length, scroll, t_space, r_blank, chart_width)
            
            # If the candle has scrolled completely off the left edge, stop drawing
            if x_center + (c_width / 2.0) < 0:
                break 

            # Get physical Y pixels for the OHLC prices
            y_open = CoordinateEngine.price_to_y(d['open'], v_mid, v_range, chart_height)
            y_close = CoordinateEngine.price_to_y(d['close'], v_mid, v_range, chart_height)
            y_high = CoordinateEngine.price_to_y(d['high'], v_mid, v_range, chart_height)
            y_low = CoordinateEngine.price_to_y(d['low'], v_mid, v_range, chart_height)

            # --- Rendering ---
            is_bull = d['close'] >= d['open']
            color = self.bull_color if is_bull else self.bear_color
            
            painter.setPen(QPen(color, 1))
            painter.setBrush(color)

            # Draw Wick (High to Low)
            painter.drawLine(int(x_center), int(y_high), int(x_center), int(y_low))

            # Draw Body using our Coordinate Engine helper
            rect_x, rect_y, rect_w, rect_h = CoordinateEngine.get_candle_rect(x_center, y_open, y_close, c_width)
            painter.fillRect(int(rect_x), int(rect_y), int(rect_w), int(rect_h), color)