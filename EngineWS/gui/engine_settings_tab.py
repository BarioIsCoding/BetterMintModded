"""
Engine settings tab for BetterMint Modded GUI
Configuration for server connection and engine parameters
UPDATED: Added threat arrows option
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox, QGroupBox, 
    QGridLayout, QSpinBox, QLineEdit
)

from settings import SettingsManager


class EngineSettingsTab(QWidget):
    """Tab for engine configuration settings"""
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the Engine Settings tab UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Server Configuration
        server_group = QGroupBox("Server Configuration")
        server_group.setObjectName("settings_group")
        server_layout = QGridLayout(server_group)

        # API URL
        server_layout.addWidget(QLabel("WebSocket URL:"), 0, 0)
        self.api_url_edit = QLineEdit()
        self.api_url_edit.setText(self.settings_manager.get_setting("url-api-stockfish"))
        self.api_url_edit.textChanged.connect(lambda x: self.settings_manager.set_setting("url-api-stockfish", x))
        server_layout.addWidget(self.api_url_edit, 0, 1)

        # Use API
        self.api_checkbox = QCheckBox("Use WebSocket API")
        self.api_checkbox.setChecked(self.settings_manager.get_setting("api-stockfish"))
        self.api_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("api-stockfish", x))
        server_layout.addWidget(self.api_checkbox, 1, 0, 1, 2)

        layout.addWidget(server_group)

        # Engine Configuration
        engine_group = QGroupBox("Engine Configuration")
        engine_group.setObjectName("settings_group")
        engine_layout = QGridLayout(engine_group)

        # Depth
        engine_layout.addWidget(QLabel("Search Depth:"), 0, 0)
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 50)
        self.depth_spin.setValue(self.settings_manager.get_setting("depth"))
        self.depth_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("depth", x))
        engine_layout.addWidget(self.depth_spin, 0, 1)

        # MultiPV
        engine_layout.addWidget(QLabel("Analysis Lines:"), 1, 0)
        self.multipv_spin = QSpinBox()
        self.multipv_spin.setRange(1, 10)
        self.multipv_spin.setValue(self.settings_manager.get_setting("multipv"))
        self.multipv_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("multipv", x))
        engine_layout.addWidget(self.multipv_spin, 1, 1)

        # Mate finder
        engine_layout.addWidget(QLabel("Mate Finder Distance:"), 2, 0)
        self.mate_finder_spin = QSpinBox()
        self.mate_finder_spin.setRange(1, 20)
        self.mate_finder_spin.setValue(self.settings_manager.get_setting("mate-finder-value"))
        self.mate_finder_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("mate-finder-value", x))
        engine_layout.addWidget(self.mate_finder_spin, 2, 1)

        layout.addWidget(engine_group)

        # Threat Detection
        threat_group = QGroupBox("Threat Detection")
        threat_group.setObjectName("settings_group")
        threat_layout = QGridLayout(threat_group)

        # Show threat arrows
        self.threat_arrows_checkbox = QCheckBox("Show Threat Arrows")
        self.threat_arrows_checkbox.setChecked(self.settings_manager.get_setting("show-threat-arrows"))
        self.threat_arrows_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("show-threat-arrows", x))
        self.threat_arrows_checkbox.setToolTip("Show green arrows for your threats and red arrows for opponent threats")
        threat_layout.addWidget(self.threat_arrows_checkbox, 0, 0, 1, 2)

        # Maximum player threats
        threat_layout.addWidget(QLabel("Max Player Threats:"), 1, 0)
        self.max_player_threats_spin = QSpinBox()
        self.max_player_threats_spin.setRange(1, 15)
        self.max_player_threats_spin.setValue(self.settings_manager.get_setting("max-player-threats"))
        self.max_player_threats_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("max-player-threats", x))
        self.max_player_threats_spin.setToolTip("Maximum number of green threat arrows to show")
        threat_layout.addWidget(self.max_player_threats_spin, 1, 1)

        # Maximum opponent threats
        threat_layout.addWidget(QLabel("Max Opponent Threats:"), 2, 0)
        self.max_opponent_threats_spin = QSpinBox()
        self.max_opponent_threats_spin.setRange(1, 15)
        self.max_opponent_threats_spin.setValue(self.settings_manager.get_setting("max-opponent-threats"))
        self.max_opponent_threats_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("max-opponent-threats", x))
        self.max_opponent_threats_spin.setToolTip("Maximum number of red threat arrows to show")
        threat_layout.addWidget(self.max_opponent_threats_spin, 2, 1)

        layout.addWidget(threat_group)
        layout.addStretch()
    
    def load_settings(self):
        """Reload settings from settings manager"""
        try:
            self.api_url_edit.setText(self.settings_manager.get_setting("url-api-stockfish"))
            self.api_checkbox.setChecked(self.settings_manager.get_setting("api-stockfish"))
            self.depth_spin.setValue(self.settings_manager.get_setting("depth"))
            self.multipv_spin.setValue(self.settings_manager.get_setting("multipv"))
            self.mate_finder_spin.setValue(self.settings_manager.get_setting("mate-finder-value"))
            self.threat_arrows_checkbox.setChecked(self.settings_manager.get_setting("show-threat-arrows"))
            self.max_player_threats_spin.setValue(self.settings_manager.get_setting("max-player-threats"))
            self.max_opponent_threats_spin.setValue(self.settings_manager.get_setting("max-opponent-threats"))
        except Exception as e:
            print(f"Error loading engine settings: {e}")