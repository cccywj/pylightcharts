from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel
from PySide6.QtGui import QPainter, QWheelEvent, QColor
from PySide6.QtCore import Qt, QPoint, Signal

from pylightcharts.core.data_manager import DataManager
from pylightcharts.core.viewport import Viewport
from pylightcharts.toolbar import ChartToolbar
from pylightcharts.views.candle_view import CandleView
from pylightcharts.views.grid_view import GridView        
from pylightcharts.views.axis_view import AxisView
from pylightcharts.views.crosshair_view import CrosshairView
from pylightcharts.views.tooltip_view import TooltipView
from pylightcharts.views.indicator_view import IndicatorLineView
from pylightcharts.views.volume_view import VolumeView

# ==========================================
# INTERNAL CANVAS (Handles the Drawing)
# ==========================================
class _ChartCanvas(QWidget):
    """Internal widget that strictly handles mouse events and rendering."""
    def __init__(self, data_manager: DataManager, viewport: Viewport):
        super().__init__()
        self.data_manager = data_manager
        self.viewport = viewport
        
        # 2. Initialize rendering layers
        self.grid_view = GridView()
        self.volume_view = VolumeView() 
        self.candle_view = CandleView()

        # --- Indicator Layers ---
        self.sma_view = IndicatorLineView("SMA", "#2962FF")   # Blue SMA line
        self.vwap_view = IndicatorLineView("VWAP", "#E0D714") # Yellow VWAP line
        
        self.axis_view = AxisView()
        self.crosshair_view = CrosshairView()
        self.tooltip_view = TooltipView()
        
        # 3. Widget Configuration
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.bg_color = "#131722" # Background color
        
        # Interaction State
        self.drag_mode = None
        self.last_mouse_pos = QPoint()

    # ==========================================
    # PYSIDE6 EVENT HANDLERS
    # ==========================================
    def wheelEvent(self, event: QWheelEvent):
        zoom_step = 0.5 if event.angleDelta().y() > 0 else -0.5
        self.viewport.zoom_x(zoom_step)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            chart_w = self.width() - self.viewport.margin_right 
            chart_h = self.height() - self.viewport.margin_bottom
            
            # Simple hit testing for axis vs chart
            if pos.x() > chart_w and pos.y() < chart_h:
                self.drag_mode = 'y_axis'
            elif pos.x() < chart_w and pos.y() > chart_h:
                self.drag_mode = 'x_axis'
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
            self.viewport.pan_x(dx, len(self.data_manager.get_data_list()))
            self.viewport.pan_y(dy, self.height() - self.viewport.margin_bottom)
            self.last_mouse_pos = pos
        elif self.drag_mode == 'x_axis':
            dx = pos.x() - self.last_mouse_pos.x()
            self.viewport.zoom_x(dx * 0.05)
            self.last_mouse_pos = pos
        elif self.drag_mode == 'y_axis':
            dy = pos.y() - self.last_mouse_pos.y()
            self.viewport.zoom_y(dy)
            self.last_mouse_pos = pos
        else:
            # If not dragging, we are just hovering! Tell the viewport!
            self.viewport.update_crosshair(pos.x(), pos.y())
            
        self.update()

    def mouseReleaseEvent(self, event):
        self.drag_mode = None

    def leaveEvent(self, event):
        # Hide crosshair when mouse leaves widget
        self.viewport.hide_crosshair()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor(self.bg_color))

        # Calculate the actual inner chart dimensions based on margins
        chart_w = w - self.viewport.margin_right
        chart_h = h - self.viewport.margin_bottom
        
        # 2. Execute the Render Pipeline (Layering)
        self.grid_view.draw(painter, self.viewport, self.data_manager, chart_w, chart_h)
        
        # Draw volume BEFORE candles so it sits behind the price action
        self.volume_view.draw(painter, self.viewport, self.data_manager, chart_w, chart_h) 
        
        self.candle_view.draw(painter, self.viewport, self.data_manager, chart_w, chart_h)
        
        # --- Indicator Render Pipeline ---
        self.sma_view.draw(painter, self.viewport, self.data_manager, chart_w, chart_h)
        self.vwap_view.draw(painter, self.viewport, self.data_manager, chart_w, chart_h)
        
        # 3. Axes and Borders
        self.axis_view.draw(painter, self.viewport, self.data_manager, chart_w, chart_h)
        
        # 4. Crosshair and Floating Labels
        self.crosshair_view.draw(painter, self.viewport, self.data_manager, chart_w, chart_h)
        
        # 5. Top-Left OHLC Legend
        self.tooltip_view.draw(painter, self.viewport, self.data_manager, chart_w, chart_h)


# ==========================================
# MAIN PUBLIC WIDGET (The "React-like" Component)
# ==========================================
class PyLightChartWidget(QWidget):
    """
    The main library component. Contains the UI toolbar and the drawing canvas.
    Emits signals to the parent application when user requests changes.
    """
    
    # --- Hooks for the Main App ---
    timeframe_requested = Signal(int) # Emits the requested timeframe in seconds
    indicator_requested = Signal(str) # Emits the name of the requested indicator

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Initialize core non-UI components
        self.data_manager = DataManager()
        self.viewport = Viewport()
        
        # Setup Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 2. Initialize Toolbar Component
        self.toolbar = ChartToolbar()
        self.main_layout.addWidget(self.toolbar)
        
        # 3. Initialize Canvas Component
        self.canvas = _ChartCanvas(self.data_manager, self.viewport)
        self.main_layout.addWidget(self.canvas)
        
        # 4. Connect Signals
        # Whenever data or the camera changes, schedule a repaint on the canvas
        self.data_manager.data_changed.connect(self.canvas.update)
        self.viewport.viewport_changed.connect(self.canvas.update)
        
        # Connect Toolbar signals to internal logic
        self.toolbar.timeframe_changed.connect(self._handle_tf_changed)
        self.toolbar.indicator_requested.connect(self.toggle_indicator)

    def _handle_tf_changed(self, tf_seconds):
        """Internal handler for timeframe changes."""
        self.data_manager.set_timeframe(tf_seconds)
        self.timeframe_requested.emit(tf_seconds)

    # ==========================================
    # PUBLIC API
    # ==========================================
    def apply_new_data(self, data):
        """Replaces the current data with a new historical dataset."""
        self.data_manager.apply_new_data(data)

    def update_data(self, price, timestamp, volume=0.0):
        """Processes a live tick."""
        self.data_manager.update_tick(price, timestamp, volume)

    def set_timeframe(self, seconds):
        """Sets the timeframe programmatically and updates the toolbar UI."""
        self.toolbar.set_timeframe(seconds)

    def toggle_indicator(self, ind_code: str):
        """Allows toggling an indicator on/off directly."""
        # Handle the custom Volume view toggle
        if ind_code == "VOL":
            self.canvas.volume_view.visible = not self.canvas.volume_view.visible
            self.canvas.update()
            return

        # Handle math-based indicators (SMA, VWAP)
        if ind_code in self.data_manager.active_indicators:
            self.data_manager.remove_indicator(ind_code)
        else:
            params = {"period": 14} if ind_code == "SMA" else {}
            self.data_manager.add_indicator(ind_code, params)