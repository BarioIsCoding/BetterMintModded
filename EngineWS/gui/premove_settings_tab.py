"""
Premove settings tab for BetterMint Modded GUI
Configuration for premove functionality with advanced timing controls
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox, QGroupBox, 
    QGridLayout, QSpinBox
)

from settings import SettingsManager


class PremoveSettingsTab(QWidget):
    """Tab for premove configuration with timing optimization"""
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the Premove Settings tab UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Premove Configuration
        premove_group = QGroupBox("Premove Configuration")
        premove_group.setObjectName("settings_group")
        premove_layout = QGridLayout(premove_group)

        # Enable premoves
        self.premove_checkbox = QCheckBox("Enable Premoves")
        self.premove_checkbox.setChecked(self.settings_manager.get_setting("premove-enabled"))
        self.premove_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("premove-enabled", x))
        premove_layout.addWidget(self.premove_checkbox, 0, 0, 1, 2)

        # Max premoves
        premove_layout.addWidget(QLabel("Max Premoves:"), 1, 0)
        self.max_premoves_spin = QSpinBox()
        self.max_premoves_spin.setRange(1, 10)
        self.max_premoves_spin.setValue(self.settings_manager.get_setting("max-premoves"))
        self.max_premoves_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("max-premoves", x))
        premove_layout.addWidget(self.max_premoves_spin, 1, 1)

        # Premove delay
        premove_layout.addWidget(QLabel("Premove Delay (ms):"), 2, 0)
        self.premove_delay_spin = QSpinBox()
        self.premove_delay_spin.setRange(100, 5000)
        self.premove_delay_spin.setSingleStep(50)
        self.premove_delay_spin.setValue(self.settings_manager.get_setting("premove-time"))
        self.premove_delay_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("premove-time", x))
        premove_layout.addWidget(self.premove_delay_spin, 2, 1)

        # Premove random
        premove_layout.addWidget(QLabel("Random Delay (ms):"), 3, 0)
        self.premove_random_spin = QSpinBox()
        self.premove_random_spin.setRange(0, 2000)
        self.premove_random_spin.setSingleStep(50)
        self.premove_random_spin.setValue(self.settings_manager.get_setting("premove-time-random"))
        self.premove_random_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("premove-time-random", x))
        premove_layout.addWidget(self.premove_random_spin, 3, 1)

        layout.addWidget(premove_group)

        # Advanced Premove Timing
        premove_timing_group = QGroupBox("Advanced Premove Timing")
        premove_timing_group.setObjectName("settings_group")
        premove_timing_layout = QGridLayout(premove_timing_group)

        # Premove random divider
        premove_timing_layout.addWidget(QLabel("Random Divider:"), 0, 0)
        self.premove_div_spin = QSpinBox()
        self.premove_div_spin.setRange(1, 500)
        self.premove_div_spin.setValue(self.settings_manager.get_setting("premove-time-random-div"))
        self.premove_div_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("premove-time-random-div", x))
        premove_timing_layout.addWidget(self.premove_div_spin, 0, 1)

        # Premove random multiplier
        premove_timing_layout.addWidget(QLabel("Random Multiplier:"), 1, 0)
        self.premove_multi_spin = QSpinBox()
        self.premove_multi_spin.setRange(1, 100)
        self.premove_multi_spin.setValue(self.settings_manager.get_setting("premove-time-random-multi"))
        self.premove_multi_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("premove-time-random-multi", x))
        premove_timing_layout.addWidget(self.premove_multi_spin, 1, 1)

        layout.addWidget(premove_timing_group)
        layout.addStretch()
    
    def load_settings(self):
        """Reload settings from settings manager with error handling"""
        try:
            self.premove_checkbox.setChecked(self.settings_manager.get_setting("premove-enabled"))
            self.max_premoves_spin.setValue(self.settings_manager.get_setting("max-premoves"))
            self.premove_delay_spin.setValue(self.settings_manager.get_setting("premove-time"))
            self.premove_random_spin.setValue(self.settings_manager.get_setting("premove-time-random"))
            self.premove_div_spin.setValue(self.settings_manager.get_setting("premove-time-random-div"))
            self.premove_multi_spin.setValue(self.settings_manager.get_setting("premove-time-random-multi"))
        except Exception as e:
            print(f"Error loading premove settings: {e}")