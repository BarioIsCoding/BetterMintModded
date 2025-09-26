"""
Extension Installation Guide for BetterMint Modded GUI
Clean implementation without browser automation - encourages manual extension use
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QPixmap


class PlaywrightChessController(QObject):
    """
    Compatibility stub - all browser automation removed.
    Maintains interface compatibility with existing code.
    """
    
    # Signals for backwards compatibility
    page_loaded = Signal(str)
    extension_data_updated = Signal(dict)
    move_suggested = Signal(str)
    error_occurred = Signal(str)
    connection_status_changed = Signal(bool)
    initialization_progress = Signal(str)
    screenshot_updated = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_playwright_active = False
    
    def start_async_loop(self):
        """Stub - no browser automation"""
        pass
    
    def stop_async_loop(self):
        """Stub - no cleanup needed"""
        pass
    
    def make_move(self, move: str):
        """Stub - returns False"""
        return False
    
    def get_game_state(self) -> Dict[str, Any]:
        """Stub - returns empty dict"""
        return {}


class ExtensionGuideWidget(QWidget):
    """Clean extension installation guide widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the extension guide UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create scroll area for the guide
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(25)
        
        # Header section
        self.create_header_section(content_layout)
        
        # Installation steps
        self.create_installation_steps(content_layout)
        
        # Usage information
        self.create_usage_section(content_layout)
        
        # Footer
        self.create_footer_section(content_layout)
        
        # Add stretch at end
        content_layout.addStretch()
        
        # Set up scroll area
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
    
    def create_header_section(self, layout):
        """Create the header section"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #4b4847;
                border: 1px solid #69923e;
                border-radius: 8px;
                padding: 30px;
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(15)
        
        # Main title
        title = QLabel("Chrome Extension Installation")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #69923e; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Install the BetterMint Modded browser extension to enable chess analysis on your favorite platforms."
        )
        desc.setFont(QFont("Arial", 12))
        desc.setStyleSheet("color: #ffffff; background: transparent;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        header_layout.addWidget(desc)
        
        layout.addWidget(header_frame)
    
    def create_installation_steps(self, layout):
        """Create installation steps section"""
        steps_frame = QFrame()
        steps_frame.setStyleSheet("""
            QFrame {
                background-color: #2c2b29;
                border: 1px solid #4b4847;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        steps_layout = QVBoxLayout(steps_frame)
        steps_layout.setSpacing(15)
        
        # Section title
        steps_title = QLabel("Installation Steps")
        steps_title.setFont(QFont("Arial", 16, QFont.Bold))
        steps_title.setStyleSheet("color: #69923e; background: transparent; margin-bottom: 10px;")
        steps_layout.addWidget(steps_title)
        
        # Installation steps
        steps = [
            {
                "number": "1",
                "title": "Get Extension Files",
                "description": "Click the button below to open the extension folder containing all necessary files.",
                "button_text": "Open Extension Folder",
                "action": self.open_extension_folder
            },
            {
                "number": "2", 
                "title": "Open Browser Extensions",
                "description": "In Google Chrome, navigate to chrome://extensions/ or use Menu > Extensions > Manage Extensions.",
                "button_text": None,
                "action": None
            },
            {
                "number": "3",
                "title": "Enable Developer Mode", 
                "description": "Toggle the 'Developer mode' switch in the top-right corner of the extensions page.",
                "button_text": None,
                "action": None
            },
            {
                "number": "4",
                "title": "Load Extension",
                "description": "Click 'Load unpacked' and select the BetterMintModded folder from step 1.",
                "button_text": None,
                "action": None
            },
            {
                "number": "5",
                "title": "Start Playing",
                "description": "Navigate to your chess platform and start a game. The extension will automatically connect.",
                "button_text": None,
                "action": None
            }
        ]
        
        for step in steps:
            step_widget = self.create_step_widget(step)
            steps_layout.addWidget(step_widget)
        
        layout.addWidget(steps_frame)
    
    def create_step_widget(self, step_data):
        """Create individual step widget"""
        step_frame = QFrame()
        step_frame.setStyleSheet("""
            QFrame {
                background-color: #4b4847;
                border: 1px solid #69923e;
                border-radius: 6px;
                padding: 15px;
                margin: 5px 0;
            }
        """)
        
        step_layout = QHBoxLayout(step_frame)
        step_layout.setSpacing(15)
        
        # Step number circle
        number_label = QLabel(step_data["number"])
        number_label.setFont(QFont("Arial", 14, QFont.Bold))
        number_label.setStyleSheet("""
            QLabel {
                background-color: #69923e;
                color: white;
                border-radius: 20px;
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
                qproperty-alignment: AlignCenter;
            }
        """)
        number_label.setAlignment(Qt.AlignCenter)
        step_layout.addWidget(number_label)
        
        # Step content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)
        
        # Title
        title_label = QLabel(step_data["title"])
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff; background: transparent;")
        content_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(step_data["description"])
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setStyleSheet("color: #cccccc; background: transparent;")
        desc_label.setWordWrap(True)
        content_layout.addWidget(desc_label)
        
        step_layout.addLayout(content_layout, 1)
        
        # Action button if provided
        if step_data["button_text"] and step_data["action"]:
            button = QPushButton(step_data["button_text"])
            button.setFont(QFont("Arial", 9, QFont.Bold))
            button.setStyleSheet("""
                QPushButton {
                    background-color: #69923e;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #4e7837;
                }
                QPushButton:pressed {
                    background-color: #3e5f2b;
                }
            """)
            button.clicked.connect(step_data["action"])
            step_layout.addWidget(button)
        
        return step_frame
    
    def create_usage_section(self, layout):
        """Create usage information section"""
        usage_frame = QFrame()
        usage_frame.setStyleSheet("""
            QFrame {
                background-color: #2c2b29;
                border: 1px solid #4b4847;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        usage_layout = QVBoxLayout(usage_frame)
        usage_layout.setSpacing(15)
        
        # Section title
        usage_title = QLabel("How to Use")
        usage_title.setFont(QFont("Arial", 16, QFont.Bold))
        usage_title.setStyleSheet("color: #69923e; background: transparent; margin-bottom: 5px;")
        usage_layout.addWidget(usage_title)
        
        # Usage instructions
        usage_text = QLabel(
            "1. Ensure the BetterMint Modded server is running (green status indicator)\n"
            "2. Configure your analysis preferences in the Intelligence and Engine tabs\n"
            "3. Open your chess platform in the browser with the extension installed\n"
            "4. Start or join a chess game - analysis will begin automatically\n"
            "5. Use visual hints, move suggestions, and evaluation data to improve your play"
        )
        usage_text.setFont(QFont("Arial", 11))
        usage_text.setStyleSheet("color: #ffffff; background: transparent; line-height: 1.4;")
        usage_text.setWordWrap(True)
        usage_layout.addWidget(usage_text)
        
        layout.addWidget(usage_frame)
    
    def create_footer_section(self, layout):
        """Create footer section"""
        footer_frame = QFrame()
        footer_frame.setStyleSheet("""
            QFrame {
                background-color: #4b4847;
                border: 1px solid #69923e;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
            }
        """)
        
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setSpacing(10)
        
        # Important note
        note = QLabel(
            "Important: This extension is designed for chess analysis and learning purposes. "
            "Use responsibly and in accordance with the terms of service of your chess platform."
        )
        note.setFont(QFont("Arial", 9))
        note.setStyleSheet("color: #cccccc; background: transparent;")
        note.setWordWrap(True)
        note.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(note)
        
        # Version info
        version_info = QLabel("BetterMint Modded v3.0.0 - Educational Chess Analysis Tool")
        version_info.setFont(QFont("Arial", 8))
        version_info.setStyleSheet("color: #999999; background: transparent;")
        version_info.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(version_info)
        
        layout.addWidget(footer_frame)
    
    def open_extension_folder(self):
        """Open the extension folder in file manager"""
        try:
            # Get the extension folder path
            script_dir = Path(__file__).parent.parent.parent
            extension_dir = script_dir / "BetterMintModded"
            
            if extension_dir.exists():
                # Open folder based on OS
                if sys.platform == 'win32':
                    os.startfile(str(extension_dir))
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', str(extension_dir)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(extension_dir)])
                
                print(f"Opened extension folder: {extension_dir}")
            else:
                print(f"Extension folder not found: {extension_dir}")
                # Show error in the UI instead of console only
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Folder Not Found", 
                    f"Extension folder not found at:\n{extension_dir}\n\n"
                    "Please ensure BetterMint Modded is properly installed."
                )
        except Exception as e:
            print(f"Error opening extension folder: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open extension folder:\n{str(e)}"
            )


# Aliases for backward compatibility
ChessComWebView = ExtensionGuideWidget
EnhancedChessComWebView = ExtensionGuideWidget

# Compatibility flag
PLAYWRIGHT_AVAILABLE = False