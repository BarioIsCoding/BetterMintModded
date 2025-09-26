"""
Custom Chess Engine Store for BetterMint Modded
Allows importing, managing, and installing custom UCI chess engines
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QMessageBox,
    QFrame, QWidget, QScrollArea, QFileDialog, QLineEdit,
    QWizard, QWizardPage, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap

from constants import COLORS, APP_NAME


class EngineManifest:
    """Represents a chess engine with its metadata"""
    
    def __init__(self, name: str, executable: str, description: str = "",
                 is_builtin: bool = False, platform: str = "windows"):
        self.name = name
        self.executable = executable
        self.description = description
        self.is_builtin = is_builtin
        self.platform = platform
        self.enabled = True
        
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'executable': self.executable,
            'description': self.description,
            'is_builtin': self.is_builtin,
            'platform': self.platform,
            'enabled': self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EngineManifest':
        manifest = cls(
            name=data.get('name', 'Unknown'),
            executable=data.get('executable', ''),
            description=data.get('description', ''),
            is_builtin=data.get('is_builtin', False),
            platform=data.get('platform', 'windows')
        )
        manifest.enabled = data.get('enabled', True)
        return manifest


class EngineManager:
    """Manages custom engine installations and manifests"""
    
    def __init__(self, engines_dir: str = "engines"):
        self.engines_dir = Path(engines_dir)
        self.engines_dir.mkdir(exist_ok=True)
        self.engines: Dict[str, EngineManifest] = {}
        self.load_all_engines()
    
    def load_all_engines(self):
        """Load all engines from the engines directory"""
        self.engines.clear()
        
        # Load built-in engines
        self._load_builtin_engines()
        
        # Load custom engines from manifests
        for engine_dir in self.engines_dir.iterdir():
            if engine_dir.is_dir():
                manifest_path = engine_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            manifest = EngineManifest.from_dict(data)
                            self.engines[manifest.name] = manifest
                    except Exception as e:
                        print(f"Error loading manifest from {engine_dir}: {e}")
    
    def _load_builtin_engines(self):
        """Load built-in engine definitions"""
        builtin_engines = [
            {
                'name': 'Stockfish',
                'executable': 'stockfish/stockfish.exe',
                'description': 'World\'s strongest chess engine with advanced analysis capabilities',
                'platform': 'windows'
            },
            {
                'name': 'Leela Chess Zero',
                'executable': 'leela/lc0.exe',
                'description': 'Neural network-based engine with human-like play and Maia support',
                'platform': 'windows'
            },
            {
                'name': 'Rodent IV',
                'executable': 'rodent/rodent-iv-plain.exe',
                'description': 'Personality-based engine with multiple playing styles',
                'platform': 'windows'
            }
        ]
        
        for engine_data in builtin_engines:
            engine_path = self.engines_dir / engine_data['executable']
            if engine_path.exists():
                manifest = EngineManifest(
                    name=engine_data['name'],
                    executable=engine_data['executable'],
                    description=engine_data['description'],
                    is_builtin=True,
                    platform=engine_data['platform']
                )
                self.engines[manifest.name] = manifest
    
    def install_engine(self, source_folder: Path, executable_name: str,
                      engine_name: str, description: str) -> bool:
        """Install a custom engine"""
        try:
            # Create engine directory
            engine_dir = self.engines_dir / engine_name.lower().replace(' ', '_')
            engine_dir.mkdir(exist_ok=True)
            
            # Verify executable exists in source
            source_executable = source_folder / executable_name
            if not source_executable.exists():
                raise FileNotFoundError(f"Executable not found: {source_executable}")
            
            print(f"Copying all files from {source_folder} to {engine_dir}")
            copied_count = 0
            
            for item in source_folder.rglob('*'):
                if item.is_file():
                    # Calculate relative path
                    relative_path = item.relative_to(source_folder)
                    dest_path = engine_dir / relative_path
                    
                    # Create parent directories if needed
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(item, dest_path)
                    copied_count += 1
                    
                    # Set executable permissions for main executable on Linux
                    if item.name == executable_name and not executable_name.endswith('.exe'):
                        try:
                            dest_path.chmod(0o755)
                        except:
                            pass
            
            print(f"Copied {copied_count} files/dependencies")
            
            # Create manifest
            manifest = EngineManifest(
                name=engine_name,
                executable=f"{engine_dir.name}/{executable_name}",
                description=description,
                is_builtin=False,
                platform='windows' if executable_name.endswith('.exe') else 'linux'
            )
            
            manifest_path = engine_dir / "manifest.json"
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest.to_dict(), f, indent=2)
            
            # Add to engines dict
            self.engines[engine_name] = manifest
            
            print(f"Successfully installed engine: {engine_name} with {copied_count} files")
            return True
            
        except Exception as e:
            print(f"Error installing engine: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def uninstall_engine(self, engine_name: str) -> bool:
        """Uninstall a custom engine"""
        if engine_name not in self.engines:
            return False
        
        manifest = self.engines[engine_name]
        if manifest.is_builtin:
            return False  # Can't uninstall built-in engines
        
        try:
            # Remove engine directory
            engine_dir = self.engines_dir / engine_name.lower().replace(' ', '_')
            if engine_dir.exists():
                shutil.rmtree(engine_dir)
            
            # Remove from dict
            del self.engines[engine_name]
            
            print(f"Successfully uninstalled engine: {engine_name}")
            return True
            
        except Exception as e:
            print(f"Error uninstalling engine: {e}")
            return False
    
    def get_engine_path(self, engine_name: str) -> Optional[str]:
        """Get full path to engine executable"""
        if engine_name not in self.engines:
            return None
        
        manifest = self.engines[engine_name]
        return str(self.engines_dir / manifest.executable)


class EngineImportWizard(QWizard):
    """Multi-step wizard for importing custom engines"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Custom Chess Engine")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setMinimumSize(600, 500)
        
        # Store wizard data
        self.selected_folder = None
        self.selected_executable = None
        self.engine_name = ""
        self.engine_description = ""
        
        # Add pages
        self.addPage(self.create_folder_page())
        self.addPage(self.create_executable_page())
        self.addPage(self.create_name_page())
        self.addPage(self.create_description_page())
        
        self.apply_styles()
    
    def create_folder_page(self) -> QWizardPage:
        """Step 1: Select engine folder"""
        page = QWizardPage()
        page.setTitle("Select Engine Folder")
        page.setSubTitle("Choose the folder containing your chess engine")
        
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # Instructions
        instructions = QLabel(
            "Select the folder where your chess engine is located.\n"
            "ALL files and subdirectories will be copied to preserve dependencies.\n"
            "This folder should contain the engine's main executable file."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Warning about folder contents
        warning = QLabel(
            "Note: The entire folder contents will be imported, so make sure "
            "it doesn't contain personal stuff. Only UCI Engines are supported."
            "For more information, use a search engine of your choice and search for"
            "\"List of UCI Chess Engines\"."
        )
        warning.setObjectName("warning_label")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Folder selection
        folder_frame = QFrame()
        folder_frame.setObjectName("selection_frame")
        folder_layout = QVBoxLayout(folder_frame)
        
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setObjectName("path_label")
        self.folder_label.setWordWrap(True)
        folder_layout.addWidget(self.folder_label)
        
        select_folder_btn = QPushButton("Browse for Folder...")
        select_folder_btn.setObjectName("browse_button")
        select_folder_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(select_folder_btn)
        
        layout.addWidget(folder_frame)
        layout.addStretch()
        
        return page
    
    def create_executable_page(self) -> QWizardPage:
        """Step 2: Select engine executable"""
        page = QWizardPage()
        page.setTitle("Select Engine Executable")
        page.setSubTitle("Choose the main executable file for the engine")
        
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # Instructions
        instructions = QLabel(
            "Select the executable file for your chess engine.\n"
            "Common names: engine.exe, chess.exe, uci.exe\n"
            "Linux engines typically have no extension."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Executable list
        list_label = QLabel("Available files in folder:")
        layout.addWidget(list_label)
        
        self.executable_list = QListWidget()
        self.executable_list.setObjectName("file_list")
        self.executable_list.itemSelectionChanged.connect(self.on_executable_selected)
        layout.addWidget(self.executable_list)
        
        self.executable_label = QLabel("No file selected")
        self.executable_label.setObjectName("selection_label")
        layout.addWidget(self.executable_label)
        
        return page
    
    def create_name_page(self) -> QWizardPage:
        """Step 3: Enter engine name"""
        page = QWizardPage()
        page.setTitle("Name Your Engine")
        page.setSubTitle("Provide a friendly name for this engine")
        
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # Instructions
        instructions = QLabel(
            "Enter a unique name for this engine.\n"
            "This name will appear in the engine selection list."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Name input
        name_label = QLabel("Engine Name:")
        name_label.setObjectName("input_label")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setObjectName("name_input")
        self.name_input.setPlaceholderText("e.g., My Custom Engine")
        self.name_input.textChanged.connect(self.on_name_changed)
        layout.addWidget(self.name_input)
        
        # Validation message
        self.name_validation = QLabel("")
        self.name_validation.setObjectName("validation_label")
        layout.addWidget(self.name_validation)
        
        layout.addStretch()
        
        return page
    
    def create_description_page(self) -> QWizardPage:
        """Step 4: Enter engine description"""
        page = QWizardPage()
        page.setTitle("Describe Your Engine")
        page.setSubTitle("Add a brief description (optional)")
        
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        
        # Instructions
        instructions = QLabel(
            "Provide a brief description of this engine.\n"
            "Include details like playing style, strength, or special features."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Description input
        desc_label = QLabel("Description:")
        desc_label.setObjectName("input_label")
        layout.addWidget(desc_label)
        
        self.description_input = QTextEdit()
        self.description_input.setObjectName("description_input")
        self.description_input.setPlaceholderText(
            "e.g., A strong tactical engine with aggressive playing style. "
            "Best suited for tactical positions and sharp play."
        )
        self.description_input.setMaximumHeight(150)
        self.description_input.textChanged.connect(self.on_description_changed)
        layout.addWidget(self.description_input)
        
        # Summary
        summary_label = QLabel("Import Summary:")
        summary_label.setObjectName("summary_label")
        layout.addWidget(summary_label)
        
        self.summary_text = QTextEdit()
        self.summary_text.setObjectName("summary_display")
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(120)
        layout.addWidget(self.summary_text)
        
        return page
    
    def select_folder(self):
        """Open folder selection dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Engine Folder",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            self.selected_folder = Path(folder)
            self.folder_label.setText(f"Selected: {folder}")
            self.populate_executable_list()
    
    def populate_executable_list(self):
        """Populate list of potential executables"""
        if not self.selected_folder:
            return
        
        self.executable_list.clear()
        
        # Look for executable files
        for file in self.selected_folder.iterdir():
            if file.is_file():
                # Windows executables or files without extension (Linux)
                if file.suffix.lower() == '.exe' or not file.suffix:
                    item = QListWidgetItem(file.name)
                    self.executable_list.addItem(item)
    
    def on_executable_selected(self):
        """Handle executable selection"""
        current_item = self.executable_list.currentItem()
        if current_item:
            self.selected_executable = current_item.text()
            self.executable_label.setText(f"Selected: {self.selected_executable}")
    
    def on_name_changed(self, text):
        """Validate engine name"""
        self.engine_name = text.strip()
        
        if len(self.engine_name) < 3:
            self.name_validation.setText("Name must be at least 3 characters")
            self.name_validation.setStyleSheet(f"color: {COLORS['error_red']};")
        else:
            self.name_validation.setText("Valid name")
            self.name_validation.setStyleSheet(f"color: {COLORS['success_green']};")
        
        self.update_summary()
    
    def on_description_changed(self):
        """Update description"""
        self.engine_description = self.description_input.toPlainText().strip()
        self.update_summary()
    
    def update_summary(self):
        """Update import summary"""
        summary = []
        summary.append(f"<b>Engine Name:</b> {self.engine_name or 'Not set'}")
        summary.append(f"<b>Executable:</b> {self.selected_executable or 'Not selected'}")
        summary.append(f"<b>Folder:</b> {self.selected_folder or 'Not selected'}")
        summary.append(f"<b>Description:</b> {self.engine_description or 'None'}")
        
        self.summary_text.setHtml("<br>".join(summary))
    
    def validateCurrentPage(self) -> bool:
        """Validate each page before proceeding"""
        current_id = self.currentId()
        
        if current_id == 0:  # Folder page
            if not self.selected_folder or not self.selected_folder.exists():
                QMessageBox.warning(self, "Invalid Folder", "Please select a valid folder")
                return False
        
        elif current_id == 1:  # Executable page
            if not self.selected_executable:
                QMessageBox.warning(self, "No File Selected", "Please select an executable file")
                return False
        
        elif current_id == 2:  # Name page
            if len(self.engine_name) < 3:
                QMessageBox.warning(self, "Invalid Name", "Engine name must be at least 3 characters")
                return False
        
        elif current_id == 3:  # Description page (final)
            self.update_summary()
        
        return True
    
    def apply_styles(self):
        """Apply custom styles to wizard"""
        self.setStyleSheet(f"""
            QWizard {{
                background-color: {COLORS['darker_gray']};
            }}
            
            QWizardPage {{
                background-color: {COLORS['darker_gray']};
                color: {COLORS['white']};
            }}
            
            QLabel {{
                color: {COLORS['white']};
                font-size: 13px;
            }}
            
            QLabel#input_label {{
                font-weight: 600;
                font-size: 14px;
                margin-top: 10px;
            }}
            
            QLabel#path_label {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 10px;
                font-family: monospace;
            }}
            
            QLabel#selection_label {{
                color: {COLORS['light_green']};
                font-weight: 600;
            }}
            
            QLabel#warning_label {{
                color: {COLORS['warning_yellow']};
                background-color: rgba(243, 156, 18, 0.1);
                border-left: 3px solid {COLORS['warning_yellow']};
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
            }}
            
            QLabel#summary_label {{
                font-weight: 700;
                font-size: 15px;
                color: {COLORS['light_green']};
                margin-top: 15px;
            }}
            
            QFrame#selection_frame {{
                background-color: rgba(75, 72, 71, 0.5);
                border: 2px solid {COLORS['dark_gray']};
                border-radius: 6px;
                padding: 15px;
            }}
            
            QPushButton#browse_button {{
                background-color: {COLORS['light_green']};
                color: {COLORS['white']};
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
            }}
            
            QPushButton#browse_button:hover {{
                background-color: {COLORS['dark_green']};
            }}
            
            QListWidget#file_list {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                color: {COLORS['white']};
                font-size: 13px;
                padding: 5px;
            }}
            
            QListWidget#file_list::item {{
                padding: 8px;
                border-radius: 3px;
            }}
            
            QListWidget#file_list::item:selected {{
                background-color: {COLORS['light_green']};
            }}
            
            QLineEdit#name_input {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 10px;
                color: {COLORS['white']};
                font-size: 14px;
                font-weight: 500;
            }}
            
            QTextEdit#description_input, QTextEdit#summary_display {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 10px;
                color: {COLORS['white']};
                font-size: 13px;
            }}
            
            QTextEdit#summary_display {{
                background-color: rgba(75, 72, 71, 0.5);
            }}
        """)


class EngineCard(QFrame):
    """Visual card for displaying engine information"""
    
    delete_requested = Signal(str)
    enable_toggled = Signal(str, bool)
    
    def __init__(self, manifest: EngineManifest, parent=None):
        super().__init__(parent)
        self.manifest = manifest
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup card UI"""
        self.setObjectName("engine_card")
        self.setMinimumHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Top row: Name and actions
        top_layout = QHBoxLayout()
        
        # Engine name
        name_label = QLabel(self.manifest.name)
        name_label.setObjectName("engine_name")
        name_label.setFont(QFont("", 14, QFont.Bold))
        top_layout.addWidget(name_label)
        
        top_layout.addStretch()
        
        # Built-in badge
        if self.manifest.is_builtin:
            builtin_badge = QLabel("BUILT-IN")
            builtin_badge.setObjectName("builtin_badge")
            top_layout.addWidget(builtin_badge)
        
        # Delete button (only for custom engines)
        if not self.manifest.is_builtin:
            delete_btn = QPushButton("×")
            delete_btn.setObjectName("delete_button")
            delete_btn.setFixedSize(28, 28)
            delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.manifest.name))
            top_layout.addWidget(delete_btn)
        
        layout.addLayout(top_layout)
        
        # Description
        desc_label = QLabel(self.manifest.description or "No description available")
        desc_label.setObjectName("engine_description")
        desc_label.setWordWrap(True)
        desc_label.setMaximumHeight(45)
        layout.addWidget(desc_label)
        
        # Bottom row: Platform and path
        bottom_layout = QHBoxLayout()
        
        platform_label = QLabel(f"Platform: {self.manifest.platform.capitalize()}")
        platform_label.setObjectName("engine_info")
        bottom_layout.addWidget(platform_label)
        
        bottom_layout.addStretch()
        
        path_label = QLabel(f"Path: {self.manifest.executable}")
        path_label.setObjectName("engine_path")
        bottom_layout.addWidget(path_label)
        
        layout.addLayout(bottom_layout)
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet(f"""
            QFrame#engine_card {{
                background-color: rgba(75, 72, 71, 0.5);
                border: 2px solid {COLORS['dark_gray']};
                border-radius: 8px;
            }}
            
            QFrame#engine_card:hover {{
                border-color: {COLORS['light_green']};
            }}
            
            QLabel#engine_name {{
                color: {COLORS['light_green']};
            }}
            
            QLabel#builtin_badge {{
                background-color: {COLORS['accent_blue']};
                color: {COLORS['white']};
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 700;
            }}
            
            QLabel#engine_description {{
                color: rgba(255, 255, 255, 0.85);
                font-size: 12px;
            }}
            
            QLabel#engine_info {{
                color: {COLORS['white']};
                font-size: 11px;
                font-weight: 600;
            }}
            
            QLabel#engine_path {{
                color: rgba(255, 255, 255, 0.6);
                font-size: 10px;
                font-family: monospace;
            }}
            
            QPushButton#delete_button {{
                background-color: {COLORS['error_red']};
                color: {COLORS['white']};
                border: none;
                border-radius: 14px;
                font-size: 20px;
                font-weight: 700;
            }}
            
            QPushButton#delete_button:hover {{
                background-color: #c0392b;
            }}
        """)


class EngineStoreDialog(QDialog):
    """Main engine store dialog"""
    
    engines_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - Engine Store")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        self.engine_manager = EngineManager()
        
        self.setup_ui()
        self.apply_styles()
        self.load_engines()
    
    def setup_ui(self):
        """Setup main UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Chess Engine Store")
        title.setObjectName("store_title")
        title.setFont(QFont("", 20, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Import button
        import_btn = QPushButton("+ Import Custom Engine")
        import_btn.setObjectName("import_button")
        import_btn.setMinimumHeight(40)
        import_btn.clicked.connect(self.import_engine)
        header_layout.addWidget(import_btn)
        
        layout.addLayout(header_layout)
        
        # Subtitle
        subtitle = QLabel(
            "Manage your chess engines. Built-in engines are installed by default. "
            "Import custom UCI-compatible engines to expand your analysis options."
        )
        subtitle.setObjectName("store_subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        
        # Engines list scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("engines_scroll")
        
        scroll_content = QWidget()
        scroll_content.setObjectName("scroll_content")
        self.engines_layout = QVBoxLayout(scroll_content)
        self.engines_layout.setSpacing(10)
        self.engines_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Bottom buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("action_button")
        refresh_btn.clicked.connect(self.load_engines)
        buttons_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setObjectName("action_button")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_engines(self):
        """Load and display all engines"""
        # Clear existing cards
        while self.engines_layout.count() > 1:  # Keep stretch
            item = self.engines_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add engine cards
        for manifest in self.engine_manager.engines.values():
            card = EngineCard(manifest)
            card.delete_requested.connect(self.delete_engine)
            self.engines_layout.insertWidget(self.engines_layout.count() - 1, card)
        
        # Show message if no engines
        if not self.engine_manager.engines:
            no_engines_label = QLabel("No engines found. Import a custom engine to get started.")
            no_engines_label.setObjectName("no_engines_label")
            no_engines_label.setAlignment(Qt.AlignCenter)
            self.engines_layout.insertWidget(0, no_engines_label)
    
    def import_engine(self):
        """Open import wizard"""
        wizard = EngineImportWizard(self)
        if wizard.exec() == QWizard.Accepted:
            # Install the engine
            success = self.engine_manager.install_engine(
                wizard.selected_folder,
                wizard.selected_executable,
                wizard.engine_name,
                wizard.engine_description
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Engine '{wizard.engine_name}' installed successfully!"
                )
                self.load_engines()
                self.engines_changed.emit()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to install engine. Check console for details."
                )
    
    def delete_engine(self, engine_name: str):
        """Delete a custom engine"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{engine_name}'?\n"
            "This will permanently remove the engine files.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.engine_manager.uninstall_engine(engine_name):
                QMessageBox.information(self, "Success", "Engine deleted successfully")
                self.load_engines()
                self.engines_changed.emit()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete engine")
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['darker_gray']};
                color: {COLORS['white']};
            }}
            
            QLabel#store_title {{
                color: {COLORS['light_green']};
            }}
            
            QLabel#store_subtitle {{
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
            }}
            
            QLabel#no_engines_label {{
                color: rgba(255, 255, 255, 0.6);
                font-size: 14px;
                padding: 40px;
            }}
            
            QPushButton#import_button {{
                background-color: {COLORS['light_green']};
                color: {COLORS['white']};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 700;
                font-size: 14px;
            }}
            
            QPushButton#import_button:hover {{
                background-color: {COLORS['dark_green']};
            }}
            
            QPushButton#action_button {{
                background-color: {COLORS['dark_gray']};
                color: {COLORS['white']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            
            QPushButton#action_button:hover {{
                background-color: {COLORS['light_green']};
            }}
            
            QScrollArea#engines_scroll {{
                border: none;
                background-color: transparent;
            }}
            
            QWidget#scroll_content {{
                background-color: transparent;
            }}
            
            QScrollBar:vertical {{
                background-color: {COLORS['dark_gray']};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {COLORS['light_green']};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['dark_green']};
            }}
        """)