"""Base view class providing the abstract interface for all chart rendering layers."""
from PySide6.QtGui import QPainter
from pylightcharts.core.data_manager import DataManager
from pylightcharts.core.viewport import Viewport


class BaseView:
    """
    Abstract Base Class for all chart rendering layers.
    
    Every visual component in the chart (axes, candles, volume, indicators, etc.)
    must inherit from this class and implement the draw() method.
    
    The rendering system uses a layered approach where each view is responsible
    for a single logical visual component. Views are drawn in order from background
    to foreground, allowing proper composition of complex visualizations.
    """

    def __init__(self) -> None:
        """Initialize the base view. Subclasses should call super().__init__()."""
        pass

    def draw(
        self,
        painter: QPainter,
        viewport: Viewport,
        data_manager: DataManager,
        chart_width: int,
        chart_height: int,
    ) -> None:
        """
        Execute the drawing logic for this specific layer.
        
        This method is called once per paint cycle and should handle all rendering
        for this layer. Coordinates are in pixels relative to the chart area.
        
        Args:
            painter: Qt painter object for drawing primitives.
            viewport: Viewport state containing zoom, pan, and crosshair info.
            data_manager: Central data repository with OHLCV candles and indicators.
            chart_width: Width of the main chart area (excluding margins) in pixels.
            chart_height: Height of the main chart area (excluding margins) in pixels.
        
        Raises:
            NotImplementedError: If not overridden by a child class.
        """
        raise NotImplementedError("Every view must implement the draw() method.")