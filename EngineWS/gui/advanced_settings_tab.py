"""
Advanced settings tab for BetterMint Modded GUI
Configuration for performance monitoring, notifications, and debug features
"""

import os
import glob
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, 
    QGroupBox, QGridLayout, QComboBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Signal

from settings import SettingsManager


class AdvancedSettingsTab(QWidget):
    """Tab for advanced settings and system configuration"""
    
    performance_monitoring_changed = Signal(bool)
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the Advanced Settings tab UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Performance Settings
        perf_group = QGroupBox("Performance & Monitoring")
        perf_group.setObjectName("settings_group")
        perf_layout = QVBoxLayout(perf_group)

        # Performance monitoring
        self.perf_monitor_checkbox = QCheckBox("Enable Performance Monitoring")
        self.perf_monitor_checkbox.setChecked(self.settings_manager.get_setting("performance-monitoring"))
        self.perf_monitor_checkbox.toggled.connect(self.on_performance_monitoring_changed)
        perf_layout.addWidget(self.perf_monitor_checkbox)

        # Auto-save settings
        self.autosave_checkbox = QCheckBox("Auto-Save Settings")
        self.autosave_checkbox.setChecked(self.settings_manager.get_setting("auto-save-settings"))
        self.autosave_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("auto-save-settings", x))
        perf_layout.addWidget(self.autosave_checkbox)

        layout.addWidget(perf_group)

        # Notification Settings
        notif_group = QGroupBox("Notifications")
        notif_group.setObjectName("settings_group")
        notif_layout = QGridLayout(notif_group)

        notif_layout.addWidget(QLabel("Notification Level:"), 0, 0)
        self.notif_combo = QComboBox()
        self.notif_combo.addItems(["Minimal", "Normal", "Verbose"])
        current_level = self.settings_manager.get_setting("notification-level", "normal")
        self.notif_combo.setCurrentText(current_level.title())
        self.notif_combo.currentTextChanged.connect(lambda x: self.settings_manager.set_setting("notification-level", x.lower()))
        notif_layout.addWidget(self.notif_combo, 0, 1)

        layout.addWidget(notif_group)

        # Debug Settings
        debug_group = QGroupBox("Debug & Development")
        debug_group.setObjectName("settings_group")
        debug_layout = QVBoxLayout(debug_group)

        # Buttons for debug functions
        debug_buttons_layout = QHBoxLayout()

        clear_cache_btn = QPushButton("Clear Cache")
        clear_cache_btn.clicked.connect(self.clear_cache)
        debug_buttons_layout.addWidget(clear_cache_btn)

        reset_settings_btn = QPushButton("Reset to Defaults")
        reset_settings_btn.clicked.connect(self.reset_to_defaults)
        debug_buttons_layout.addWidget(reset_settings_btn)

        debug_layout.addLayout(debug_buttons_layout)
        layout.addWidget(debug_group)

        layout.addStretch()
    
    def on_performance_monitoring_changed(self, checked):
        """Handle performance monitoring toggle with signal emission"""
        try:
            self.settings_manager.set_setting("performance-monitoring", checked)
            self.performance_monitoring_changed.emit(checked)
        except Exception as e:
            print(f"Error toggling performance monitoring: {e}")
    
    def clear_cache(self):
        """Clear cache files with error handling"""
        try:
            cache_files = glob.glob("*.cache") + glob.glob("*.tmp")
            removed_count = 0
            for file in cache_files:
                try:
                    os.remove(file)
                    removed_count += 1
                except Exception as e:
                    print(f"Failed to remove cache file {file}: {e}")
            
            QMessageBox.information(
                self, 
                "Success", 
                f"Cache cleared successfully! Removed {removed_count} files."
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to clear cache: {str(e)}")
    
    def reset_to_defaults(self):
        """Reset settings to defaults with confirmation"""
        try:
            reply = QMessageBox.question(
                self, 
                "Reset Settings",
                "Are you sure you want to reset all settings to defaults?\n\n"
                "This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.settings_manager.reset_to_defaults()
                # Reload the current tab's UI to reflect changes
                self.load_settings()
                QMessageBox.information(self, "Success", "Settings reset to defaults!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reset settings: {str(e)}")
    
    def load_settings(self):
        """Reload settings from settings manager with error handling"""
        try:
            self.perf_monitor_checkbox.setChecked(self.settings_manager.get_setting("performance-monitoring"))
            self.autosave_checkbox.setChecked(self.settings_manager.get_setting("auto-save-settings"))
            notif_level = self.settings_manager.get_setting("notification-level", "normal")
            self.notif_combo.setCurrentText(notif_level.title())
        except Exception as e:
            print(f"Error loading advanced settings: {e}")