"""
Auto-move settings tab for BetterMint Modded GUI
Configuration for automatic move execution with timing and randomization controls
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox, QGroupBox, 
    QGridLayout, QSpinBox
)
from PySide6.QtCore import Signal

from settings import SettingsManager


class AutoMoveSettingsTab(QWidget):
    """Tab for auto-move configuration with intelligent timing"""
    
    settings_changed = Signal()
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the Auto-Move Settings tab UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Auto-Move Configuration
        automove_group = QGroupBox("Auto-Move Configuration")
        automove_group.setObjectName("settings_group")
        automove_layout = QGridLayout(automove_group)

        # Enable auto-move
        self.automove_checkbox = QCheckBox("Enable Legit Auto-Move")
        self.automove_checkbox.setChecked(self.settings_manager.get_setting("legit-auto-move"))
        self.automove_checkbox.toggled.connect(self.on_automove_toggled)
        automove_layout.addWidget(self.automove_checkbox, 0, 0, 1, 2)

        # Base delay
        automove_layout.addWidget(QLabel("Base Delay (ms):"), 1, 0)
        self.automove_delay_spin = QSpinBox()
        self.automove_delay_spin.setRange(0, 30000)
        self.automove_delay_spin.setSingleStep(100)
        self.automove_delay_spin.setValue(self.settings_manager.get_setting("auto-move-time"))
        self.automove_delay_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("auto-move-time", x))
        automove_layout.addWidget(self.automove_delay_spin, 1, 1)

        # Random delay
        automove_layout.addWidget(QLabel("Random Delay (ms):"), 2, 0)
        self.automove_random_spin = QSpinBox()
        self.automove_random_spin.setRange(0, 10000)
        self.automove_random_spin.setSingleStep(100)
        self.automove_random_spin.setValue(self.settings_manager.get_setting("auto-move-time-random"))
        self.automove_random_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("auto-move-time-random", x))
        automove_layout.addWidget(self.automove_random_spin, 2, 1)

        # Best move chance
        automove_layout.addWidget(QLabel("Best Move Chance (%):"), 3, 0)
        self.best_move_spin = QSpinBox()
        self.best_move_spin.setRange(0, 100)
        self.best_move_spin.setValue(self.settings_manager.get_setting("best-move-chance"))
        self.best_move_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("best-move-chance", x))
        automove_layout.addWidget(self.best_move_spin, 3, 1)

        # Random best move
        #self.random_best_checkbox = QCheckBox("Random Best Move Selection")
        #self.random_best_checkbox.setChecked(self.settings_manager.get_setting("random-best-move"))
        #self.random_best_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("random-best-move", x))
        #automove_layout.addWidget(self.random_best_checkbox, 4, 0, 1, 2)

        layout.addWidget(automove_group)

        # Advanced Timing
        timing_group = QGroupBox("Advanced Timing Configuration")
        timing_group.setObjectName("settings_group")
        timing_layout = QGridLayout(timing_group)

        # Randomization divider
        timing_layout.addWidget(QLabel("Random Divider:"), 0, 0)
        self.random_div_spin = QSpinBox()
        self.random_div_spin.setRange(1, 500)
        self.random_div_spin.setValue(self.settings_manager.get_setting("auto-move-time-random-div"))
        self.random_div_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("auto-move-time-random-div", x))
        timing_layout.addWidget(self.random_div_spin, 0, 1)

        # Randomization multiplier
        timing_layout.addWidget(QLabel("Random Multiplier:"), 1, 0)
        self.random_multi_spin = QSpinBox()
        self.random_multi_spin.setRange(1, 2000)
        self.random_multi_spin.setValue(self.settings_manager.get_setting("auto-move-time-random-multi"))
        self.random_multi_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("auto-move-time-random-multi", x))
        timing_layout.addWidget(self.random_multi_spin, 1, 1)

        layout.addWidget(timing_group)
        layout.addStretch()
    
    def on_automove_toggled(self, checked):
        """Handle auto-move toggle with signal emission"""
        try:
            self.settings_manager.set_setting("legit-auto-move", checked)
            self.settings_changed.emit()
        except Exception as e:
            print(f"Error toggling auto-move setting: {e}")
    
    def load_settings(self):
        """Reload settings from settings manager with error handling"""
        try:
            self.automove_checkbox.setChecked(self.settings_manager.get_setting("legit-auto-move"))
            self.automove_delay_spin.setValue(self.settings_manager.get_setting("auto-move-time"))
            self.automove_random_spin.setValue(self.settings_manager.get_setting("auto-move-time-random"))
            self.best_move_spin.setValue(self.settings_manager.get_setting("best-move-chance"))
            self.random_best_checkbox.setChecked(self.settings_manager.get_setting("random-best-move"))
            self.random_div_spin.setValue(self.settings_manager.get_setting("auto-move-time-random-div"))
            self.random_multi_spin.setValue(self.settings_manager.get_setting("auto-move-time-random-multi"))
        except Exception as e:
            print(f"Error loading auto-move settings: {e}")