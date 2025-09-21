"""
Debug tab for BetterMint Modded GUI
Connection monitoring, activity logging, real-time status tracking, and cleanup tools
"""

import os
import sys
import subprocess
import webbrowser
import time
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QTextEdit, QFileDialog, QMessageBox,
    QDialog, QLabel, QScrollArea, QFrame, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from settings import SettingsManager


class CleanupDialog(QDialog):
    """Advanced cleanup and repair dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Cleanup Functions")
        self.setModal(True)
        self.setFixedSize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the cleanup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Header icon and title
        header_title = QLabel("Advanced cleanup functions")
        header_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        
        # Return button
        return_btn = QPushButton("Return")
        return_btn.clicked.connect(self.accept)
        header_layout.addWidget(return_btn)
        
        layout.addWidget(header_frame)
        
        # Description - UPDATED TEXT
        desc_label = QLabel("Note: Most options will close BetterMint Modded. That said, here are the repair functions:")
        desc_label.setWordWrap(True)
        desc_label.setContentsMargins(20, 15, 20, 10)
        layout.addWidget(desc_label)
        
        # Scroll area for cleanup options
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(2)
        scroll_layout.setContentsMargins(20, 0, 20, 0)
        
        # Cleanup options
        cleanup_options = [
            {
                "title": "Playwright issues?",
                "description": "Fixes browser automation issues that prevent web interface loading.\nSafety: Low risk\nSolves: Browser connection problems\nTime: 30-60 seconds",
                "button_text": "Fix!",
                "action": self.fix_playwright,
                "icon_color": "#4CAF50"
            },
            {
                "title": "Find path",
                "description": "Shows current installation path for troubleshooting.\nSafety: No risk\nSolves: Path-related configuration issues\nTime: Instant",
                "button_text": "Find",
                "action": self.show_path,
                "icon_color": "#2196F3"
            },
            {
                "title": "Improper pip installation?",
                "description": "Reinstalls Python dependencies and fixes package conflicts.\nSafety: Low risk\nSolves: Missing or corrupted Python packages\nTime: 1-3 minutes",
                "button_text": "Fix!",
                "action": self.fix_pip,
                "icon_color": "#FF9800"
            },
            {
                "title": "Improper engine installation?",
                "description": "Downloads and installs missing chess engines (Stockfish, Leela).\nSafety: Low risk\nSolves: Missing or corrupted engine files\nTime: 2-5 minutes",
                "button_text": "Fix!",
                "action": self.fix_engines,
                "icon_color": "#9C27B0"
            },
            {
                "title": "Reinstall BetterMint Modded?",
                "description": "Complete reinstallation while preserving user settings.\nSafety: Medium risk\nSolves: Core application corruption\nTime: 3-10 minutes",
                "button_text": "Reinstall",
                "action": self.reinstall_app,
                "icon_color": "#FF5722"
            },
            {
                "title": "Uninstall BetterMint Modded?",
                "description": "Completely removes BetterMint Modded and all associated files.\nSafety: High risk - permanent removal\nSolves: Complete cleanup for fresh start\nTime: 1-2 minutes",
                "button_text": "Uninstall",
                "action": self.uninstall_app,
                "icon_color": "#F44336"
            },
            {
                "title": "Config issue?",
                "description": "Resets all configuration to default values.\nSafety: Medium risk - loses custom settings\nSolves: Corrupted configuration files\nTime: Instant",
                "button_text": "Reset",
                "action": self.reset_config,
                "icon_color": "#607D8B"
            },
            {
                "title": "Other issue?",
                "description": "Opens GitHub issues page for reporting unlisted problems.\nSafety: No risk\nSolves: Contact support for unique issues\nTime: Instant",
                "button_text": "Feedback",
                "action": self.open_feedback,
                "icon_color": "#795548"
            },
            {
                "title": "Report bugs?",
                "description": "Opens GitHub issues page for bug reporting.\nSafety: No risk\nSolves: Report software bugs to developers\nTime: Instant",
                "button_text": "Feedback",
                "action": self.report_bugs,
                "icon_color": "#E91E63"
            }
        ]
        
        for option in cleanup_options:
            option_widget = self.create_cleanup_option(option)
            scroll_layout.addWidget(option_widget)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Footer
        footer_label = QLabel("If you still can't connect, please send feedback to our GitHub repository.")
        footer_label.setWordWrap(True)
        footer_label.setContentsMargins(20, 10, 20, 15)
        footer_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(footer_label)
    
    def create_cleanup_option(self, option):
        """Create a single cleanup option widget"""
        frame = QFrame()
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(15)
        
        # Icon placeholder (colored square)
        icon_frame = QFrame()
        icon_frame.setFixedSize(24, 24)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {option['icon_color']};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(icon_frame)
        
        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(option['title'])
        title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title_label.setStyleSheet("color: #333;")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(option['description'])
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setStyleSheet("color: #666; line-height: 1.2;")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Action button
        action_btn = QPushButton(option['button_text'])
        action_btn.clicked.connect(option['action'])
        layout.addWidget(action_btn)
        
        return frame
    
    def run_debug_script(self, script_name):
        """Run a debug script from the debug directory in a new window"""
        try:
            # Get main.py directory
            main_dir = Path(__file__).parent.parent
            debug_dir = main_dir / "debug"
            
            # Determine script extension based on platform
            if sys.platform == "win32":
                script_file = debug_dir / f"{script_name}.bat"
            else:
                script_file = debug_dir / f"{script_name}.sh"
            
            if not script_file.exists():
                QMessageBox.warning(
                    self,
                    "Script Not Found",
                    f"Debug script not found: {script_file}\n\n"
                    "Please ensure the debug scripts are properly installed."
                )
                return False
            
            # Run the script in a new window
            if sys.platform == "win32":
                # Use start command to open in new command window
                cmd = f'start "BetterMint Debug - {script_name}" /wait cmd /c "{script_file}"'
                subprocess.Popen(cmd, shell=True, cwd=str(debug_dir))
            else:
                # Try different terminal emulators for Unix-like systems
                script_path = str(script_file)
                terminals = [
                    ['gnome-terminal', '--', 'bash', script_path],
                    ['konsole', '-e', 'bash', script_path],
                    ['xterm', '-e', 'bash', script_path],
                    ['x-terminal-emulator', '-e', 'bash', script_path]
                ]
                
                terminal_started = False
                for terminal_cmd in terminals:
                    try:
                        subprocess.Popen(terminal_cmd, cwd=str(debug_dir))
                        terminal_started = True
                        break
                    except FileNotFoundError:
                        continue
                
                if not terminal_started:
                    # Fallback: run in background if no terminal emulator found
                    subprocess.Popen(['bash', script_path], cwd=str(debug_dir))
            
            # Show confirmation message
            QMessageBox.information(
                self,
                "Script Started",
                f"Debug script '{script_name}' has been started in a new window.\n\n"
                "BetterMint Modded will now close to prevent conflicts during the repair process."
            )
            
            # Close dialog and application
            self.close_application()
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Script Error",
                f"Failed to run debug script '{script_name}':\n\n{str(e)}"
            )
            return False
    
    def close_application(self):
        """Close the dialog and then the entire application"""
        try:
            # Close this dialog first
            self.accept()
            
            # Use a timer to close the application after a short delay
            # This ensures the dialog closes properly before the app exits
            QTimer.singleShot(500, self.force_close_app)
            
        except Exception as e:
            print(f"Error during application close: {e}")
            # Force close as fallback
            sys.exit(0)
    
    def force_close_app(self):
        """Force close the entire application"""
        try:
            app = QApplication.instance()
            if app:
                app.quit()
            
            # Fallback: force exit after short delay
            QTimer.singleShot(1000, lambda: sys.exit(0))
            
        except Exception:
            # Ultimate fallback
            sys.exit(0)
    
    def fix_playwright(self):
        """Fix Playwright browser automation issues"""
        self.run_debug_script("playwright_fix")
    
    def show_path(self):
        """Show current installation path"""
        try:
            current_path = str(Path(__file__).parent.parent.absolute())
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Current Installation Path")
            msg_box.setText("BetterMint Modded Installation Path:")
            msg_box.setDetailedText(current_path)
            msg_box.setStandardButtons(QMessageBox.Ok)
            
            # Make the path selectable
            msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
            
            msg_box.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Path Error",
                f"Failed to determine installation path:\n\n{str(e)}"
            )
    
    def fix_pip(self):
        """Fix pip installation issues"""
        self.run_debug_script("pip_fix")
    
    def fix_engines(self):
        """Fix engine installation issues"""
        self.run_debug_script("engine_fix")
    
    def reinstall_app(self):
        """Reinstall BetterMint Modded"""
        reply = QMessageBox.question(
            self,
            "Confirm Reinstallation",
            "This will reinstall BetterMint Modded while preserving your settings.\n\n"
            "Continue with reinstallation?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.run_debug_script("reinstall")
    
    def uninstall_app(self):
        """Uninstall BetterMint Modded"""
        reply = QMessageBox.warning(
            self,
            "Confirm Uninstallation",
            "WARNING: This will completely remove BetterMint Modded and all associated files.\n\n"
            "This action cannot be undone. Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Double confirmation for destructive action
            final_reply = QMessageBox.critical(
                self,
                "Final Confirmation",
                "FINAL WARNING: You are about to permanently delete BetterMint Modded.\n\n"
                "Type 'UNINSTALL' in the next dialog to confirm.",
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            
            if final_reply == QMessageBox.Ok:
                self.run_debug_script("uninstall")
    
    def reset_config(self):
        """Reset configuration files"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Reset Configuration")
        msg_box.setText("Please use the toolbar > File > New Profile to reset the BetterMint Modded configuration.")
        
        # Style the text with blue color for the menu path
        msg_box.setInformativeText("This is not recommended unless you're experiencing configuration issues.")
        
        # Create rich text for the detailed text
        detailed_text = (
            "To reset your configuration:\n\n"
            "1. Go to the main window\n"
            "2. Click on 'File' in the toolbar\n"
            "3. Select 'New Profile'\n"
            "4. This will create a fresh configuration\n\n"
            "Note: This will reset all your custom settings to defaults."
        )
        msg_box.setDetailedText(detailed_text)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec()
    
    def open_feedback(self):
        """Open feedback page"""
        self.open_github_issues("Other Issue")
    
    def report_bugs(self):
        """Open bug reporting page"""
        self.open_github_issues("Bug Report")
    
    def open_github_issues(self, issue_type):
        """Open GitHub issues page with confirmation"""
        reply = QMessageBox.question(
            self,
            "Open External URL",
            f"This will open the GitHub issues page for {issue_type} in your default browser.\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            try:
                url = "https://github.com/BarioIsCoding/BetterMintModded/issues/new"
                webbrowser.open(url)
                
                QMessageBox.information(
                    self,
                    "URL Opened",
                    f"GitHub issues page opened in your default browser for {issue_type}."
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Browser Error",
                    f"Failed to open browser:\n\n{str(e)}\n\n"
                    f"Please manually visit:\n{url}"
                )


class MonitoringTab(QWidget):
    """Tab for debugging, connection monitoring, and activity logging"""
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()

    def setup_ui(self):
        """Setup the Debug tab UI"""
        layout = QVBoxLayout(self)

        # Debug Tools
        debug_group = QGroupBox("Debug Tools")
        debug_group.setObjectName("settings_group")
        debug_layout = QVBoxLayout(debug_group)

        # Cleanup button
        cleanup_btn = QPushButton("Advanced Cleanup Functions")
        cleanup_btn.clicked.connect(self.open_cleanup_dialog)
        debug_layout.addWidget(cleanup_btn)

        layout.addWidget(debug_group)

        # Connection Monitor
        conn_group = QGroupBox("Connection Monitor")
        conn_group.setObjectName("settings_group")
        conn_layout = QVBoxLayout(conn_group)

        # Connection table
        self.connection_table = QTableWidget()
        self.connection_table.setColumnCount(4)
        self.connection_table.setHorizontalHeaderLabels([
            "Client ID", 
            "Connected At", 
            "Last Activity", 
            "Status"
        ])
        self.connection_table.horizontalHeader().setStretchLastSection(True)
        self.connection_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        conn_layout.addWidget(self.connection_table)

        layout.addWidget(conn_group)

        # Activity Log
        log_group = QGroupBox("Activity Log")
        log_group.setObjectName("settings_group")
        log_layout = QVBoxLayout(log_group)

        self.activity_log = QTextEdit()
        self.activity_log.setObjectName("activity_log")
        self.activity_log.setMaximumHeight(200)
        self.activity_log.setReadOnly(True)
        log_layout.addWidget(self.activity_log)

        # Log controls
        log_controls = QHBoxLayout()
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        log_controls.addWidget(clear_log_btn)

        export_log_btn = QPushButton("Export Log")
        export_log_btn.clicked.connect(self.export_log)
        log_controls.addWidget(export_log_btn)

        log_controls.addStretch()
        log_layout.addLayout(log_controls)

        layout.addWidget(log_group)
    
    def open_cleanup_dialog(self):
        """Open the advanced cleanup dialog"""
        try:
            dialog = CleanupDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Dialog Error",
                f"Failed to open cleanup dialog:\n\n{str(e)}"
            )
    
    def update_connection_table(self, connections):
        """Update the connection monitor table with error handling"""
        try:
            self.connection_table.setRowCount(len(connections))
            
            for i, conn_info in enumerate(connections):
                client_id = conn_info.get('client_id', 'Unknown')
                connected_time = conn_info.get('connected_time', '')
                last_activity = conn_info.get('last_activity', '')
                status = conn_info.get('status', 'Unknown')
                
                # Set table items with safe error handling
                self.connection_table.setItem(i, 0, QTableWidgetItem(str(client_id)))
                self.connection_table.setItem(i, 1, QTableWidgetItem(str(connected_time)))
                self.connection_table.setItem(i, 2, QTableWidgetItem(str(last_activity)))
                self.connection_table.setItem(i, 3, QTableWidgetItem(str(status)))
                
        except Exception as e:
            print(f"Error updating connection table: {e}")
    
    def log_activity(self, message):
        """Log activity message with timestamp"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            self.activity_log.append(formatted_message)
            
            # Auto-scroll to bottom to show latest messages
            scrollbar = self.activity_log.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            print(f"Error logging activity: {e}")
    
    def clear_log(self):
        """Clear activity log with confirmation"""
        try:
            if self.activity_log.toPlainText().strip():
                reply = QMessageBox.question(
                    self, 
                    "Clear Log", 
                    "Are you sure you want to clear the activity log?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.activity_log.clear()
                    self.log_activity("Activity log cleared")
            else:
                self.activity_log.clear()
        except Exception as e:
            print(f"Error clearing log: {e}")
    
    def export_log(self):
        """Export activity log to file with error handling"""
        try:
            log_content = self.activity_log.toPlainText()
            
            if not log_content.strip():
                QMessageBox.information(self, "Export Log", "No activity log data to export.")
                return
                
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_filename = f"betterMint_log_{timestamp}.txt"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Export Log", 
                default_filename, 
                "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"BetterMint Modded Activity Log\n")
                    f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(log_content)
                
                self.log_activity(f"Activity log exported to: {file_path}")
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Log exported successfully to:\n{file_path}"
                )
                
        except Exception as e:
            error_msg = f"Failed to export log: {str(e)}"
            print(f"Error exporting log: {e}")
            QMessageBox.critical(self, "Export Error", error_msg)
    
    def load_settings(self):
        """No persistent settings for debug tab"""
        # This tab doesn't have user-configurable settings to load
        # It primarily displays real-time data and logs
        pass
    
    def get_connection_count(self):
        """Get current connection count"""
        return self.connection_table.rowCount()
    
    def clear_connections(self):
        """Clear all connection data"""
        try:
            self.connection_table.setRowCount(0)
            self.log_activity("Connection table cleared")
        except Exception as e:
            print(f"Error clearing connections: {e}")