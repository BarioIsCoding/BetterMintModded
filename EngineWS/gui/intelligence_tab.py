"""
Intelligence tab for advanced engine behavior configuration
Updated with NEW intelligence control features: Disable Intelligence + Avoid Low Intelligence
ENHANCED: Full Rodent IV personality integration with UCI options display
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
    QCheckBox, QGroupBox, QGridLayout, QDoubleSpinBox,
    QPushButton, QMessageBox, QButtonGroup, QScrollArea, QSpinBox,
    QComboBox, QFrame, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from settings import SettingsManager


class IntelligenceTab(QWidget):
    """Intelligence tab with NEW intelligence control features, clean styling, and Rodent IV personality integration"""
    
    settings_changed = Signal()
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.intelligence_enabled = True
        self.rodent_available = self._check_rodent_availability()
        self.setup_ui()
        self.load_settings()
    
    def _check_rodent_availability(self):
        """Check if Rodent IV engine is available"""
        try:
            from constants import RODENT_PATH
            import os
            return os.path.exists(RODENT_PATH)
        except:
            return False
    
    def setup_ui(self):
        """Setup the Intelligence tab UI with NEW control features and Rodent IV integration"""
        # Set Arial font for the entire tab
        arial_font = QFont("Arial", 9)
        self.setFont(arial_font)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(10, 10, 10, 10)

        # NEW: Enhanced Intelligence Master Control with both features
        control_group = QGroupBox("Intelligence Control")
        control_group.setObjectName("settings_group")
        control_layout = QGridLayout(control_group)
        control_layout.setSpacing(15)
        control_layout.setContentsMargins(20, 20, 20, 20)

        # Row 0: Master Intelligence Toggle
        self.intelligence_toggle_btn = QPushButton("Disable Intelligence")
        self.intelligence_toggle_btn.setMinimumHeight(32)
        self.intelligence_toggle_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:checked {
                background-color: #f44336;
                color: white;
            }
        """)
        self.intelligence_toggle_btn.clicked.connect(self.toggle_intelligence)
        control_layout.addWidget(self.intelligence_toggle_btn, 0, 0, 1, 2)

        desc_label = QLabel("Completely disables all intelligence features (uses pure engine moves)")
        desc_label.setWordWrap(True)
        control_layout.addWidget(desc_label, 0, 2, 1, 2)

        # Row 1: NEW - Avoid Low Intelligence Feature
        self.avoid_low_intelligence_cb = QCheckBox("Avoid Low Intelligence")
        self.avoid_low_intelligence_cb.setStyleSheet("font-weight: bold; color: #FF9800;")
        self.avoid_low_intelligence_cb.toggled.connect(self.on_avoid_low_intelligence_changed)
        control_layout.addWidget(self.avoid_low_intelligence_cb, 1, 0)

        avoid_desc_label = QLabel("Falls back to engine moves when intelligent evaluation is too low")
        avoid_desc_label.setWordWrap(True)
        control_layout.addWidget(avoid_desc_label, 1, 1, 1, 3)

        # Row 2: NEW - Threshold Control (only visible when avoid feature is enabled)
        threshold_label = QLabel("Low Intelligence Threshold:")
        threshold_label.setIndent(20)  # Indent to show it's a sub-setting
        control_layout.addWidget(threshold_label, 2, 0)

        self.threshold_spinbox = QDoubleSpinBox()
        self.threshold_spinbox.setRange(-3.0, -1.0)
        self.threshold_spinbox.setSingleStep(0.1)
        self.threshold_spinbox.setDecimals(1)
        self.threshold_spinbox.setValue(-1.5)
        self.threshold_spinbox.setSuffix(" pawns")
        self.threshold_spinbox.setToolTip("If intelligent move evaluation <= this threshold, use engine move instead")
        self.threshold_spinbox.valueChanged.connect(self.on_threshold_changed)
        control_layout.addWidget(self.threshold_spinbox, 2, 1)

        threshold_desc_label = QLabel("Threshold for switching to engine moves (-3.0 = very low, -1.0 = moderately low)")
        threshold_desc_label.setWordWrap(True)
        threshold_desc_label.setStyleSheet("color: #666; font-size: 11px;")
        control_layout.addWidget(threshold_desc_label, 2, 2, 1, 2)

        # Store threshold controls for enable/disable
        self.threshold_label = threshold_label
        self.threshold_desc = threshold_desc_label

        layout.addWidget(control_group)

        # Create scroll area for the rest of the intelligence settings
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2b2b2b;
                border: none;
                font-family: Arial;
            }
            QScrollArea * {
                font-family: Arial;
            }
        """)

        # Main content widget
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                font-family: Arial;
            }
            QWidget * {
                font-family: Arial;
            }
            QLabel {
                font-family: Arial;
            }
            QPushButton {
                font-family: Arial;
            }
            QCheckBox {
                font-family: Arial;
            }
            QComboBox {
                font-family: Arial;
            }
            QSpinBox {
                font-family: Arial;
            }
            QDoubleSpinBox {
                font-family: Arial;
            }
        """)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(25)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Move Multipliers Section
        self.create_multipliers_section(content_layout)
        
        # Piece Preferences Section
        self.create_piece_section(content_layout)
        
        # Emotional Behavior Section
        self.create_emotions_section(content_layout)
        
        # NEW: Rodent IV Personality Section
        if self.rodent_available:
            self.create_rodent_personality_section(content_layout)
        
        # NEW: Enhanced Info Section with intelligence control information
        self.create_info_section(content_layout)

        content_layout.addStretch()

        # Set up scroll area
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
    
    def create_multipliers_section(self, parent_layout):
        """Create move multipliers section with clean layout"""
        group = QGroupBox("Move Multipliers")
        group.setObjectName("settings_group")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        row = 0
        
        # Aggressiveness Contempt
        layout.addWidget(QLabel("Aggressiveness Contempt:"), row, 0)
        self.aggressiveness_slider = QSlider(Qt.Horizontal)
        self.aggressiveness_slider.setRange(0, 200)
        self.aggressiveness_slider.setValue(100)
        self.aggressiveness_slider.valueChanged.connect(self.on_aggressiveness_changed)
        layout.addWidget(self.aggressiveness_slider, row, 1)
        self.aggressiveness_display = QLabel("1.00")
        self.aggressiveness_display.setMinimumWidth(60)
        layout.addWidget(self.aggressiveness_display, row, 2)
        
        row += 1
        
        # Passiveness Contempt
        layout.addWidget(QLabel("Passiveness Contempt:"), row, 0)
        self.passiveness_slider = QSlider(Qt.Horizontal)
        self.passiveness_slider.setRange(0, 200)
        self.passiveness_slider.setValue(100)
        self.passiveness_slider.valueChanged.connect(self.on_passiveness_changed)
        layout.addWidget(self.passiveness_slider, row, 1)
        self.passiveness_display = QLabel("1.00")
        self.passiveness_display.setMinimumWidth(60)
        layout.addWidget(self.passiveness_display, row, 2)
        
        row += 1
        
        # Trading Preference
        layout.addWidget(QLabel("Trading Preference:"), row, 0)
        self.trading_spin = QDoubleSpinBox()
        self.trading_spin.setRange(-2.0, 1.0)
        self.trading_spin.setSingleStep(0.1)
        self.trading_spin.setDecimals(1)
        self.trading_spin.setValue(0.0)
        self.trading_spin.valueChanged.connect(self.on_trading_changed)
        layout.addWidget(self.trading_spin, row, 1, 1, 2)
        
        row += 1
        
        # Capture Preference
        layout.addWidget(QLabel("Capture Preference:"), row, 0)
        self.capture_slider = QSlider(Qt.Horizontal)
        self.capture_slider.setRange(0, 300)
        self.capture_slider.setValue(100)
        self.capture_slider.valueChanged.connect(self.on_capture_changed)
        layout.addWidget(self.capture_slider, row, 1)
        self.capture_display = QLabel("1.00")
        self.capture_display.setMinimumWidth(60)
        layout.addWidget(self.capture_display, row, 2)
        
        row += 1
        
        # Castle Preference
        layout.addWidget(QLabel("Castle Preference:"), row, 0)
        self.castle_slider = QSlider(Qt.Horizontal)
        self.castle_slider.setRange(0, 500)
        self.castle_slider.setValue(100)
        self.castle_slider.valueChanged.connect(self.on_castle_changed)
        layout.addWidget(self.castle_slider, row, 1)
        self.castle_display = QLabel("1.00")
        self.castle_display.setMinimumWidth(60)
        layout.addWidget(self.castle_display, row, 2)
        
        row += 1
        
        # En Passant Preference
        layout.addWidget(QLabel("En Passant Preference:"), row, 0)
        self.en_passant_slider = QSlider(Qt.Horizontal)
        self.en_passant_slider.setRange(0, 300)
        self.en_passant_slider.setValue(100)
        self.en_passant_slider.valueChanged.connect(self.on_en_passant_changed)
        layout.addWidget(self.en_passant_slider, row, 1)
        self.en_passant_display = QLabel("1.00")
        self.en_passant_display.setMinimumWidth(60)
        layout.addWidget(self.en_passant_display, row, 2)
        
        row += 1
        
        # Promotion Preference
        layout.addWidget(QLabel("Promotion Preference:"), row, 0)
        self.promotion_slider = QSlider(Qt.Horizontal)
        self.promotion_slider.setRange(0, 500)
        self.promotion_slider.setValue(100)
        self.promotion_slider.valueChanged.connect(self.on_promotion_changed)
        layout.addWidget(self.promotion_slider, row, 1)
        self.promotion_display = QLabel("1.00")
        self.promotion_display.setMinimumWidth(60)
        layout.addWidget(self.promotion_display, row, 2)
        
        row += 1
        
        # Checkboxes
        self.early_castling_cb = QCheckBox("Prefer Early Castling")
        self.early_castling_cb.toggled.connect(self.on_early_castling_changed)
        layout.addWidget(self.early_castling_cb, row, 0, 1, 3)
        
        row += 1
        
        self.prefer_pins_cb = QCheckBox("Prefer Pins")
        self.prefer_pins_cb.toggled.connect(self.on_pins_changed)
        layout.addWidget(self.prefer_pins_cb, row, 0, 1, 3)
        
        row += 1
        
        # Castle Side Preference
        self.castle_side_cb = QCheckBox("Prefer Specific Castle Side")
        self.castle_side_cb.toggled.connect(self.on_castle_side_enabled_changed)
        layout.addWidget(self.castle_side_cb, row, 0, 1, 3)
        
        row += 1
        
        # Castle side buttons with clear visual indication
        castle_container = QWidget()
        castle_layout = QHBoxLayout(castle_container)
        castle_layout.setContentsMargins(30, 10, 30, 10)  # Indent from left
        castle_layout.setSpacing(20)
        
        self.kingside_btn = QPushButton("Kingside")
        self.queenside_btn = QPushButton("Queenside")
        self.kingside_btn.setCheckable(True)
        self.queenside_btn.setCheckable(True)
        self.kingside_btn.setMinimumHeight(35)
        self.queenside_btn.setMinimumHeight(35)
        self.kingside_btn.setMinimumWidth(120)
        self.queenside_btn.setMinimumWidth(120)
        
        # Create button group for exclusive selection
        self.castle_side_group = QButtonGroup()
        self.castle_side_group.addButton(self.kingside_btn)
        self.castle_side_group.addButton(self.queenside_btn)
        self.castle_side_group.setExclusive(True)
        
        self.kingside_btn.toggled.connect(self.on_castle_side_changed)
        self.queenside_btn.toggled.connect(self.on_castle_side_changed)
        
        castle_layout.addWidget(self.kingside_btn)
        castle_layout.addWidget(self.queenside_btn)
        castle_layout.addStretch()
        
        self.castle_buttons_widget = castle_container
        self.castle_buttons_widget.setVisible(False)
        layout.addWidget(self.castle_buttons_widget, row, 0, 1, 3)
        
        parent_layout.addWidget(group)
    
    def create_piece_section(self, parent_layout):
        """Create piece preferences section"""
        group = QGroupBox("Piece Movement Preferences")
        group.setObjectName("settings_group")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.piece_sliders = {}
        self.piece_displays = {}
        pieces = [("Pawn", "pawn"), ("Knight", "knight"), ("Bishop", "bishop"), 
                 ("Rook", "rook"), ("Queen", "queen"), ("King", "king")]
        
        for i, (piece_name, piece_key) in enumerate(pieces):
            row = i // 2
            col = (i % 2) * 3
            
            layout.addWidget(QLabel(f"{piece_name} Preference:"), row, col)
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 300)
            slider.setValue(100)
            slider.valueChanged.connect(lambda val, key=piece_key: self.on_piece_changed(key, val))
            layout.addWidget(slider, row, col + 1)
            
            display = QLabel("1.00")
            display.setMinimumWidth(60)
            layout.addWidget(display, row, col + 2)
            
            self.piece_sliders[piece_key] = slider
            self.piece_displays[piece_key] = display
        
        parent_layout.addWidget(group)
    
    def create_emotions_section(self, parent_layout):
        """Create emotional behavior section"""
        group = QGroupBox("Emotional Behavior")
        group.setObjectName("settings_group")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Stalemate Probability
        layout.addWidget(QLabel("Stalemate Probability:"), 0, 0)
        self.stalemate_slider = QSlider(Qt.Horizontal)
        self.stalemate_slider.setRange(0, 100)
        self.stalemate_slider.setValue(0)
        self.stalemate_slider.valueChanged.connect(self.on_stalemate_changed)
        layout.addWidget(self.stalemate_slider, 0, 1)
        self.stalemate_display = QLabel("0%")
        self.stalemate_display.setMinimumWidth(60)
        layout.addWidget(self.stalemate_display, 0, 2)
        
        # Emotion checkboxes
        self.stay_equal_cb = QCheckBox("Stay Equal Mode")
        self.stay_equal_cb.toggled.connect(self.on_stay_equal_changed)
        layout.addWidget(self.stay_equal_cb, 1, 0, 1, 3)
        
        self.promote_queen_cb = QCheckBox("Always Promote to Queen")
        self.promote_queen_cb.toggled.connect(self.on_promote_queen_changed)
        layout.addWidget(self.promote_queen_cb, 2, 0, 1, 3)
        
        self.checkmate_immediately_cb = QCheckBox("Checkmate Immediately")
        self.checkmate_immediately_cb.toggled.connect(self.on_checkmate_changed)
        layout.addWidget(self.checkmate_immediately_cb, 3, 0, 1, 3)
        
        parent_layout.addWidget(group)
    
    def create_rodent_personality_section(self, parent_layout):
        """NEW: Create Rodent IV personality settings section"""
        group = QGroupBox("Rodent IV Personality Settings")
        group.setObjectName("settings_group")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Enable Rodent personalities checkbox
        self.rodent_personalities_cb = QCheckBox("Enable Rodent IV Personalities")
        self.rodent_personalities_cb.setStyleSheet("font-weight: bold; color: #9C27B0;")
        self.rodent_personalities_cb.setToolTip("Enable personality-based playing styles for Rodent IV engine")
        self.rodent_personalities_cb.toggled.connect(self.on_rodent_personalities_changed)
        layout.addWidget(self.rodent_personalities_cb)
        
        # Personality selection frame (only visible when enabled)
        self.rodent_config_frame = QFrame()
        self.rodent_config_frame.setVisible(False)
        config_layout = QVBoxLayout(self.rodent_config_frame)
        config_layout.setContentsMargins(20, 10, 20, 10)
        config_layout.setSpacing(15)
        
        # Personality selection
        personality_layout = QHBoxLayout()
        personality_layout.addWidget(QLabel("Personality:"))
        
        self.personality_combo = QComboBox()
        self.personality_combo.setToolTip("Select a personality file for Rodent IV")
        self.personality_combo.currentTextChanged.connect(self.on_personality_changed)
        personality_layout.addWidget(self.personality_combo)
        personality_layout.addStretch()
        
        config_layout.addLayout(personality_layout)
        
        # UCI Options Display Area - integrated into main layout
        options_label = QLabel("Personality UCI Options:")
        config_layout.addWidget(options_label)
        
        # UCI options widget - directly in the layout, no separate scroll area
        self.uci_options_widget = QFrame()
        self.uci_options_widget.setStyleSheet("""
            QFrame {
                border: 1px solid #666;
                border-radius: 4px;
                padding: 10px;
                font-family: Arial;
            }
            QFrame * {
                font-family: Arial;
            }
            QLabel {
                font-family: Arial;
            }
        """)
        self.uci_options_layout = QGridLayout(self.uci_options_widget)
        self.uci_options_layout.setSpacing(8)
        self.uci_options_layout.setContentsMargins(10, 10, 10, 10)
        
        # Initially empty
        no_options_label = QLabel("No personality selected")
        no_options_label.setStyleSheet("color: #888; font-style: italic;")
        no_options_label.setAlignment(Qt.AlignCenter)
        self.uci_options_layout.addWidget(no_options_label, 0, 0, 1, 2)
        
        config_layout.addWidget(self.uci_options_widget)
        
        layout.addWidget(self.rodent_config_frame)
        
        # Store references for later use
        self.rodent_group = group
        parent_layout.addWidget(group)
        
        # Initially populate personalities
        self._populate_personalities()
    
    def _populate_personalities(self):
        """Populate the personality dropdown with available files"""
        try:
            personalities = self.settings_manager.get_available_personalities()
            self.personality_combo.clear()
            
            if personalities:
                for personality in personalities:
                    display_name = self.settings_manager.get_personality_display_name(personality)
                    self.personality_combo.addItem(display_name, personality)  # Store filename as data
            else:
                self.personality_combo.addItem("No personalities found")
                self.personality_combo.setEnabled(False)
                
        except Exception as e:
            print(f"Error populating personalities: {e}")
            self.personality_combo.addItem("Error loading personalities")
            self.personality_combo.setEnabled(False)
    
    def _update_uci_options_display(self, personality_file: str):
        """Update the UCI options display for the selected personality"""
        try:
            # Clear existing options
            for i in reversed(range(self.uci_options_layout.count())):
                child = self.uci_options_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            if not personality_file:
                no_selection_label = QLabel("No personality selected")
                no_selection_label.setStyleSheet("color: #888; font-style: italic;")
                no_selection_label.setAlignment(Qt.AlignCenter)
                self.uci_options_layout.addWidget(no_selection_label, 0, 0, 1, 2)
                return
            
            # Parse personality file
            uci_options = self.settings_manager.parse_personality_file(personality_file)
            
            if not uci_options:
                no_options_label = QLabel("No UCI options found in personality file")
                no_options_label.setStyleSheet("color: #ff6600; font-style: italic;")
                no_options_label.setAlignment(Qt.AlignCenter)
                self.uci_options_layout.addWidget(no_options_label, 0, 0, 1, 2)
                return
            
            # Display UCI options in a grid
            row = 0
            for option_name, option_value in sorted(uci_options.items()):
                # Option name label
                name_label = QLabel(f"{option_name}:")
                name_label.setStyleSheet("font-weight: bold;")
                name_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.uci_options_layout.addWidget(name_label, row, 0)
                
                # Option value label
                value_label = QLabel(str(option_value))
                value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                value_label.setWordWrap(True)
                self.uci_options_layout.addWidget(value_label, row, 1)
                
                row += 1
            
            # Add stretch to push options to top
            spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
            self.uci_options_layout.addItem(spacer, row, 0, 1, 2)
            
            print(f"Displayed {len(uci_options)} UCI options for personality: {personality_file}")
            
        except Exception as e:
            print(f"Error updating UCI options display: {e}")
            error_label = QLabel(f"Error parsing personality file: {str(e)}")
            error_label.setStyleSheet("color: #ff0000; font-style: italic;")
            error_label.setWordWrap(True)
            self.uci_options_layout.addWidget(error_label, 0, 0, 1, 2)
    
    def create_info_section(self, parent_layout):
        """Create enhanced info section"""
        info_label = QLabel(
            "<b>Intelligence Features:</b><br>"
            "• <b>Disable Intelligence:</b> Completely turns off all intelligence, using pure engine moves<br>"
            "• <b>Avoid Low Intelligence:</b> Falls back to engine moves when intelligent evaluation is too low<br>"
            "• <b>Move Multipliers:</b> Modify engine move preferences through sophisticated multipliers<br>"
            "• <b>Piece Preferences:</b> Boost or penalize moves by specific piece types<br>"
            "• <b>Emotional Behavior:</b> Add human-like behavioral patterns to move selection<br>"
            + ("• <b>Rodent IV Personalities:</b> Load chess player personalities that modify engine behavior<br>" if self.rodent_available else "") +
            "<br>"
            "All settings are automatically saved when changed and persist between sessions. "
            "Visual indicators in the game show which system (engine vs intelligence) selected each move."
        )
        info_label.setWordWrap(True)
        info_label.setContentsMargins(10, 10, 10, 10)
        info_label.setStyleSheet("QLabel { background-color: #000000; padding: 10px; border-radius: 5px; }")
        parent_layout.addWidget(info_label)
    
    def save_setting(self, key, value):
        """Save setting reliably with error handling"""
        try:
            self.settings_manager.update_intelligence_setting(key, value)
            # Force save to disk if method exists
            if hasattr(self.settings_manager, 'save'):
                self.settings_manager.save()
            elif hasattr(self.settings_manager, 'save_settings'):
                self.settings_manager.save_settings()
            self.settings_changed.emit()
        except Exception as e:
            print(f"Error saving setting {key}: {e}")
    
    def toggle_intelligence(self):
        """NEW: Enhanced intelligence toggle with proper state management"""
        self.intelligence_enabled = not self.intelligence_enabled
        
        # Update button appearance and text
        if self.intelligence_enabled:
            self.intelligence_toggle_btn.setText("Disable Intelligence")
            self.intelligence_toggle_btn.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    padding: 8px 16px;
                    background-color: #4CAF50;
                    color: white;
                }
            """)
        else:
            self.intelligence_toggle_btn.setText("Enable Intelligence")
            self.intelligence_toggle_btn.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    padding: 8px 16px;
                    background-color: #f44336;
                    color: white;
                }
            """)
        
        # Show/hide the intelligence settings sections
        self.content_widget.setVisible(self.intelligence_enabled)
        
        # Enable/disable the avoid low intelligence controls
        self.update_avoid_controls_state()
        
        # Save the intelligence enabled state
        self.save_setting('intelligence_enabled', self.intelligence_enabled)
    
    def update_avoid_controls_state(self):
        """Update the enabled state of avoid low intelligence controls"""
        # Avoid controls are only available when intelligence is enabled
        avoid_enabled = self.intelligence_enabled and self.avoid_low_intelligence_cb.isChecked()
        
        self.avoid_low_intelligence_cb.setEnabled(self.intelligence_enabled)
        self.threshold_spinbox.setEnabled(avoid_enabled)
        self.threshold_label.setEnabled(avoid_enabled)
        self.threshold_desc.setEnabled(avoid_enabled)
    
    # NEW: Event handlers for new intelligence control features
    def on_avoid_low_intelligence_changed(self, checked):
        """Handle avoid low intelligence checkbox change"""
        self.save_setting('avoid_low_intelligence', checked)
        self.update_avoid_controls_state()
    
    def on_threshold_changed(self, value):
        """Handle threshold spinbox change"""
        # Clamp value to valid range (-3.0 to -1.0)
        clamped_value = max(-3.0, min(-1.0, value))
        if clamped_value != value:
            self.threshold_spinbox.setValue(clamped_value)
            return
        
        self.save_setting('low_intelligence_threshold', value)
    
    # NEW: Rodent IV personality event handlers
    def on_rodent_personalities_changed(self, checked):
        """Handle Rodent personalities enable/disable"""
        try:
            self.settings_manager.set_rodent_personalities_enabled(checked)
            self.rodent_config_frame.setVisible(checked)
            
            if checked:
                # Load current personality if any
                current_personality = self.settings_manager.get_selected_rodent_personality()
                self._select_personality_in_combo(current_personality)
            else:
                # Clear UCI options display when disabled
                self._update_uci_options_display("")
            
            print(f"Rodent IV personalities {'enabled' if checked else 'disabled'}")
            
        except Exception as e:
            print(f"Error toggling Rodent personalities: {e}")
    
    def on_personality_changed(self, display_name):
        """Handle personality selection change"""
        try:
            # Get the actual filename from combo box data
            current_index = self.personality_combo.currentIndex()
            if current_index >= 0:
                personality_file = self.personality_combo.itemData(current_index)
                if personality_file:
                    self.settings_manager.set_selected_rodent_personality(personality_file)
                    self._update_uci_options_display(personality_file)
                    print(f"Selected Rodent personality: {personality_file}")
                else:
                    self._update_uci_options_display("")
        except Exception as e:
            print(f"Error changing personality: {e}")
    
    def _select_personality_in_combo(self, personality_file):
        """Select a personality in the combo box by filename"""
        for i in range(self.personality_combo.count()):
            if self.personality_combo.itemData(i) == personality_file:
                self.personality_combo.setCurrentIndex(i)
                self._update_uci_options_display(personality_file)
                break
    
    # Existing event handlers - simplified and reliable
    def on_aggressiveness_changed(self, value):
        multiplier = value / 100.0
        self.aggressiveness_display.setText(f"{multiplier:.2f}")
        self.save_setting('aggressiveness_contempt', multiplier)
    
    def on_passiveness_changed(self, value):
        multiplier = value / 100.0
        self.passiveness_display.setText(f"{multiplier:.2f}")
        self.save_setting('passiveness_contempt', multiplier)
    
    def on_trading_changed(self, value):
        self.save_setting('trading_preference', value)
    
    def on_capture_changed(self, value):
        multiplier = value / 100.0
        self.capture_display.setText(f"{multiplier:.2f}")
        self.save_setting('capture_preference', multiplier)
    
    def on_castle_changed(self, value):
        multiplier = value / 100.0
        self.castle_display.setText(f"{multiplier:.2f}")
        self.save_setting('castle_preference', multiplier)
    
    def on_en_passant_changed(self, value):
        multiplier = value / 100.0
        self.en_passant_display.setText(f"{multiplier:.2f}")
        self.save_setting('en_passant_preference', multiplier)
    
    def on_promotion_changed(self, value):
        multiplier = value / 100.0
        self.promotion_display.setText(f"{multiplier:.2f}")
        self.save_setting('promotion_preference', multiplier)
    
    def on_early_castling_changed(self, checked):
        self.save_setting('prefer_early_castling', checked)
    
    def on_pins_changed(self, checked):
        self.save_setting('prefer_pins', checked)
    
    def on_castle_side_enabled_changed(self, checked):
        self.castle_buttons_widget.setVisible(checked)
        self.save_setting('prefer_side_castle', checked)
        if not checked:
            # Clear selection when disabled
            self.castle_side_group.setExclusive(False)
            self.kingside_btn.setChecked(False)
            self.queenside_btn.setChecked(False)
            self.castle_side_group.setExclusive(True)
            self.save_setting('castle_side', None)
            self.update_castle_button_styles()
    
    def on_castle_side_changed(self):
        if self.kingside_btn.isChecked():
            castle_side = "kingside"
        elif self.queenside_btn.isChecked():
            castle_side = "queenside"
        else:
            castle_side = None
        
        self.save_setting('castle_side', castle_side)
        self.update_castle_button_styles()
    
    def update_castle_button_styles(self):
        """Update button styles to clearly show selection"""
        # Reset styles
        self.kingside_btn.setStyleSheet("")
        self.queenside_btn.setStyleSheet("")
        
        # Highlight selected button
        if self.kingside_btn.isChecked():
            self.kingside_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                    border: 2px solid #45a049;
                }
            """)
        elif self.queenside_btn.isChecked():
            self.queenside_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    font-weight: bold;
                    border: 2px solid #1976D2;
                }
            """)
    
    def on_piece_changed(self, piece_key, value):
        multiplier = value / 100.0
        if piece_key in self.piece_displays:
            self.piece_displays[piece_key].setText(f"{multiplier:.2f}")
        self.save_setting(f'{piece_key}_preference', multiplier)
    
    def on_stalemate_changed(self, value):
        self.stalemate_display.setText(f"{value}%")
        self.save_setting('stalemate_probability', value / 100.0)
    
    def on_stay_equal_changed(self, checked):
        self.save_setting('stay_equal', checked)
    
    def on_promote_queen_changed(self, checked):
        self.save_setting('always_promote_queen', checked)
    
    def on_checkmate_changed(self, checked):
        self.save_setting('checkmate_immediately', checked)
    
    def update_auto_move_status(self, auto_move_enabled: bool):
        """Handle auto-move status updates"""
        pass  # Placeholder for compatibility
    
    def load_settings(self):
        """NEW: Enhanced settings loading with new intelligence controls and Rodent IV"""
        try:
            intel_settings = self.settings_manager.get_intelligence_settings()
            
            # Load intelligence enabled state
            self.intelligence_enabled = getattr(intel_settings, 'intelligence_enabled', True)
            self.content_widget.setVisible(self.intelligence_enabled)
            
            if self.intelligence_enabled:
                self.intelligence_toggle_btn.setText("Disable Intelligence")
                self.intelligence_toggle_btn.setStyleSheet("""
                    QPushButton {
                        font-weight: bold;
                        padding: 8px 16px;
                        background-color: #4CAF50;
                        color: white;
                    }
                """)
            else:
                self.intelligence_toggle_btn.setText("Enable Intelligence")
                self.intelligence_toggle_btn.setStyleSheet("""
                    QPushButton {
                        font-weight: bold;
                        padding: 8px 16px;
                        background-color: #f44336;
                        color: white;
                    }
                """)
            
            # NEW: Load avoid low intelligence settings
            avoid_low_intelligence = getattr(intel_settings, 'avoid_low_intelligence', False)
            self.avoid_low_intelligence_cb.setChecked(avoid_low_intelligence)
            
            low_intelligence_threshold = getattr(intel_settings, 'low_intelligence_threshold', -1.5)
            # Ensure threshold is within valid range
            low_intelligence_threshold = max(-3.0, min(-1.0, low_intelligence_threshold))
            self.threshold_spinbox.setValue(low_intelligence_threshold)
            
            # Update control states
            self.update_avoid_controls_state()
            
            # Load multiplier settings
            self.aggressiveness_slider.setValue(int(getattr(intel_settings, 'aggressiveness_contempt', 1.0) * 100))
            self.passiveness_slider.setValue(int(getattr(intel_settings, 'passiveness_contempt', 1.0) * 100))
            self.trading_spin.setValue(getattr(intel_settings, 'trading_preference', 0.0))
            self.capture_slider.setValue(int(getattr(intel_settings, 'capture_preference', 1.0) * 100))
            self.castle_slider.setValue(int(getattr(intel_settings, 'castle_preference', 1.0) * 100))
            self.en_passant_slider.setValue(int(getattr(intel_settings, 'en_passant_preference', 1.0) * 100))
            self.promotion_slider.setValue(int(getattr(intel_settings, 'promotion_preference', 1.0) * 100))
            
            # Load checkbox settings
            self.early_castling_cb.setChecked(getattr(intel_settings, 'prefer_early_castling', False))
            self.prefer_pins_cb.setChecked(getattr(intel_settings, 'prefer_pins', False))
            
            # Load castle side settings
            prefer_side_castle = getattr(intel_settings, 'prefer_side_castle', False)
            self.castle_side_cb.setChecked(prefer_side_castle)
            self.castle_buttons_widget.setVisible(prefer_side_castle)
            
            castle_side = getattr(intel_settings, 'castle_side', None)
            if castle_side == "kingside":
                self.kingside_btn.setChecked(True)
            elif castle_side == "queenside":
                self.queenside_btn.setChecked(True)
            
            # Load piece preferences
            for piece_key in self.piece_sliders:
                value = getattr(intel_settings, f'{piece_key}_preference', 1.0)
                self.piece_sliders[piece_key].setValue(int(value * 100))
            
            # Load emotion settings
            self.stalemate_slider.setValue(int(getattr(intel_settings, 'stalemate_probability', 0.0) * 100))
            self.stay_equal_cb.setChecked(getattr(intel_settings, 'stay_equal', False))
            self.promote_queen_cb.setChecked(getattr(intel_settings, 'always_promote_queen', False))
            self.checkmate_immediately_cb.setChecked(getattr(intel_settings, 'checkmate_immediately', False))
            
            # NEW: Load Rodent IV personality settings
            if self.rodent_available:
                rodent_enabled = self.settings_manager.is_rodent_personalities_enabled()
                self.rodent_personalities_cb.setChecked(rodent_enabled)
                self.rodent_config_frame.setVisible(rodent_enabled)
                
                if rodent_enabled:
                    current_personality = self.settings_manager.get_selected_rodent_personality()
                    self._select_personality_in_combo(current_personality)
            
            # Update all displays
            self.update_all_displays()
            
        except Exception as e:
            print(f"Error loading intelligence settings: {e}")
    
    def update_all_displays(self):
        """Update all display labels"""
        self.aggressiveness_display.setText(f"{self.aggressiveness_slider.value() / 100.0:.2f}")
        self.passiveness_display.setText(f"{self.passiveness_slider.value() / 100.0:.2f}")
        self.capture_display.setText(f"{self.capture_slider.value() / 100.0:.2f}")
        self.castle_display.setText(f"{self.castle_slider.value() / 100.0:.2f}")
        self.en_passant_display.setText(f"{self.en_passant_slider.value() / 100.0:.2f}")
        self.promotion_display.setText(f"{self.promotion_slider.value() / 100.0:.2f}")
        self.stalemate_display.setText(f"{self.stalemate_slider.value()}%")
        
        for piece_key, display in self.piece_displays.items():
            display.setText(f"{self.piece_sliders[piece_key].value() / 100.0:.2f}")
        
        self.update_castle_button_styles()