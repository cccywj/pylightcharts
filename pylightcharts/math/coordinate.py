"""
Coordinate system translation engine for financial charts.

This module provides pure mathematical transformations between:
- Data space (price values, array indices) and pixel space (X, Y screen coordinates)
- This decouples rendering logic from viewport calculations
"""

import math
from typing import Tuple

class CoordinateEngine:
    """
    Mathematical translation layer for coordinate transformations.
    
    Converts between logical data/price values and physical X/Y pixel coordinates in both directions.
    This layer is viewport-agnostic and deals purely with math, making it easily testable.
    
    Attributes:
        None - this is a stateless utility class with only static methods.
    
    Methods:
        price_to_y: Convert a price value to Y-pixel coordinate
        y_to_price: Convert Y-pixel coordinate to price value
        index_to_x: Convert data array index to X-pixel coordinate
        x_to_index: Convert X-pixel coordinate to data array index
        get_candle_rect: Calculate rectangle bounds for a candlestick body
        calculate_nice_step: Generate human-readable grid intervals
    """

    # ==========================================
    # Y-AXIS: PRICE <-> PIXEL
    # ==========================================

    @staticmethod
    def price_to_y(price: float, view_mid_price: float, view_price_range: float, chart_height: int) -> float:
        """
        Converts a price value to a Y-axis pixel coordinate.
        
        In Qt/PySide6, Y=0 is at the top of the screen and increases downward.
        This method inverts the price scale so higher prices appear higher on screen.
        
        Args:
            price: The price value to convert (e.g., 150.25)
            view_mid_price: The midpoint price currently visible on screen
            view_price_range: The total price range currently visible (e.g., 10.0 for a 10-dollar range)
            chart_height: Height of the chart area in pixels
        
        Returns:
            float: Y-pixel coordinate (0 at top, chart_height at bottom)
        
        Examples:
            >>> CoordinateEngine.price_to_y(150.0, 150.0, 10.0, 800)
            400.0  # Midpoint
            >>> CoordinateEngine.price_to_y(155.0, 150.0, 10.0, 800)
            0.0    # Top of screen (height = 5 dollars above mid)
        """
        if view_price_range <= 0 or chart_height <= 0:
            return 0.0
            
        display_min = view_mid_price - (view_price_range / 2.0)
        normalized_position = (price - display_min) / view_price_range
        
        # Invert because UI coordinates go down, but price goes up
        return chart_height - (normalized_position * chart_height)

    @staticmethod
    def y_to_price(y: float, view_mid_price: float, view_price_range: float, chart_height: int) -> float:
        """
        Converts a Y-axis pixel coordinate (from mouse hover) back into a price value.
        
        This is the inverse of price_to_y(), used when the user hovers/clicks on the chart.
        
        Args:
            y: The pixel Y-coordinate (0 at top, chart_height at bottom)
            view_mid_price: The midpoint price currently visible on screen
            view_price_range: The total price range currently visible
            chart_height: Height of the chart area in pixels
        
        Returns:
            float: The price value at the given Y-pixel position
        
        Examples:
            >>> CoordinateEngine.y_to_price(400, 150.0, 10.0, 800)
            150.0  # Midpoint
            >>> CoordinateEngine.y_to_price(0, 150.0, 10.0, 800)
            155.0  # Top of screen
        """
        if view_price_range <= 0 or chart_height <= 0:
            return 0.0
            
        display_min = view_mid_price - (view_price_range / 2.0)
        normalized_position = (chart_height - y) / chart_height
        
        return display_min + (normalized_position * view_price_range)

    # ==========================================
    # X-AXIS: INDEX <-> PIXEL
    # ==========================================

    @staticmethod
    def index_to_x(index: int, data_length: int, scroll_offset: float, total_candle_space: float, 
                   right_blank_space: float, chart_width: int) -> float:
        """
        Converts a data array index to an X-axis pixel coordinate.
        
        The returned coordinate is the exact CENTER of the candlestick.
        Right-anchored: the latest candle (index = data_length - 1) is always on the right side.
        
        Args:
            index: Data array index (0 = oldest, data_length-1 = newest)
            data_length: Total number of candles in the dataset
            scroll_offset: How many candles the view has been panned left (floating-point)
            total_candle_space: Width of one candle + spacing (candle_width + spacing)
            right_blank_space: Padding on the right side of the chart (for price labels)
            chart_width: Total width of the chart area in pixels
        
        Returns:
            float: X-pixel coordinate of the candle's center
        
        Note:
            - Negative X means the candle is off the left edge of the screen
            - X > chart_width - right_blank_space means off the right edge
        """
        if data_length == 0:
            return 0.0

        # The exact center X pixel of the absolute latest candlestick
        right_anchor_x = chart_width - right_blank_space - (total_candle_space / 2.0)
        
        # How many candles from the latest? Subtract scroll for panning
        candles_from_right = (data_length - 1 - index) - scroll_offset
        
        return right_anchor_x - (candles_from_right * total_candle_space)

    @staticmethod
    def x_to_index(x: float, data_length: int, scroll_offset: float, total_candle_space: float, 
                   right_blank_space: float, chart_width: int) -> int:
        """
        Converts an X-pixel coordinate to the nearest data array index.
        
        This reverses index_to_x(), used when the user hovers/clicks on the chart.
        The returned index is rounded to the nearest candle.
        
        Args:
            x: The pixel X-coordinate
            data_length: Total number of candles in the dataset
            scroll_offset: Current pan offset in candles
            total_candle_space: Width of one candle + spacing
            right_blank_space: Padding on the right side
            chart_width: Width of chart area in pixels
        
        Returns:
            int: Data array index (clamped to [0, data_length-1])
        
        Examples:
            >>> # If the latest candle is at x=900, this returns data_length-1
            >>> CoordinateEngine.x_to_index(900, 300, 0, 10, 100, 1000)
            299
        """
        if data_length == 0 or total_candle_space <= 0:
            return -1

        right_anchor_x = chart_width - right_blank_space - (total_candle_space / 2.0)
        
        # How many candles away from the anchor is this pixel?
        candles_from_right = (right_anchor_x - x) / total_candle_space
        
        # Reverse the math to find the exact float index, then round
        exact_index = (data_length - 1) - scroll_offset - candles_from_right
        
        return int(round(exact_index))

    # ==========================================
    # HELPER METHODS
    # ==========================================

    @staticmethod
    def get_candle_rect(center_x: float, open_y: float, close_y: float, candle_width: float) -> Tuple[float, float, float, float]:
        """
        Calculate the bounding rectangle for a candlestick body.
        
        Creates the rectangle needed for QPainter.fillRect() to draw the main OHLC body
        (not including the wick). The rectangle is centered on center_x and spans from
        the open to close price on the Y-axis.
        
        Args:
            center_x: The X-pixel center of the candlestick
            open_y: The Y-pixel coordinate of the open price
            close_y: The Y-pixel coordinate of the close price
            candle_width: Width of the candlestick in pixels
        
        Returns:
            Tuple[float, float, float, float]: (x, y, width, height) for the rectangle
        
        Note:
            - The height is guaranteed to be at least 1 pixel, even for doji candles
            - Doji handling ensures they remain visible (not collapsed to 0 pixels)
        
        Examples:
            >>> CoordinateEngine.get_candle_rect(100, 200, 180, 8)
            (96.0, 180, 8, 20)  # x, y, width, height
        """
        rect_x = center_x - (candle_width / 2.0)
        rect_y = min(open_y, close_y)
        rect_height = max(abs(open_y - close_y), 1.0)  # Guarantee at least 1px height for visibility
        
        return rect_x, rect_y, candle_width, rect_height
    
    @staticmethod
    def calculate_nice_step(price_range: float, max_ticks: int = 5) -> float:
        """
        Calculate human-readable grid intervals for axis labels and grid lines.
        
        This algorithm generates "nice" step sizes like 0.1, 0.5, 1, 2, 5, 10, 50, 100, etc.
        that are pleasant for human reading, rather than arbitrary floating-point values.
        
        It uses a decade-based algorithm:
        - Find the order of magnitude of the rough step
        - Snap the normalized step to a nice multiplier (1, 2, 5, or 10)
        
        Args:
            price_range: The total price range to divide (e.g., 120.0 for a chart showing $120)
            max_ticks: Desired maximum number of grid lines (default 5, actual may be ±1)
        
        Returns:
            float: A human-readable step size that divides the price_range evenly
        
        Examples:
            >>> CoordinateEngine.calculate_nice_step(100.0, 5)
            20.0  # 5 grid lines at $20 intervals
            >>> CoordinateEngine.calculate_nice_step(0.5, 5)
            0.1   # 5 grid lines at $0.10 intervals
            >>> CoordinateEngine.calculate_nice_step(0.0025, 5)
            0.0005  # Very small ranges (penny stocks, crypto)
        """
        if price_range <= 0:
            return 1.0
        
        rough_step = price_range / max_ticks
        
        # Find the power of 10 magnitude (e.g., 100, 10, 1, 0.1, 0.01)
        magnitude = math.pow(10, math.floor(math.log10(rough_step)))
        normalized_step = rough_step / magnitude
        
        # Snap the normalized step to one of the nice multipliers
        if normalized_step < 1.5:
            nice_multiplier = 1.0
        elif normalized_step < 3.0:
            nice_multiplier = 2.0
        elif normalized_step < 7.0:
            nice_multiplier = 5.0
        else:
            nice_multiplier = 10.0
            
        return nice_multiplier * magnitude