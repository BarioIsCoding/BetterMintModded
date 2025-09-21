"""
Main window for BetterMint Modded GUI
Enhanced with Rodent IV engine support and smooth performance monitoring
"""

import os
import sys
import json
import glob
import socket
import psutil
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QComboBox, QSlider, QFrame,
    QMessageBox, QSpacerItem, QSizePolicy, QGroupBox,
    QGridLayout, QTabWidget, QProgressBar, QSplitter,
    QFileDialog, QMenuBar, QMenu, QStatusBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSettings, QByteArray, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QAction, QFontDatabase

from .tabs import (
    EngineSettingsTab, AutoMoveSettingsTab, PremoveSettingsTab,
    VisualSettingsTab, AdvancedSettingsTab, MonitoringTab, ChessComWebView
)
from .intelligence_tab import IntelligenceTab
from settings import SettingsManager
from server import create_server
from engine import EngineChess, EnhancedIntelligentEngineManager
from constants import *

import asyncio
import uvicorn
from threading import Event

class ServerThread(QThread):
    """Thread for running the FastAPI server - FIXED VERSION"""
    status_changed = Signal(str, str)  # status, color
    performance_update = Signal(dict)  # performance data
    connection_update = Signal(list)  # connection info
    log_message = Signal(str)  # log messages

    def __init__(self, engine_configs, book_config, tablebase_config, settings_manager):
        super().__init__()
        self.engine_configs = engine_configs
        self.book_config = book_config
        self.tablebase_config = tablebase_config
        self.settings_manager = settings_manager
        self.engines = []
        self.running = False
        self.server = None
        self.stop_event = Event()
        self.connections = {}
        self.connection_counter = 0

    def update_engines(self, new_configs):
        """Update engine configurations on the fly"""
        # Stop old engines
        for engine in self.engines:
            engine.quit()
        
        self.engines.clear()
        self.engine_configs = new_configs
        
        # Start new engines
        for config in self.engine_configs:
            try:
                engine = EngineChess(
                    config['path'],
                    is_maia=config['is_maia'],
                    maia_config=config['config'],
                    book_config=self.book_config,
                    tablebase_config=self.tablebase_config,
                    intelligence_settings=self.settings_manager.get_intelligence_settings()
                )
                # CRITICAL FIX: Initialize the engine regardless of type
                engine.initialize_engine()
                self.engines.append(engine)
                self.log_message.emit(f"Loaded and initialized engine: {config['name']}")
            except Exception as e:
                self.log_message.emit(f"Failed to load engine {config['name']}: {e}")

    def is_port_available(self, port):
        """Check if port is available"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', port))
            return result != 0

    def run(self):
        # Initialize engines
        for config in self.engine_configs:
            try:
                engine = EngineChess(
                    config['path'],
                    is_maia=config['is_maia'],
                    maia_config=config['config'],
                    book_config=self.book_config,
                    tablebase_config=self.tablebase_config,
                    intelligence_settings=self.settings_manager.get_intelligence_settings()
                )
                self.engines.append(engine)
                self.log_message.emit(f"Loaded engine: {config['name']}")
                
                # CRITICAL FIX: Initialize ALL engines, not just Maia
                # The engine.initialize_engine() method will be called automatically
                # in the new __init__, but we can also call it explicitly here
                engine.initialize_engine()
                self.log_message.emit(f"Initialized engine: {config['name']}")
                
            except Exception as e:
                self.log_message.emit(f"Failed to load engine {config['name']}: {e}")
                continue

        # Check port availability
        if not self.is_port_available(DEFAULT_PORT):
            self.status_changed.emit(f"Port {DEFAULT_PORT} in use", COLORS['error_red'])
            self.log_message.emit(f"ERROR: Port {DEFAULT_PORT} is already in use")
            return

        # Create server
        from server import create_server
        server = create_server(
            engines=self.engines,
            engine_configs=self.engine_configs,
            settings_manager=self.settings_manager,
            connection_update_callback=lambda x: self.connection_update.emit(x),
            log_callback=lambda x: self.log_message.emit(x)
        )

        # Start server with proper async handling
        try:
            self.running = True
            self.stop_event.clear()
            self.status_changed.emit("Running", COLORS['success_green'])
            
            config = uvicorn.Config(
                app=server.get_app(),
                host=DEFAULT_HOST,
                port=DEFAULT_PORT,
                log_level="error",
                loop="asyncio"
            )
            self.server = uvicorn.Server(config)
            
            # Run server in async context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def serve():
                await self.server.serve()
            
            # Monitor for stop signal
            async def monitor_stop():
                while not self.stop_event.is_set():
                    await asyncio.sleep(0.1)
                await self.server.shutdown()
            
            loop.create_task(serve())
            loop.create_task(monitor_stop())
            loop.run_forever()
            
        except Exception as e:
            self.log_message.emit(f"Server error: {e}")
            self.running = False
            self.status_changed.emit("Error", COLORS['error_red'])
        finally:
            # Cleanup
            loop.close()
            for engine in self.engines:
                engine.quit()
            self.running = False

    def stop(self):
        """Properly stop the server"""
        self.stop_event.set()
        self.running = False


class SmoothProgressBar(QProgressBar):
    """Enhanced progress bar with smooth interpolation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.target_value = 0
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(800)  # 800ms for smooth transition
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def setValueSmooth(self, value):
        """Set value with smooth animation"""
        if value == self.value():
            return
            
        self.target_value = value
        self.animation.stop()
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(value)
        self.animation.start()
    
    def setValueInstant(self, value):
        """Set value without animation"""
        self.animation.stop()
        self.setValue(value)
        self.target_value = value


class ChessEngineGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - Advanced Chess Engine Manager")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.set_window_icon()
        
        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        # Load custom font
        self.load_custom_font()

        # Initialize settings manager
        self.settings_manager = SettingsManager()

        # Server thread
        self.server_thread = None
        self.server_running = False

        # Performance monitoring with smoothing
        self.performance_data = []
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self.update_performance_metrics)
        
        # Previous values for smooth interpolation
        self.prev_cpu_percent = 0.0
        self.prev_memory_percent = 0.0
        self.prev_memory_mb = 0.0
        
        # Connection update timer
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.request_connection_update)
        self.connection_timer.start(CONNECTION_UPDATE_INTERVAL)

        self.setup_ui()
        self.apply_styles()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.load_gui_settings()
        
        # Initialize performance monitoring if enabled
        if self.settings_manager.get_setting("performance-monitoring", False):
            self.performance_widget.setVisible(True)
            self.performance_timer.start(PERFORMANCE_UPDATE_INTERVAL)

    def set_window_icon(self):
        """Set the main window icon using centralized constants"""
        try:
            from PySide6.QtGui import QIcon
            from PySide6.QtCore import QSize
            from constants import ICON_DIR, ICON_FILES
            
            icon = QIcon()
            icon_loaded = False
            
            for icon_file in ICON_FILES:
                icon_path = ICON_DIR / icon_file
                if icon_path.exists():
                    print(f"Loading window icon: {icon_path}")
                    
                    # For sized PNG files, add with specific size
                    if icon_file.startswith("icon-") and icon_file.endswith(".png"):
                        try:
                            size_str = icon_file.replace("icon-", "").replace(".png", "")
                            size = int(size_str)
                            icon.addFile(str(icon_path), QSize(size, size))
                            icon_loaded = True
                        except ValueError:
                            icon.addFile(str(icon_path))
                            icon_loaded = True
                    else:
                        icon.addFile(str(icon_path))
                        icon_loaded = True
            
            if icon_loaded and not icon.isNull():
                self.setWindowIcon(icon)
                print("Window icon set successfully")
            else:
                print("No valid window icon found")
                
        except Exception as e:
            print(f"Error setting window icon: {e}")

    def load_custom_font(self):
        """Load Montserrat font from file"""
        try:
            font_path = os.path.join(os.path.dirname(__file__), "..", "Montserrat.ttf")
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    if font_families:
                        font = QFont(font_families[0])
                        QApplication.setFont(font)
                        print(f"Loaded custom font: {font_families[0]}")
                else:
                    print("Failed to load Montserrat font, using system default")
            else:
                print(f"Font file not found: {font_path}")
                # Try to use system Montserrat if available
                font = QFont("Montserrat")
                if font.family() == "Montserrat":
                    QApplication.setFont(font)
        except Exception as e:
            print(f"Error loading custom font: {e}")

    def setup_menu_bar(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu('File')

        new_profile_action = QAction('New Profile', self)
        new_profile_action.triggered.connect(self.new_profile)
        file_menu.addAction(new_profile_action)

        load_profile_action = QAction('Load Profile', self)
        load_profile_action.triggered.connect(self.load_profile)
        file_menu.addAction(load_profile_action)

        save_profile_action = QAction('Save Profile', self)
        save_profile_action.triggered.connect(self.save_profile)
        file_menu.addAction(save_profile_action)

        file_menu.addSeparator()

        export_action = QAction('Export Settings', self)
        export_action.triggered.connect(self.export_settings)
        file_menu.addAction(export_action)

        import_action = QAction('Import Settings', self)
        import_action.triggered.connect(self.import_settings)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Server Menu
        server_menu = menubar.addMenu('Server')

        start_action = QAction('Start Server', self)
        start_action.triggered.connect(self.start_server)
        server_menu.addAction(start_action)

        stop_action = QAction('Stop Server', self)
        stop_action.triggered.connect(self.stop_server)
        server_menu.addAction(stop_action)

        server_menu.addSeparator()

        open_web_action = QAction('Open Web Interface', self)
        open_web_action.triggered.connect(lambda: os.system(f"start http://{DEFAULT_HOST}:{DEFAULT_PORT}"))
        server_menu.addAction(open_web_action)

        # Tools Menu
        tools_menu = menubar.addMenu('Tools')

        performance_action = QAction('Performance Monitor', self)
        performance_action.setCheckable(True)
        performance_action.setChecked(self.settings_manager.get_setting("performance-monitoring", False))
        performance_action.triggered.connect(self.toggle_performance_monitoring)
        tools_menu.addAction(performance_action)

        clear_logs_action = QAction('Clear Logs', self)
        clear_logs_action.triggered.connect(self.clear_logs)
        tools_menu.addAction(clear_logs_action)

        # Help Menu
        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_status_bar(self):
        self.status_bar = self.statusBar()

        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # Server status
        self.server_status_label = QLabel("Server: Stopped")
        self.status_bar.addPermanentWidget(self.server_status_label)

        # Connection count
        self.connection_count_label = QLabel("Connections: 0")
        self.status_bar.addPermanentWidget(self.connection_count_label)

    def setup_ui(self):
        # Central widget with main splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        # Left panel - Engine and Server controls
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)

        # Right panel - Settings tabs
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)

        # Set splitter sizes (25% left, 75% right)
        main_splitter.setSizes([350, 1050])

    def create_left_panel(self):
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)

        # Title
        title_label = QLabel(APP_NAME)
        title_label.setObjectName("main_title")
        title_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title_label)

        # Engine Selection
        self.setup_engine_section(left_layout)

        # Server Status
        self.setup_server_status_section(left_layout)

        # Control Buttons
        self.setup_control_buttons(left_layout)

        # Performance Monitor (initially visible if enabled)
        self.performance_widget = self.create_performance_widget()
        self.performance_widget.setVisible(
            self.settings_manager.get_setting("performance-monitoring", False)
        )
        left_layout.addWidget(self.performance_widget)

        left_layout.addStretch()
        return left_widget

    def create_right_panel(self):
        # Create tabbed settings interface
        self.settings_tabs = QTabWidget()
        self.settings_tabs.setObjectName("settings_tabs")

        # Chess.com Tab (First)
        self.chess_com_tab = ChessComWebView()
        self.settings_tabs.addTab(self.chess_com_tab, "Chess.com")

        # Engine Settings Tab
        self.engine_settings_tab = EngineSettingsTab(self.settings_manager)
        self.settings_tabs.addTab(self.engine_settings_tab, "Engine")

        # Auto-Move Settings Tab
        self.automove_settings_tab = AutoMoveSettingsTab(self.settings_manager)
        self.automove_settings_tab.settings_changed.connect(self.on_automove_settings_changed)
        self.settings_tabs.addTab(self.automove_settings_tab, "Auto-Move")

        # Premove Settings Tab
        self.premove_settings_tab = PremoveSettingsTab(self.settings_manager)
        self.settings_tabs.addTab(self.premove_settings_tab, "Premoves")

        # Visual Settings Tab
        self.visual_settings_tab = VisualSettingsTab(self.settings_manager)
        self.settings_tabs.addTab(self.visual_settings_tab, "Visual")

        # Intelligence Tab (New)
        self.intelligence_tab = IntelligenceTab(self.settings_manager)
        self.intelligence_tab.settings_changed.connect(self.on_intelligence_settings_changed)
        self.settings_tabs.addTab(self.intelligence_tab, "Intelligence")

        # Advanced Settings Tab
        self.advanced_settings_tab = AdvancedSettingsTab(self.settings_manager)
        self.advanced_settings_tab.performance_monitoring_changed.connect(self.toggle_performance_monitoring)
        self.settings_tabs.addTab(self.advanced_settings_tab, "Advanced")

        # Monitoring Tab
        self.monitoring_tab = MonitoringTab(self.settings_manager)
        self.settings_tabs.addTab(self.monitoring_tab, "Monitor")

        return self.settings_tabs

    def setup_engine_section(self, layout):
        engine_group = QGroupBox("Chess Engines")
        engine_group.setObjectName("group_box")

        engine_layout = QVBoxLayout(engine_group)
        engine_layout.setSpacing(10)

        # Stockfish
        self.stockfish_frame = self.create_engine_option(
            "Stockfish", "World's strongest engine", self.check_stockfish_available()
        )
        engine_layout.addWidget(self.stockfish_frame)

        # Rodent IV - NEW ENGINE SUPPORT
        self.rodent_frame = self.create_engine_option(
            "Rodent IV", "Personality-based engine", self.check_rodent_available()
        )
        engine_layout.addWidget(self.rodent_frame)

        # Leela Chess Zero
        self.leela_frame = self.create_engine_option(
            "Leela Chess Zero", "Neural network engine", self.check_leela_available()
        )
        engine_layout.addWidget(self.leela_frame)

        # Maia configuration
        self.setup_maia_options(engine_layout)

        layout.addWidget(engine_group)

    def create_engine_option(self, name, description, available):
        frame = QFrame()
        frame.setObjectName("engine_option")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)

        # Top row
        top_layout = QHBoxLayout()

        checkbox = QCheckBox(name)
        checkbox.setObjectName("engine_checkbox")
        checkbox.setEnabled(available)

        if name == "Stockfish":
            self.stockfish_checkbox = checkbox
            checkbox.toggled.connect(self.on_engine_config_changed)
        elif name == "Rodent IV":
            self.rodent_checkbox = checkbox
            checkbox.toggled.connect(self.on_engine_config_changed)
        elif name == "Leela Chess Zero":
            self.leela_checkbox = checkbox
            checkbox.toggled.connect(self.on_leela_toggle)

        top_layout.addWidget(checkbox)
        top_layout.addStretch()

        status_label = QLabel("Available" if available else "Not Found")
        status_label.setObjectName("status_available" if available else "status_unavailable")
        top_layout.addWidget(status_label)

        layout.addLayout(top_layout)

        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("description")
        layout.addWidget(desc_label)

        return frame

    def setup_maia_options(self, layout):
        self.maia_frame = QFrame()
        self.maia_frame.setObjectName("maia_frame")
        self.maia_frame.setVisible(False)

        maia_layout = QVBoxLayout(self.maia_frame)
        maia_layout.setContentsMargins(15, 10, 15, 10)

        self.maia_checkbox = QCheckBox("Enable Maia (Human-like)")
        self.maia_checkbox.setObjectName("maia_checkbox")
        self.maia_checkbox.toggled.connect(self.on_maia_toggle)
        maia_layout.addWidget(self.maia_checkbox)

        # Maia config frame
        self.maia_config_frame = QFrame()
        self.maia_config_frame.setObjectName("maia_config")
        self.maia_config_frame.setVisible(False)

        config_layout = QVBoxLayout(self.maia_config_frame)
        config_layout.setContentsMargins(10, 10, 10, 10)

        # Strength selection
        strength_label = QLabel("Maia Strength:")
        strength_label.setObjectName("config_label")
        config_layout.addWidget(strength_label)

        self.strength_combo = QComboBox()
        self.strength_combo.setObjectName("strength_combo")
        self.strength_combo.currentTextChanged.connect(self.on_engine_config_changed)
        available_weights = self.get_available_maia_weights()
        if available_weights:
            self.strength_combo.addItems(available_weights)
        else:
            self.strength_combo.addItem("No weights found")
            self.strength_combo.setEnabled(False)
        config_layout.addWidget(self.strength_combo)

        # Nodes per second
        nodes_label = QLabel("Playing Speed (Nodes/sec):")
        nodes_label.setObjectName("config_label")
        config_layout.addWidget(nodes_label)

        nodes_layout = QHBoxLayout()
        self.nodes_slider = QSlider(Qt.Horizontal)
        self.nodes_slider.setObjectName("nodes_slider")
        self.nodes_slider.setMinimum(1)
        self.nodes_slider.setMaximum(1000)
        self.nodes_slider.setValue(1)
        self.nodes_slider.valueChanged.connect(self.update_nodes_display)
        self.nodes_slider.sliderReleased.connect(self.on_engine_config_changed)

        self.nodes_display = QLabel("0.001")
        self.nodes_display.setObjectName("nodes_display")
        self.nodes_display.setMinimumWidth(60)

        nodes_layout.addWidget(self.nodes_slider, 1)
        nodes_layout.addWidget(self.nodes_display)
        config_layout.addLayout(nodes_layout)

        maia_layout.addWidget(self.maia_config_frame)
        layout.addWidget(self.maia_frame)

    def setup_server_status_section(self, layout):
        status_group = QGroupBox("Server Status")
        status_group.setObjectName("group_box")

        status_layout = QVBoxLayout(status_group)

        self.status_label_local = QLabel("Server: Stopped")
        self.status_label_local.setObjectName("status_stopped")
        status_layout.addWidget(self.status_label_local)

        self.engines_label = QLabel("Active Engines: 0")
        self.engines_label.setObjectName("status_info")
        status_layout.addWidget(self.engines_label)

        self.connections_label = QLabel("Connections: 0")
        self.connections_label.setObjectName("status_info")
        status_layout.addWidget(self.connections_label)

        layout.addWidget(status_group)

    def setup_control_buttons(self, layout):
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)

        self.start_button = QPushButton("START SERVER")
        self.start_button.setObjectName("start_button")
        self.start_button.setMinimumHeight(45)
        self.start_button.clicked.connect(self.start_server)

        self.stop_button = QPushButton("STOP SERVER")
        self.stop_button.setObjectName("stop_button")
        self.stop_button.setMinimumHeight(45)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_server)

        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)

        layout.addLayout(buttons_layout)

    def create_performance_widget(self):
        perf_group = QGroupBox("Performance Monitor")
        perf_group.setObjectName("group_box")

        perf_layout = QVBoxLayout(perf_group)

        self.cpu_progress = QProgressBar()
        self.cpu_progress.setObjectName("progress_bar")
        self.cpu_label = QLabel("CPU: 0%")
        perf_layout.addWidget(self.cpu_label)
        perf_layout.addWidget(self.cpu_progress)

        self.memory_progress = QProgressBar()
        self.memory_progress.setObjectName("progress_bar")
        self.memory_label = QLabel("Memory: 0 MB")
        perf_layout.addWidget(self.memory_label)
        perf_layout.addWidget(self.memory_progress)

        return perf_group

    def apply_styles(self):
        # Import the complete stylesheet from the original main.py
        # This is a large block but needs to be preserved exactly
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['darker_gray']};
                color: {COLORS['white']};
                font-family: 'Montserrat'
                , -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}

            QTabWidget#settings_tabs {{
                background-color: transparent;
                border: none;
            }}

            QTabWidget#settings_tabs::pane {{
                background-color: transparent;
                border: none;
                padding: 10px;
            }}

            QTabWidget#settings_tabs::tab-bar {{
                alignment: center;
            }}

            QTabBar::tab {{
                background-color: {COLORS['dark_gray']};
                color: {COLORS['white']};
                padding: 12px 20px;
                margin: 2px;
                border-radius: 6px 6px 0px 0px;
                font-weight: 600;
                font-size: 13px;
                min-width: 80px;
            }}

            QTabBar::tab:selected {{
                background-color: {COLORS['light_green']};
                color: {COLORS['white']};
            }}

            QTabBar::tab:hover {{
                background-color: {COLORS['dark_green']};
            }}

            QGroupBox#group_box, QGroupBox#settings_group {{
                font-weight: 600;
                font-size: 14px;
                color: {COLORS['white']};
                border: 2px solid {COLORS['dark_gray']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: rgba(75, 72, 71, 0.3);
            }}

            QGroupBox#group_box::title, QGroupBox#settings_group::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: {COLORS['light_green']};
                background-color: {COLORS['darker_gray']};
                font-size: 14px;
            }}

            QLabel#main_title {{
                font-size: 26px;
                font-weight: 700;
                color: {COLORS['light_green']};
                margin: 10px 0;
                letter-spacing: 1px;
            }}

            QFrame#engine_option {{
                background-color: rgba(75, 72, 71, 0.5);
                border: 1px solid {COLORS['dark_gray']};
                border-radius: 6px;
                margin: 2px;
            }}

            QCheckBox {{
                font-weight: 500;
                color: {COLORS['white']};
                spacing: 8px;
                font-size: 13px;
            }}

            QCheckBox#engine_checkbox, QCheckBox#maia_checkbox, QCheckBox#intelligence_checkbox {{
                font-weight: 600;
                font-size: 14px;
            }}

            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {COLORS['white']};
                background-color: transparent;
            }}

            QCheckBox::indicator:checked {{
                background-color: {COLORS['light_green']};
                border-color: {COLORS['light_green']};
            }}

            QLabel#status_available {{
                color: {COLORS['success_green']};
                font-weight: 600;
                font-size: 12px;
            }}

            QLabel#status_unavailable {{
                color: {COLORS['error_red']};
                font-weight: 600;
                font-size: 12px;
            }}

            QLabel#description {{
                color: rgba(255, 255, 255, 0.8);
                font-size: 12px;
                margin-top: 2px;
            }}

            QLabel#config_label, QLabel#intelligence_label {{
                color: {COLORS['white']};
                font-weight: 600;
                margin-bottom: 5px;
                font-size: 13px;
            }}

            QLabel#value_display {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS['white']};
                font-weight: 600;
                text-align: center;
                font-size: 13px;
            }}

            QLabel#note_label {{
                color: {COLORS['warning_yellow']};
                font-size: 11px;
                font-style: italic;
            }}

            QLabel#info_label {{
                background-color: rgba(52, 152, 219, 0.1);
                border: 1px solid {COLORS['accent_blue']};
                border-radius: 4px;
                padding: 10px;
                color: {COLORS['white']};
                font-size: 12px;
            }}

            QLabel {{
                color: {COLORS['white']};
                font-size: 13px;
            }}

            QComboBox {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS['white']};
                font-weight: 500;
                font-size: 13px;
                min-height: 20px;
            }}

            QComboBox::drop-down {{
                border: none;
                width: 25px;
            }}

            QComboBox::down-arrow {{
                image: none;
                border: 4px solid transparent;
                border-top: 8px solid {COLORS['white']};
                margin-right: 8px;
            }}

            QComboBox QAbstractItemView {{
                background-color: {COLORS['dark_gray']};
                color: {COLORS['white']};
                selection-background-color: {COLORS['light_green']};
                border: 1px solid {COLORS['light_green']};
                font-size: 13px;
            }}

            QSlider#nodes_slider, QSlider#intelligence_slider {{
                height: 25px;
            }}

            QSlider#nodes_slider::groove:horizontal, QSlider#intelligence_slider::groove:horizontal {{
                background: {COLORS['dark_gray']};
                height: 6px;
                border-radius: 3px;
            }}

            QSlider#nodes_slider::handle:horizontal, QSlider#intelligence_slider::handle:horizontal {{
                background: {COLORS['light_green']};
                width: 20px;
                height: 20px;
                border-radius: 10px;
                margin: -7px 0;
            }}

            QSlider#nodes_slider::handle:horizontal:hover, QSlider#intelligence_slider::handle:horizontal:hover {{
                background: {COLORS['dark_green']};
            }}

            QLabel#nodes_display {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS['white']};
                font-weight: 600;
                text-align: center;
                font-size: 13px;
            }}

            QLabel#status_stopped {{
                color: {COLORS['error_red']};
                font-weight: 600;
                font-size: 14px;
            }}

            QLabel#status_running {{
                color: {COLORS['success_green']};
                font-weight: 600;
                font-size: 14px;
            }}

            QLabel#status_info {{
                color: rgba(255, 255, 255, 0.9);
                font-weight: 500;
                font-size: 13px;
            }}

            QPushButton#start_button {{
                background-color: {COLORS['success_green']};
                color: {COLORS['white']};
                border: none;
                border-radius: 6px;
                font-weight: 700;
                font-size: 14px;
                letter-spacing: 0.5px;
            }}

            QPushButton#start_button:hover {{
                background-color: #229954;
            }}

            QPushButton#start_button:pressed {{
                background-color: #1e7e34;
            }}

            QPushButton#start_button:disabled {{
                background-color: rgba(102, 102, 102, 0.5);
                color: rgba(153, 153, 153, 0.8);
            }}

            QPushButton#stop_button {{
                background-color: {COLORS['error_red']};
                color: {COLORS['white']};
                border: none;
                border-radius: 6px;
                font-weight: 700;
                font-size: 14px;
                letter-spacing: 0.5px;
            }}

            QPushButton#stop_button:hover {{
                background-color: #c0392b;
            }}

            QPushButton#stop_button:pressed {{
                background-color: #a93226;
            }}

            QPushButton#stop_button:disabled {{
                background-color: rgba(102, 102, 102, 0.5);
                color: rgba(153, 153, 153, 0.8);
            }}

            QSpinBox, QDoubleSpinBox {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 6px;
                color: {COLORS['white']};
                font-weight: 500;
                font-size: 13px;
                min-height: 20px;
            }}

            QSpinBox::up-button, QSpinBox::down-button,
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background-color: {COLORS['light_green']};
                width: 20px;
            }}

            QSpinBox::up-button:hover, QSpinBox::down-button:hover,
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: {COLORS['dark_green']};
            }}

            QLineEdit {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS['white']};
                font-weight: 500;
                font-size: 13px;
            }}

            QLineEdit:focus {{
                border-color: {COLORS['dark_green']};
            }}

            QProgressBar#progress_bar {{
                border: 2px solid {COLORS['dark_gray']};
                border-radius: 4px;
                text-align: center;
                color: {COLORS['white']};
                font-weight: 600;
                font-size: 12px;
                background-color: rgba(75, 72, 71, 0.5);
            }}

            QProgressBar#progress_bar::chunk {{
                background-color: {COLORS['light_green']};
                border-radius: 2px;
            }}

            QTableWidget {{
                background-color: rgba(75, 72, 71, 0.5);
                border: 2px solid {COLORS['dark_gray']};
                border-radius: 4px;
                color: {COLORS['white']};
                gridline-color: {COLORS['darker_gray']};
                font-size: 12px;
            }}

            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid rgba(75, 72, 71, 0.3);
            }}

            QTableWidget::item:selected {{
                background-color: {COLORS['light_green']};
            }}

            QHeaderView::section {{
                background-color: {COLORS['dark_gray']};
                color: {COLORS['white']};
                padding: 8px;
                border: none;
                font-weight: 600;
                font-size: 12px;
            }}

            QTextEdit#activity_log {{
                background-color: rgba(75, 72, 71, 0.5);
                border: 2px solid {COLORS['dark_gray']};
                border-radius: 4px;
                color: {COLORS['white']};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 8px;
            }}

            QPushButton {{
                background-color: {COLORS['light_green']};
                color: {COLORS['white']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
            }}

            QPushButton:hover {{
                background-color: {COLORS['dark_green']};
            }}

            QPushButton:pressed {{
                background-color: {COLORS['dark_green']};
            }}

            QStatusBar {{
                background-color: {COLORS['dark_gray']};
                color: {COLORS['white']};
                border-top: 1px solid {COLORS['light_green']};
                font-size: 12px;
            }}

            QMenuBar {{
                background-color: {COLORS['dark_gray']};
                color: {COLORS['white']};
                border-bottom: 1px solid {COLORS['light_green']};
                font-size: 13px;
            }}

            QMenuBar::item {{
                background-color: transparent;
                padding: 8px 12px;
            }}

            QMenuBar::item:selected {{
                background-color: {COLORS['light_green']};
            }}

            QMenu {{
                background-color: {COLORS['dark_gray']};
                color: {COLORS['white']};
                border: 1px solid {COLORS['light_green']};
                font-size: 13px;
            }}

            QMenu::item {{
                padding: 8px 20px;
            }}

            QMenu::item:selected {{
                background-color: {COLORS['light_green']};
            }}

            QSplitter::handle {{
                background-color: {COLORS['dark_gray']};
                width: 2px;
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

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollArea#settings_scroll_area {{
                background-color: #2c2b29;  /* or your COLORS['darker_gray'] value */
            }}

            QWidget#settings_scroll_content {{
                background-color: #2c2b29;  /* match the scroll area */
            }}
                        
            QFrame#sub_setting_frame {{
                background-color: rgba(75, 72, 71, 0.2);
                border-left: 3px solid {COLORS['light_green']};
                border-radius: 4px;
            }}
        """)

    # Event handlers and utility methods
    def update_nodes_display(self, value):
        nodes_value = value / 1000.0
        self.nodes_display.setText(f"{nodes_value:.3f}")

    def on_leela_toggle(self, checked):
        self.maia_frame.setVisible(checked)
        if not checked:
            self.maia_checkbox.setChecked(False)
        self.on_engine_config_changed()

    def on_maia_toggle(self, checked):
        self.maia_config_frame.setVisible(checked)
        self.on_engine_config_changed()

    def on_engine_config_changed(self):
        """Update engines when configuration changes"""
        if self.server_running and self.server_thread:
            selected_engines = self.get_selected_engines()
            if selected_engines:
                self.server_thread.update_engines(selected_engines)
                self.monitoring_tab.log_activity("Engine configuration updated")

    def on_automove_settings_changed(self):
        """Handle auto-move settings change"""
        # Update intelligence tab about auto-move status
        auto_move_enabled = self.settings_manager.get_setting("legit-auto-move", False)
        self.intelligence_tab.update_auto_move_status(auto_move_enabled)

    def on_intelligence_settings_changed(self):
        """Handle intelligence settings change"""
        if self.server_running and self.server_thread:
            # Engines will use the updated settings via settings_manager
            self.monitoring_tab.log_activity("Intelligence settings updated")

    def get_selected_engines(self):
        """Get currently selected engine configurations"""
        selected_engines = []

        # Stockfish
        if hasattr(self, 'stockfish_checkbox') and self.stockfish_checkbox.isChecked():
            if self.check_stockfish_available():
                selected_engines.append({
                    'path': STOCKFISH_PATH,
                    'is_maia': False,
                    'config': {},
                    'name': 'Stockfish'
                })

        # Rodent IV - NEW ENGINE SUPPORT
        if hasattr(self, 'rodent_checkbox') and self.rodent_checkbox.isChecked():
            if self.check_rodent_available():
                selected_engines.append({
                    'path': RODENT_PATH,
                    'is_maia': False,
                    'config': {},
                    'name': 'Rodent IV'
                })

        # Leela Chess Zero
        if hasattr(self, 'leela_checkbox') and self.leela_checkbox.isChecked():
            if self.check_leela_available():
                config = {}
                if hasattr(self, 'maia_checkbox') and self.maia_checkbox.isChecked():
                    strength = self.strength_combo.currentText()
                    weights_path = MAIA_WEIGHTS_PATH.format(strength)
                    if os.path.exists(weights_path):
                        nodes_value = self.nodes_slider.value() / 1000.0
                        config = {
                            'weights_file': weights_path,
                            'nodes_per_second_limit': nodes_value,
                            'use_slowmover': False
                        }

                engine_name = "Leela"
                if hasattr(self, 'maia_checkbox') and self.maia_checkbox.isChecked():
                    engine_name += f" + Maia {self.strength_combo.currentText()}"

                selected_engines.append({
                    'path': LEELA_PATH,
                    'is_maia': hasattr(self, 'maia_checkbox') and self.maia_checkbox.isChecked(),
                    'config': config,
                    'name': engine_name
                })

        return selected_engines

    def check_stockfish_available(self):
        return os.path.exists(STOCKFISH_PATH)

    def check_rodent_available(self):
        """Check if Rodent IV engine is available"""
        return os.path.exists(RODENT_PATH)

    def check_leela_available(self):
        return os.path.exists(LEELA_PATH)

    def get_available_maia_weights(self):
        weights = []
        for i in range(1100, 2000, 100):
            pattern = MAIA_WEIGHTS_PATH.format(i)
            if os.path.exists(pattern):
                weights.append(str(i))
        return weights

    def toggle_performance_monitoring(self, enabled):
        self.settings_manager.set_setting("performance-monitoring", enabled)
        self.performance_widget.setVisible(enabled)
        if enabled:
            self.performance_timer.start(PERFORMANCE_UPDATE_INTERVAL)
            self.monitoring_tab.log_activity("Performance monitoring enabled")
        else:
            self.performance_timer.stop()
            self.monitoring_tab.log_activity("Performance monitoring disabled")

    def update_performance_metrics(self):
        # Get real performance metrics
        try:
            cpu_percent = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            memory_mb = memory_info.used / (1024 * 1024)

            self.cpu_progress.setValue(int(cpu_percent))
            self.cpu_label.setText(f"CPU: {cpu_percent:.1f}%")

            self.memory_progress.setValue(int(memory_info.percent))
            self.memory_label.setText(f"Memory: {memory_mb:.0f} MB")

        except Exception as e:
            print(f"Error updating performance metrics: {e}")

    def request_connection_update(self):
        """Request connection info update from server thread"""
        # Connection info will be sent via signal from server thread
        pass

    def start_server(self):
        selected_engines = self.get_selected_engines()

        if not selected_engines:
            QMessageBox.warning(self, "Warning", "Please select at least one engine")
            return

        book_config = {}
        tablebase_config = {}

        try:
            self.server_thread = ServerThread(selected_engines, book_config, tablebase_config, self.settings_manager)
            self.server_thread.status_changed.connect(self.on_server_status_changed)
            self.server_thread.connection_update.connect(self.monitoring_tab.update_connection_table)
            self.server_thread.log_message.connect(self.monitoring_tab.log_activity)
            self.server_thread.start()

            self.server_running = True

            # Update UI
            self.status_label_local.setText("Server: Starting...")
            self.status_label_local.setObjectName("status_running")
            self.engines_label.setText(f"Active Engines: {len(selected_engines)}")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            self.monitoring_tab.log_activity(f"Server started with {len(selected_engines)} engines")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start server: {str(e)}")
            self.server_running = False

    def stop_server(self):
        if self.server_thread and self.server_thread.isRunning():
            self.server_thread.stop()
            self.server_thread.wait(5000)  # Wait up to 5 seconds for clean shutdown
            
            if self.server_thread.isRunning():
                self.server_thread.terminate()
                self.server_thread.wait()

        self.server_running = False

        self.status_label_local.setText("Server: Stopped")
        self.status_label_local.setObjectName("status_stopped")
        self.engines_label.setText("Active Engines: 0")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self.monitoring_tab.log_activity("Server stopped")
        
        # Clear connection table
        self.monitoring_tab.connection_table.setRowCount(0)
        self.connections_label.setText("Connections: 0")
        self.connection_count_label.setText("Connections: 0")

    def on_server_status_changed(self, status, color):
        self.status_label_local.setText(f"Server: {status}")
        self.server_status_label.setText(f"Server: {status}")
        
        if status == "Running":
            self.status_label_local.setObjectName("status_running")
        else:
            self.status_label_local.setObjectName("status_stopped")
        
        # Re-apply styles to update colors
        self.status_label_local.style().unpolish(self.status_label_local)
        self.status_label_local.style().polish(self.status_label_local)

    # Menu actions
    def new_profile(self):
        self.settings_manager.settings = self.settings_manager.default_settings.copy()
        self.load_gui_settings()
        self.monitoring_tab.log_activity("New profile created")

    def load_profile(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Profile", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    profile_data = json.load(f)
                self.settings_manager.settings.update(profile_data)
                self.load_gui_settings()
                self.monitoring_tab.log_activity(f"Profile loaded from {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load profile: {str(e)}")

    def save_profile(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Profile", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.settings_manager.settings, f, indent=2)
                self.monitoring_tab.log_activity(f"Profile saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save profile: {str(e)}")

    def export_settings(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Settings", "betterMint_export.json", "JSON Files (*.json)")
        if file_path:
            if self.settings_manager.export_settings(file_path):
                self.monitoring_tab.log_activity(f"Settings exported to {file_path}")
                QMessageBox.information(self, "Success", "Settings exported successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to export settings")

    def import_settings(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Settings", "", "JSON Files (*.json)")
        if file_path:
            if self.settings_manager.import_settings(file_path):
                self.load_gui_settings()
                self.monitoring_tab.log_activity(f"Settings imported from {file_path}")
                QMessageBox.information(self, "Success", "Settings imported successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to import settings")

    def clear_logs(self):
        self.monitoring_tab.activity_log.clear()

    def show_about(self):
        QMessageBox.about(self, f"About {APP_NAME}",
                         f"{APP_NAME} v{APP_VERSION}\n\n"
                         "Advanced Chess Analysis Tool\n"
                         "Server-side managed settings\n"
                         "Intelligent engine behavior\n\n"
                         "Enhanced by Claude AI\n"
                         f"Original BetterMint by {APP_ORGANIZATION}")

    def load_gui_settings(self):
        """Load all settings into GUI elements"""
        # Load settings for all tabs
        self.engine_settings_tab.load_settings()
        self.automove_settings_tab.load_settings()
        self.premove_settings_tab.load_settings()
        self.visual_settings_tab.load_settings()
        self.advanced_settings_tab.load_settings()
        self.intelligence_tab.load_settings()

    def closeEvent(self, event):
        if self.server_running:
            self.stop_server()

        # Save window state
        settings = QSettings(APP_ORGANIZATION, APP_NAME)
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        print("Made with <3 by Bqrio and Claude")
        event.accept()
