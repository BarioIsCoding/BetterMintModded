"""
Visual settings tab for BetterMint Modded GUI
Configuration for visual features and audio feedback
ENHANCED: Functional Text-to-Speech integration with pyttsx3
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QGroupBox, 
    QLabel, QSlider, QSpinBox, QPushButton, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt, QTimer

from settings import SettingsManager

# Check TTS availability
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False


class VisualSettingsTab(QWidget):
    """Tab for visual and audio settings configuration"""
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.tts_engine = None
        self.tts_test_timer = QTimer()
        self.tts_test_timer.setSingleShot(True)
        self.tts_test_timer.timeout.connect(self._stop_tts_test)
        
        self.setup_ui()
        self._initialize_tts()
    
    def setup_ui(self):
        """Setup the Visual Settings tab UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Visual Features Group
        visual_group = QGroupBox("Visual Features")
        visual_group.setObjectName("settings_group")
        visual_layout = QVBoxLayout(visual_group)

        # Show hints
        self.hints_checkbox = QCheckBox("Show Move Hints (Analysis Arrows)")
        self.hints_checkbox.setToolTip("Display colored arrows showing the best moves from engine analysis")
        self.hints_checkbox.setChecked(self.settings_manager.get_setting("show-hints", True))
        self.hints_checkbox.toggled.connect(self._on_hints_changed)
        visual_layout.addWidget(self.hints_checkbox)

        # Move analysis
        self.analysis_checkbox = QCheckBox("Post-Move Analysis Badges")
        self.analysis_checkbox.setToolTip("Show quality badges after moves are played (Best Move, Good, Mistake, etc.)")
        self.analysis_checkbox.setChecked(self.settings_manager.get_setting("move-analysis", True))
        self.analysis_checkbox.toggled.connect(self._on_analysis_changed)
        visual_layout.addWidget(self.analysis_checkbox)

        # Depth bar
        self.depth_bar_checkbox = QCheckBox("Analysis Depth Progress Bar")
        self.depth_bar_checkbox.setToolTip("Show progress bar indicating how deep the engine is analyzing")
        self.depth_bar_checkbox.setChecked(self.settings_manager.get_setting("depth-bar", True))
        self.depth_bar_checkbox.toggled.connect(self._on_depth_bar_changed)
        visual_layout.addWidget(self.depth_bar_checkbox)

        # Evaluation bar
        self.eval_bar_checkbox = QCheckBox("Position Evaluation Bar")
        self.eval_bar_checkbox.setToolTip("Show bar indicating who has the advantage and by how much")
        self.eval_bar_checkbox.setChecked(self.settings_manager.get_setting("evaluation-bar", True))
        self.eval_bar_checkbox.toggled.connect(self._on_eval_bar_changed)
        visual_layout.addWidget(self.eval_bar_checkbox)

        layout.addWidget(visual_group)

        # Audio Features Group
        audio_group = QGroupBox("Audio Features")
        audio_group.setObjectName("settings_group")
        audio_layout = QVBoxLayout(audio_group)

        # TTS availability status
        if not TTS_AVAILABLE:
            tts_warning = QLabel("⚠ Text-to-Speech not available. Install with: pip install pyttsx3")
            tts_warning.setStyleSheet("color: #ff6600; font-weight: bold;")
            audio_layout.addWidget(tts_warning)
            print("Please install TTS. pip install pyttsx3")

        ## Text to speech main toggle
        tts_layout = QHBoxLayout()
        self.tts_checkbox = QCheckBox("Text-to-Speech Move Announcements (Please do not use this, buggy)")
        self.tts_checkbox.setToolTip("Announce moves using computer voice (e.g., 'rook from a1 to a8')")
        self.tts_checkbox.setChecked(self.settings_manager.get_setting("text-to-speech", False))
        self.tts_checkbox.setEnabled(TTS_AVAILABLE)
        self.tts_checkbox.toggled.connect(self._on_tts_changed)
        tts_layout.addWidget(self.tts_checkbox)
        
        # Test TTS button
        self.tts_test_button = QPushButton("Test Voice")
        self.tts_test_button.setToolTip("Test the text-to-speech voice with a sample move")
        self.tts_test_button.setEnabled(TTS_AVAILABLE)
        self.tts_test_button.clicked.connect(self._test_tts)
        self.tts_test_button.setMaximumWidth(100)
        tts_layout.addWidget(self.tts_test_button)
        tts_layout.addStretch()
        
        audio_layout.addLayout(tts_layout)

        # TTS Settings (only if available)
        if TTS_AVAILABLE:
            # Voice selection
            voice_layout = QHBoxLayout()
            voice_layout.addWidget(QLabel("Voice:"))
            
            self.voice_combo = QComboBox()
            self.voice_combo.setToolTip("Select the voice for text-to-speech")
            self._populate_voices()
            self.voice_combo.currentTextChanged.connect(self._on_voice_changed)
            voice_layout.addWidget(self.voice_combo)
            voice_layout.addStretch()
            
            audio_layout.addLayout(voice_layout)

            # Speech rate
            rate_layout = QHBoxLayout()
            rate_layout.addWidget(QLabel("Speech Rate:"))
            
            self.rate_slider = QSlider(Qt.Horizontal)
            self.rate_slider.setMinimum(50)
            self.rate_slider.setMaximum(300)
            self.rate_slider.setValue(self.settings_manager.get_setting("tts-rate", 150))
            self.rate_slider.setToolTip("Adjust how fast the voice speaks (50-300 words per minute)")
            self.rate_slider.valueChanged.connect(self._on_rate_changed)
            rate_layout.addWidget(self.rate_slider)
            
            self.rate_label = QLabel(f"{self.rate_slider.value()} WPM")
            self.rate_label.setMinimumWidth(60)
            rate_layout.addWidget(self.rate_label)
            
            audio_layout.addLayout(rate_layout)

            # Volume
            volume_layout = QHBoxLayout()
            volume_layout.addWidget(QLabel("Volume:"))
            
            self.volume_slider = QSlider(Qt.Horizontal)
            self.volume_slider.setMinimum(0)
            self.volume_slider.setMaximum(100)
            self.volume_slider.setValue(int(self.settings_manager.get_setting("tts-volume", 0.8) * 100))
            self.volume_slider.setToolTip("Adjust the voice volume (0-100%)")
            self.volume_slider.valueChanged.connect(self._on_volume_changed)
            volume_layout.addWidget(self.volume_slider)
            
            self.volume_label = QLabel(f"{self.volume_slider.value()}%")
            self.volume_label.setMinimumWidth(40)
            volume_layout.addWidget(self.volume_label)
            
            audio_layout.addLayout(volume_layout)

            # TTS Options
            self.tts_announce_player_moves = QCheckBox("Announce Player Moves")
            self.tts_announce_player_moves.setToolTip("Announce moves that the player makes")
            self.tts_announce_player_moves.setChecked(self.settings_manager.get_setting("tts-announce-player", True))
            self.tts_announce_player_moves.toggled.connect(self._on_announce_player_changed)
            audio_layout.addWidget(self.tts_announce_player_moves)

            self.tts_announce_engine_moves = QCheckBox("Announce Engine Moves")
            self.tts_announce_engine_moves.setToolTip("Announce moves that the engine suggests or plays")
            self.tts_announce_engine_moves.setChecked(self.settings_manager.get_setting("tts-announce-engine", True))
            self.tts_announce_engine_moves.toggled.connect(self._on_announce_engine_changed)
            audio_layout.addWidget(self.tts_announce_engine_moves)

        layout.addWidget(audio_group)
        layout.addStretch()

        # Update TTS controls availability
        self._update_tts_controls()
    
    def _initialize_tts(self):
        """Initialize TTS engine for testing"""
        if not TTS_AVAILABLE:
            return
        
        try:
            self.tts_engine = pyttsx3.init()
            
            # Apply saved settings
            if self.tts_engine:
                rate = self.settings_manager.get_setting("tts-rate", 150)
                volume = self.settings_manager.get_setting("tts-volume", 0.8)
                
                self.tts_engine.setProperty('rate', rate)
                self.tts_engine.setProperty('volume', volume)
                
                # Set voice if saved
                saved_voice = self.settings_manager.get_setting("tts-voice", "")
                if saved_voice:
                    voices = self.tts_engine.getProperty('voices')
                    for voice in voices:
                        if voice.name == saved_voice:
                            self.tts_engine.setProperty('voice', voice.id)
                            break
                
                print("TTS engine initialized successfully")
        except Exception as e:
            print(f"TTS initialization failed: {e}")
            self.tts_engine = None
    
    def _populate_voices(self):
        """Populate voice selection combo box"""
        if not self.tts_engine:
            return
        
        try:
            voices = self.tts_engine.getProperty('voices')
            saved_voice = self.settings_manager.get_setting("tts-voice", "")
            
            for voice in voices:
                if voice.name:
                    self.voice_combo.addItem(voice.name)
                    if voice.name == saved_voice:
                        self.voice_combo.setCurrentText(voice.name)
            
            # If no saved voice, prefer male voices for chess
            if not saved_voice and voices:
                for voice in voices:
                    if voice.gender and 'male' in voice.gender.lower():
                        self.voice_combo.setCurrentText(voice.name)
                        self._on_voice_changed(voice.name)
                        break
        except Exception as e:
            print(f"Failed to populate voices: {e}")
    
    def _update_tts_controls(self):
        """Update TTS control availability based on main toggle"""
        tts_enabled = self.tts_checkbox.isChecked() and TTS_AVAILABLE
        
        if hasattr(self, 'voice_combo'):
            self.voice_combo.setEnabled(tts_enabled)
        if hasattr(self, 'rate_slider'):
            self.rate_slider.setEnabled(tts_enabled)
        if hasattr(self, 'volume_slider'):
            self.volume_slider.setEnabled(tts_enabled)
        if hasattr(self, 'tts_announce_player_moves'):
            self.tts_announce_player_moves.setEnabled(tts_enabled)
        if hasattr(self, 'tts_announce_engine_moves'):
            self.tts_announce_engine_moves.setEnabled(tts_enabled)
        
        self.tts_test_button.setEnabled(tts_enabled)
    
    # Event handlers for visual settings
    def _on_hints_changed(self, checked):
        """Handle hints checkbox change"""
        self.settings_manager.set_setting("show-hints", checked)
        print(f"Move hints {'enabled' if checked else 'disabled'}")
    
    def _on_analysis_changed(self, checked):
        """Handle move analysis checkbox change"""
        self.settings_manager.set_setting("move-analysis", checked)
        print(f"Move analysis badges {'enabled' if checked else 'disabled'}")
    
    def _on_depth_bar_changed(self, checked):
        """Handle depth bar checkbox change"""
        self.settings_manager.set_setting("depth-bar", checked)
        print(f"Depth progress bar {'enabled' if checked else 'disabled'}")
    
    def _on_eval_bar_changed(self, checked):
        """Handle evaluation bar checkbox change"""
        self.settings_manager.set_setting("evaluation-bar", checked)
        print(f"Evaluation bar {'enabled' if checked else 'disabled'}")
    
    # Event handlers for TTS settings
    def _on_tts_changed(self, checked):
        """Handle TTS checkbox change"""
        self.settings_manager.set_setting("text-to-speech", checked)
        self._update_tts_controls()
        print(f"Text-to-speech {'enabled' if checked else 'disabled'}")
        
        if checked and not TTS_AVAILABLE:
            QMessageBox.warning(
                self,
                "TTS Unavailable",
                "Text-to-speech is not available. Please install pyttsx3:\n\npip install pyttsx3"
            )
            self.tts_checkbox.setChecked(False)
    
    def _on_voice_changed(self, voice_name):
        """Handle voice selection change"""
        if not self.tts_engine or not voice_name:
            return
        
        try:
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if voice.name == voice_name:
                    self.tts_engine.setProperty('voice', voice.id)
                    self.settings_manager.set_setting("tts-voice", voice_name)
                    print(f"TTS voice changed to: {voice_name}")
                    break
        except Exception as e:
            print(f"Failed to change voice: {e}")
    
    def _on_rate_changed(self, value):
        """Handle speech rate change"""
        if self.tts_engine:
            self.tts_engine.setProperty('rate', value)
        self.settings_manager.set_setting("tts-rate", value)
        self.rate_label.setText(f"{value} WPM")
    
    def _on_volume_changed(self, value):
        """Handle volume change"""
        volume = value / 100.0
        if self.tts_engine:
            self.tts_engine.setProperty('volume', volume)
        self.settings_manager.set_setting("tts-volume", volume)
        self.volume_label.setText(f"{value}%")
    
    def _on_announce_player_changed(self, checked):
        """Handle announce player moves setting"""
        self.settings_manager.set_setting("tts-announce-player", checked)
        print(f"Announce player moves {'enabled' if checked else 'disabled'}")
    
    def _on_announce_engine_changed(self, checked):
        """Handle announce engine moves setting"""
        self.settings_manager.set_setting("tts-announce-engine", checked)
        print(f"Announce engine moves {'enabled' if checked else 'disabled'}")
    
    def _test_tts(self):
        """Test TTS with a sample move"""
        if not self.tts_engine:
            QMessageBox.warning(self, "TTS Error", "Text-to-speech engine not available")
            return
        
        try:
            # Disable test button during test
            self.tts_test_button.setEnabled(False)
            self.tts_test_button.setText("Testing...")
            
            # Test with a sample chess move
            test_phrases = [
                "Knight from g1 to f3",
                "Pawn from e2 to e4", 
                "Queen from d1 to h5, check",
                "Rook from a1 captures pawn on a7"
            ]
            
            import random
            test_phrase = random.choice(test_phrases)
            
            # Speak the test phrase
            self.tts_engine.say(test_phrase)
            self.tts_engine.runAndWait()
            
            print(f"TTS test completed: {test_phrase}")
            
            # Start timer to re-enable button
            self.tts_test_timer.start(1000)
            
        except Exception as e:
            QMessageBox.critical(self, "TTS Error", f"Text-to-speech test failed:\n{str(e)}")
            self._stop_tts_test()
    
    def _stop_tts_test(self):
        """Re-enable test button after test"""
        self.tts_test_button.setEnabled(True)
        self.tts_test_button.setText("Test Voice")
    
    def load_settings(self):
        """Reload settings from settings manager with error handling"""
        try:
            # Visual settings
            self.hints_checkbox.setChecked(self.settings_manager.get_setting("show-hints", True))
            self.analysis_checkbox.setChecked(self.settings_manager.get_setting("move-analysis", True))
            self.depth_bar_checkbox.setChecked(self.settings_manager.get_setting("depth-bar", True))
            self.eval_bar_checkbox.setChecked(self.settings_manager.get_setting("evaluation-bar", True))
            
            # Audio settings
            self.tts_checkbox.setChecked(self.settings_manager.get_setting("text-to-speech", False))
            
            if TTS_AVAILABLE and hasattr(self, 'rate_slider'):
                self.rate_slider.setValue(self.settings_manager.get_setting("tts-rate", 150))
                self.rate_label.setText(f"{self.rate_slider.value()} WPM")
                
                volume_percent = int(self.settings_manager.get_setting("tts-volume", 0.8) * 100)
                self.volume_slider.setValue(volume_percent)
                self.volume_label.setText(f"{volume_percent}%")
                
                self.tts_announce_player_moves.setChecked(self.settings_manager.get_setting("tts-announce-player", True))
                self.tts_announce_engine_moves.setChecked(self.settings_manager.get_setting("tts-announce-engine", True))
                
                # Reload voice selection
                saved_voice = self.settings_manager.get_setting("tts-voice", "")
                if saved_voice:
                    index = self.voice_combo.findText(saved_voice)
                    if index >= 0:
                        self.voice_combo.setCurrentIndex(index)
            
            self._update_tts_controls()
            print("Visual and audio settings loaded successfully")
            
        except Exception as e:
            print(f"Error loading visual settings: {e}")
            QMessageBox.warning(self, "Settings Error", f"Failed to load some settings: {str(e)}")
    
    def save_settings(self):
        """Save current settings (called when tab is about to close)"""
        try:
            # Settings are automatically saved through event handlers
            # This method is for any final cleanup if needed
            print("Visual and audio settings saved")
        except Exception as e:
            print(f"Error saving visual settings: {e}")
    
    def closeEvent(self, event):
        """Handle tab close event"""
        try:
            if self.tts_engine:
                # Stop any ongoing speech
                self.tts_engine.stop()
            self.save_settings()
        except Exception as e:
            print(f"Error during visual settings tab close: {e}")
        finally:
            event.accept()