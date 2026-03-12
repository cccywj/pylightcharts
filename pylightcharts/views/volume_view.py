from PySide6.QtGui import QPainter, QColor
from pylightcharts.views.base_view import BaseView
from pylightcharts.math.coordinate import CoordinateEngine

class VolumeView(BaseView):
    def __init__(self):
        super().__init__()
        # Use opacity (the 4th number: 120) so it sits subtly in the background
        self.bull_color = QColor(8, 153, 129, 120) 
        self.bear_color = QColor(242, 54, 69, 120)
        self.visible = False # Toggled via the toolbar

    def draw(self, painter: QPainter, viewport, data_manager, chart_width: int, chart_height: int):
        if not self.visible:
            return
            
        data_list = data_manager.get_data_list()
        data_length = len(data_list)
        if data_length == 0:
            return

        left_idx, right_idx = viewport.get_visible_indices(chart_width, data_length)
        visible_data = data_manager.get_visible_data(left_idx, right_idx)
        if not visible_data:
            return

        # 1. Find the highest volume currently on screen to scale against
        max_vol = max((d.get('volume', 0) for d in visible_data), default=1)
        if max_vol == 0: max_vol = 1

        # Volume bars will take up a maximum of 20% of the chart height
        max_height_px = chart_height * 0.20 
        base_y = chart_height

        scroll = viewport.scroll_index_offset
        t_space = viewport.total_space
        r_blank = viewport.right_blank_space

        # 2. Draw the bars
        for i in range(right_idx, left_idx - 1, -1):
            d = data_list[i]
            vol = d.get('volume', 0)
            if vol <= 0: continue

            # Calculate height ratio
            h_px = (vol / max_vol) * max_height_px
            
            x_center = CoordinateEngine.index_to_x(i, data_length, scroll, t_space, r_blank, chart_width)
            if x_center + (viewport.candle_width / 2.0) < 0:
                break
                
            rect_x, rect_y, rect_w, rect_h = CoordinateEngine.get_candle_rect(
                x_center, base_y - h_px, base_y, viewport.candle_width
            )

            color = self.bull_color if d['close'] >= d['open'] else self.bear_color
            painter.fillRect(int(rect_x), int(rect_y), int(rect_w), int(rect_h), color)