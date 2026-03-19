"""
Technical indicator calculations for financial charts.

Pure mathematical functions for computing common trading indicators.
These functions are stateless and work with plain lists of OHLCV data.

Supported Indicators:
- SMA: Simple Moving Average - average of closing prices over a period
- VWAP: Volume Weighted Average Price - typical price weighted by volume
"""

from typing import List, Optional

class IndicatorMath:
    """
    Collection of technical indicator calculation functions.
    
    All methods are static and stateless, operating purely on lists of OHLCV data.
    Results are returned as lists of float values or None for insufficient data.
    
    Examples:
        >>> candles = [{"close": 100, "volume": 1000}, {"close": 101, "volume": 1100}, ...]
        >>> sma = IndicatorMath.calculate_sma(candles, period=14)
        >>> vwap = IndicatorMath.calculate_vwap(candles)
    """
    
    @staticmethod
    def calculate_sma(data: List[dict], period: int = 14) -> List[Optional[float]]:
        """
        Calculate Simple Moving Average (SMA).
        
        SMA is the arithmetic mean of closing prices over a specified period.
        Useful for trend identification and smoothing price action.
        
        Args:
            data: List of OHLCV candles, each with 'close' key
            period: Number of periods for the average (default 14)
        
        Returns:
            List of floats: SMA values, None for first (period-1) entries
        
        Formula:
            SMA[n] = sum(close[n-period+1:n+1]) / period
        
        Examples:
            >>> sma = IndicatorMath.calculate_sma(candles, 20)
            >>> [None, None, ..., 150.5, 150.7, ...]  # First 19 are None
        """
        closes = [d['close'] for d in data]
        sma = [None] * len(closes)
        
        for i in range(period - 1, len(closes)):
            sma[i] = sum(closes[i - period + 1 : i + 1]) / period
        return sma

    @staticmethod
    def calculate_vwap(data: List[dict]) -> List[float]:
        """
        Calculate Volume Weighted Average Price (VWAP).
        
        VWAP is the average price weighted by volume, providing insights into
        the true average price paid by all traders. Commonly used to identify
        price support/resistance and volume-weighted momentum.
        
        Args:
            data: List of OHLCV candles, each with 'high', 'low', 'close', and 'volume' keys
        
        Returns:
            List of floats: VWAP values for each candle
        
        Formula:
            TP[n] = (high[n] + low[n] + close[n]) / 3
            VWAP[n] = cumsum(TP * volume) / cumsum(volume)
        
        Note:
            - VWAP is cumulative across all bars (not a fixed lookback period)
            - Each value accounts for all bars from the start of the data
            - Zero volume candles are handled gracefully (uses typical price as fallback)
        
        Examples:
            >>> vwap = IndicatorMath.calculate_vwap(candles)
            >>> [150.0, 150.05, 150.10, ...]
        """
        vwap = []
        cumulative_tp_v = 0.0  # Cumulative typical_price * volume
        cumulative_v = 0.0      # Cumulative volume
        
        for d in data:
            # Typical price: average of high, low, close
            typical_price = (d['high'] + d['low'] + d['close']) / 3.0
            volume = d.get('volume', 0.0)
            
            cumulative_tp_v += typical_price * volume
            cumulative_v += volume
            
            if cumulative_v != 0:
                vwap.append(cumulative_tp_v / cumulative_v)
            else:
                # No volume yet, use typical price as fallback
                vwap.append(typical_price)
                
        return vwap
