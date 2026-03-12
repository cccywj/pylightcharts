from PySide6.QtGui import QPainter
from pylightcharts.core.data_manager import DataManager
from pylightcharts.core.viewport import Viewport

class BaseView:
    """
    Abstract Base Class for all rendering layers.
    Every visual component in the chart must inherit from this and implement draw().
    """
    def __init__(self):
        pass

    def draw(self, painter: QPainter, viewport: Viewport, data_manager: DataManager, 
             chart_width: int, chart_height: int):
        """
        Executes the drawing logic for this specific layer.
        Must be overridden by child classes.
        """
        raise NotImplementedError("Every view must implement the draw() method.")