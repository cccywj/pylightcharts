from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPointF

from pylightcharts.views.base_view import BaseView
from pylightcharts.math.coordinate import CoordinateEngine

class IndicatorLineView(BaseView):
    def __init__(self, indicator_name: str, color: str = "#2962FF", thickness: float = 1.5):
        super().__init__()
        self.indicator_name = indicator_name
        self.color = QColor(color)
        self.thickness = thickness

    def draw(self, painter: QPainter, viewport, data_manager, chart_width: int, chart_height: int):
        # Only draw if the indicator exists in the DataManager
        if self.indicator_name not in data_manager.indicator_data:
            return

        values = data_manager.indicator_data[self.indicator_name]
        data_length = len(data_manager.get_data_list())
        if not values or data_length == 0:
            return

        painter.setPen(QPen(self.color, self.thickness, Qt.SolidLine))
        
        left_idx, right_idx = viewport.get_visible_indices(chart_width, data_length)
        v_mid = viewport.view_mid_price
        v_range = viewport.view_price_range
        scroll = viewport.scroll_index_offset
        t_space = viewport.total_space
        r_blank = viewport.right_blank_space

        last_point = None
        
        for i in range(left_idx, right_idx + 1):
            val = values[i]
            if val is None:
                last_point = None
                continue

            x = CoordinateEngine.index_to_x(i, data_length, scroll, t_space, r_blank, chart_width)
            y = CoordinateEngine.price_to_y(val, v_mid, v_range, chart_height)

            current_point = QPointF(x, y)
            
            if last_point is not None:
                painter.drawLine(last_point, current_point)
                
            last_point = current_point