class IndicatorMath:
    @staticmethod
    def calculate_sma(data: list[dict], period: int = 14) -> list[float]:
        """Calculates Simple Moving Average."""
        closes = [d['close'] for d in data]
        sma = [None] * len(closes)
        
        for i in range(period - 1, len(closes)):
            sma[i] = sum(closes[i - period + 1 : i + 1]) / period
        return sma

    @staticmethod
    def calculate_vwap(data: list[dict]) -> list[float]:
        """Calculates Volume Weighted Average Price."""
        vwap = []
        cumulative_tp_v = 0.0
        cumulative_v = 0.0
        
        for d in data:
            typical_price = (d['high'] + d['low'] + d['close']) / 3.0
            volume = d.get('volume', 0.0)
            
            cumulative_tp_v += typical_price * volume
            cumulative_v += volume
            
            if cumulative_v != 0:
                vwap.append(cumulative_tp_v / cumulative_v)
            else:
                vwap.append(typical_price) # Fallback if no volume
                
        return vwap