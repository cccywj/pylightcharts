from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QWheelEvent, QColor
from PySide6.QtCore import Qt, QPoint

from pylightcharts.core.data_manager import DataManager
from pylightcharts.core.viewport import Viewport
from pylightcharts.views.candle_view import CandleView

class PyLightChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Initialize core non-UI components
        self.data_manager = DataManager()
        self.viewport = Viewport()
        
        # 2. Initialize rendering layers
        self.candle_view = CandleView()
        
        # 3. Widget Configuration
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.bg_color = "#131722" # Background color

        # 4. Connect Signals
        # Whenever data or the camera changes, schedule a repaint
        self.data_manager.data_changed.connect(self.update)
        self.viewport.viewport_changed.connect(self.update)

        # Interaction State
        self.drag_mode = None
        self.last_mouse_pos = QPoint()

    # ==========================================
    # PUBLIC API (The "React-like" Interface)
    # ==========================================
    def apply_new_data(self, data):
        self.data_manager.apply_new_data(data)

    def update_data(self, price, timestamp):
        self.data_manager.update_tick(price, timestamp)

    def set_timeframe(self, seconds):
        self.data_manager.set_timeframe(seconds)

    # ==========================================
    # PYSIDE6 EVENT HANDLERS
    # ==========================================
    def wheelEvent(self, event: QWheelEvent):
        zoom_step = 0.5 if event.angleDelta().y() > 0 else -0.5
        self.viewport.zoom_x(zoom_step)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            chart_w = self.width() - self.viewport.margin_right # Optional: Move margins to Viewport
            
            # Simple hit testing for axis vs chart
            if pos.x() > (self.width() - 65): # Using the margin_right from before
                self.drag_mode = 'y_axis'
            else:
                self.drag_mode = 'chart'
            self.last_mouse_pos = pos
    
    def mouseDoubleClickEvent(self, event):
        # Reset auto-scale on double click in Y-Axis
        if event.position().toPoint().x() > (self.width() - self.viewport.margin_right):
            self.viewport.set_auto_scale(True)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        
        if self.drag_mode == 'chart':
            dx = pos.x() - self.last_mouse_pos.x()
            dy = pos.y() - self.last_mouse_pos.y()
            
            # Pan X
            self.viewport.pan_x(dx, len(self.data_manager.get_data_list()))
            # Pan Y
            self.viewport.pan_y(dy, self.height() - self.viewport.margin_bottom)
            
            self.last_mouse_pos = pos
        elif self.drag_mode == 'y_axis':
            dy = pos.y() - self.last_mouse_pos.y()
            self.viewport.zoom_y(dy)
            self.last_mouse_pos = pos
            
        self.update()

    def mouseReleaseEvent(self, event):
        self.drag_mode = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()

        painter.fillRect(0, 0, w, h, QColor(self.bg_color))

        # Calculate the actual inner chart dimensions based on margins
        chart_w = w - self.viewport.margin_right
        chart_h = h - self.viewport.margin_bottom
        
        # Execute the View Pipeline
        # You can add more views here (Grid, Axis, etc.) later
        self.candle_view.draw(
            painter, 
            self.viewport, 
            self.data_manager, 
            w, h
        )