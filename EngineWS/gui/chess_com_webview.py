"""
Extension Installation Guide for BetterMint Modded GUI
Clean, modern implementation with improved visual design
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
    """Clean, modern extension installation guide widget"""
    
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
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1a1a1a;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #69923e;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #7aa84a;
            }
        """)
        
        # Main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(50, 40, 50, 40)
        content_layout.setSpacing(30)
        
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
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a5028,
                    stop:1 #69923e
                );
                border: none;
                border-radius: 12px;
                padding: 40px;
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(20)
        
    
    def create_installation_steps(self, layout):
        """Create installation steps section"""
        steps_frame = QFrame()
        steps_frame.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        
        steps_layout = QVBoxLayout(steps_frame)
        steps_layout.setSpacing(20)
        
        # Section title
        steps_title = QLabel("Installation Guide")
        steps_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        steps_title.setStyleSheet("color: #69923e; background: transparent; margin-bottom: 5px;")
        steps_layout.addWidget(steps_title)
        
        # Subtitle
        steps_subtitle = QLabel("Follow these steps to get started")
        steps_subtitle.setFont(QFont("Segoe UI", 10))
        steps_subtitle.setStyleSheet("color: #b0b0b0; background: transparent; margin-bottom: 15px;")
        steps_layout.addWidget(steps_subtitle)
        
        # Installation steps
        steps = [
            {
                "number": "1",
                "title": "Locate Extension Files",
                "description": "Open the folder containing the BetterMint Modded extension files. This folder includes all necessary components for installation.",
                "button_text": "Open Extension Folder",
                "action": self.open_extension_folder,
                "icon": "folder"
            },
            {
                "number": "2", 
                "title": "Access Chrome Extensions",
                "description": "Open Google Chrome and navigate to chrome://extensions/ in the address bar, or use Menu > More Tools > Extensions.",
                "button_text": None,
                "action": None,
                "icon": "browser"
            },
            {
                "number": "3",
                "title": "Enable Developer Mode", 
                "description": "Toggle the 'Developer mode' switch located in the top-right corner of the extensions page to enable manual installation.",
                "button_text": None,
                "action": None,
                "icon": "settings"
            },
            {
                "number": "4",
                "title": "Install Extension",
                "description": "Click the 'Load unpacked' button and select the BetterMint ModdedModded folder from step 1 to install the extension.",
                "button_text": None,
                "action": None,
                "icon": "upload"
            },
            {
                "number": "5",
                "title": "Start Analyzing",
                "description": "Visit your preferred chess platform and begin a game. The extension will automatically connect to the server and start providing analysis.",
                "button_text": None,
                "action": None,
                "icon": "play"
            }
        ]
        
        for step in steps:
            step_widget = self.create_step_widget(step)
            steps_layout.addWidget(step_widget)
        
        layout.addWidget(steps_frame)
    
    def create_step_widget(self, step_data):
        """Create individual step widget with modern design"""
        step_frame = QFrame()
        step_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 10px;
                padding: 20px;
                margin: 3px 0;
            }
            QFrame:hover {
                background-color: #323232;
                border: 1px solid #69923e;
            }
        """)
        
        step_layout = QHBoxLayout(step_frame)
        step_layout.setSpacing(20)
        
        # Step number circle with gradient
        number_label = QLabel(step_data["number"])
        number_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        number_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #69923e,
                    stop:1 #4e7837
                );
                color: white;
                border-radius: 25px;
                min-width: 50px;
                max-width: 50px;
                min-height: 50px;
                max-height: 50px;
            }
        """)
        number_label.setAlignment(Qt.AlignCenter)
        step_layout.addWidget(number_label)
        
        # Step content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        
        # Title with icon placeholder
        title_label = QLabel(step_data["title"])
        title_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff; background: transparent;")
        content_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(step_data["description"])
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setStyleSheet("color: #b0b0b0; background: transparent; line-height: 1.5;")
        desc_label.setWordWrap(True)
        content_layout.addWidget(desc_label)
        
        step_layout.addLayout(content_layout, 1)
        
        # Action button if provided
        if step_data["button_text"] and step_data["action"]:
            button = QPushButton(step_data["button_text"])
            button.setFont(QFont("Segoe UI", 10, QFont.Bold))
            button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 #69923e,
                        stop:1 #4e7837
                    );
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 24px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 #7aa84a,
                        stop:1 #69923e
                    );
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
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        
        usage_layout = QVBoxLayout(usage_frame)
        usage_layout.setSpacing(18)
        
        # Section title
        usage_title = QLabel("Quick Start Guide")
        usage_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        usage_title.setStyleSheet("color: #69923e; background: transparent; margin-bottom: 5px;")
        usage_layout.addWidget(usage_title)
        
        # Subtitle
        usage_subtitle = QLabel("How to use BetterMint Modded after installation")
        usage_subtitle.setFont(QFont("Segoe UI", 10))
        usage_subtitle.setStyleSheet("color: #b0b0b0; background: transparent; margin-bottom: 10px;")
        usage_layout.addWidget(usage_subtitle)
        
        # Usage instructions with bullet points
        usage_items = [
            "Verify the server is running (check for green status indicator)",
            "Configure your analysis preferences in the Intelligence and Engine tabs",
            "Open your chess platform in Chrome with the extension installed",
            "Start or join a game - analysis begins automatically",
            "Use visual hints, move suggestions, and evaluations to improve your play"
        ]
        
        for i, item in enumerate(usage_items, 1):
            item_frame = QFrame()
            item_frame.setStyleSheet("""
                QFrame {
                    background-color: #2d2d2d;
                    border-left: 3px solid #69923e;
                    border-radius: 4px;
                    padding: 12px 15px;
                }
            """)
            
            item_layout = QHBoxLayout(item_frame)
            item_layout.setSpacing(12)
            
            # Number badge
            number = QLabel(str(i))
            number.setFont(QFont("Segoe UI", 10, QFont.Bold))
            number.setStyleSheet("""
                QLabel {
                    background-color: #69923e;
                    color: white;
                    border-radius: 12px;
                    min-width: 24px;
                    max-width: 24px;
                    min-height: 24px;
                    max-height: 24px;
                }
            """)
            number.setAlignment(Qt.AlignCenter)
            item_layout.addWidget(number)
            
            # Item text
            text = QLabel(item)
            text.setFont(QFont("Segoe UI", 10))
            text.setStyleSheet("color: #e0e0e0; background: transparent;")
            text.setWordWrap(True)
            item_layout.addWidget(text, 1)
            
            usage_layout.addWidget(item_frame)
        
        layout.addWidget(usage_frame)
    
    def create_footer_section(self, layout):
        """Create footer section"""
        footer_frame = QFrame()
        footer_frame.setStyleSheet("""
            QFrame {
                background-color: #1f1f1f;
                border: 1px solid #3a3a3a;
                border-radius: 12px;
                padding: 25px;
                margin-top: 10px;
            }
        """)
        
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setSpacing(15)
        
        # Important notice
        notice_title = QLabel("Important Notice")
        notice_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        notice_title.setStyleSheet("color: #ffa726; background: transparent;")
        notice_title.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(notice_title)
        
        note = QLabel(
            "This extension is designed for chess analysis and educational purposes. "
            "Please use responsibly and in accordance with the terms of service of your chess platform. "
            "BetterMint Modded is intended to help you learn and improve your chess skills."
        )
        note.setFont(QFont("Segoe UI", 9))
        note.setStyleSheet("color: #c0c0c0; background: transparent; line-height: 1.4;")
        note.setWordWrap(True)
        note.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(note)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #3a3a3a; max-height: 1px;")
        footer_layout.addWidget(divider)
        
        # Version info
        version_info = QLabel("MINT Beta 2c 26092025 Features - Educational Chess Analysis Tool")
        version_info.setFont(QFont("Segoe UI", 9, QFont.Bold))
        version_info.setStyleSheet("color: #69923e; background: transparent;")
        version_info.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(version_info)
        
        layout.addWidget(footer_frame)
    
    def open_extension_folder(self):
        """Open the extension folder in file manager"""
        try:
            # Get the extension folder path
            script_dir = Path(__file__).parent.parent.parent
            extension_dir = script_dir / "BetterMint ModdedModded"
            
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