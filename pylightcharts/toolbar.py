from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLabel
from PySide6.QtCore import Qt, Signal

class ChartToolbar(QWidget):
    timeframe_changed = Signal(int)
    indicator_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(38)
        
        # --- THE FIX ---
        # This tells PySide6 to actually paint the background of a custom QWidget!
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("ChartToolbar { background-color: #131722; border-bottom: 1px solid #2A2E39; }")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.layout.setSpacing(2) # Tighter spacing
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # --- TRADINGVIEW FLAT STYLING ---
        self.combo_style = """
            QComboBox {
                background-color: transparent; 
                color: #B2B5BE; 
                border: none;
                border-radius: 4px; 
                padding: 4px 10px; 
                font-size: 13px; 
                font-weight: bold;
            }
            QComboBox:hover { 
                background-color: #2A2E39; /* Subtle highlight on hover */
                color: #D1D4DC;
            }
            QComboBox::drop-down { 
                border: none; width: 0px; 
            }
            QComboBox QAbstractItemView {
                background-color: #1E222D; 
                color: #D1D4DC; 
                border: 1px solid #2A2E39;
                border-radius: 4px;
                selection-background-color: #2962FF; 
                selection-color: white; 
                outline: none;
            }
        """
        
        self._build_timeframes()
        
        divider = QLabel("  |  ")
        divider.setStyleSheet("color: #2A2E39; font-size: 14px;")
        self.layout.addWidget(divider)
        
        self._build_indicators()

    def _build_timeframes(self):
        self.tf_combo = QComboBox()
        self.tf_combo.setCursor(Qt.PointingHandCursor)
        self.tf_combo.setStyleSheet(self.combo_style)
        
        tfs = [("1s", 1), ("5s", 5), ("1m", 60), ("5m", 300), ("15m", 900), ("1H", 3600), ("1D", 86400)]
        for label, val in tfs:
            self.tf_combo.addItem(label, val)
            
        self.tf_combo.setCurrentIndex(2) # 1m
        self.tf_combo.currentIndexChanged.connect(self._on_tf_changed)
        self.layout.addWidget(self.tf_combo)

    def _build_indicators(self):
        self.ind_combo = QComboBox()
        self.ind_combo.setCursor(Qt.PointingHandCursor)
        self.ind_combo.setStyleSheet(self.combo_style)
        
        self.ind_combo.addItem("ƒx Indicators", "")
        self.ind_combo.addItem("Simple Moving Average", "SMA")
        self.ind_combo.addItem("Volume", "VOL")
        self.ind_combo.addItem("VWAP", "VWAP")
        
        self.ind_combo.currentIndexChanged.connect(self._on_ind_changed)
        self.layout.addWidget(self.ind_combo)

    def _on_tf_changed(self, index):
        self.timeframe_changed.emit(self.tf_combo.itemData(index))

    def _on_ind_changed(self, index):
        code = self.ind_combo.itemData(index)
        if code:
            self.indicator_requested.emit(code)
            self.ind_combo.setCurrentIndex(0) 
            
    def set_timeframe(self, seconds: int):
        idx = self.tf_combo.findData(seconds)
        if idx >= 0:
            self.tf_combo.setCurrentIndex(idx)