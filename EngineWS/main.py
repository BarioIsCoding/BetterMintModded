import os
import sys
import subprocess
import asyncio
import json
import time
import glob
from datetime import datetime
from threading import Thread, Lock
from queue import Queue, Empty
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QComboBox, QSlider, QFrame,
    QMessageBox, QSpacerItem, QSizePolicy, QScrollArea, QGroupBox,
    QGridLayout, QTextEdit, QTabWidget, QSpinBox, QLineEdit,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QFileDialog, QMenuBar, QMenu, QStatusBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSettings
from PySide6.QtGui import QFont, QPixmap, QAction, QIcon

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketState
from pydantic import BaseModel
from typing import Dict, Any, List

# Chess.com inspired color scheme
COLORS = {
    'white': '#ffffff',
    'light_green': '#69923e',
    'dark_green': '#4e7837',
    'dark_gray': '#4b4847',
    'darker_gray': '#2c2b29',
    'accent_blue': '#3498db',
    'accent_orange': '#e67e22',
    'success_green': '#27ae60',
    'warning_yellow': '#f39c12',
    'error_red': '#e74c3c'
}

# Settings model for API
class Settings(BaseModel):
    settings: Dict[str, Any]

class PerformanceData(BaseModel):
    timestamp: float
    cpu_usage: float
    memory_usage: float
    engine_depth: int
    evaluation_time: float

class ServerThread(QThread):
    status_changed = Signal(str, str)  # status, color
    performance_update = Signal(dict)  # performance data

    def __init__(self, engine_configs, book_config, tablebase_config, settings_manager):
        super().__init__()
        self.engine_configs = engine_configs
        self.book_config = book_config
        self.tablebase_config = tablebase_config
        self.settings_manager = settings_manager
        self.engines = []
        self.running = False

    def run(self):
        # Initialize engines
        for config in self.engine_configs:
            try:
                engine = EngineChess(
                    config['path'],
                    is_maia=config['is_maia'],
                    maia_config=config['config'],
                    book_config=self.book_config,
                    tablebase_config=self.tablebase_config
                )
                self.engines.append(engine)
                print(f"Loaded engine: {config['name']}")
            except Exception as e:
                print(f"Failed to load engine {config['name']}: {e}")
                continue

        # Initialize Maia engines
        for engine in self.engines:
            if engine.is_maia:
                engine.initialize_maia()

        # Start FastAPI server
        import uvicorn

        app = create_fastapi_app(self.engines, self.engine_configs, self.settings_manager)

        try:
            self.running = True
            self.status_changed.emit("Running", COLORS['success_green'])
            uvicorn.run(app, host="localhost", port=8000, log_level="error")
        except Exception as e:
            print(f"Server error: {e}")
            self.running = False
            self.status_changed.emit("Error", COLORS['error_red'])

class SettingsManager:
    def __init__(self):
        self.settings_file = "betterMint_settings.json"
        self.default_settings = {
            # WebSocket Settings
            "url-api-stockfish": "ws://localhost:8000/ws",
            "api-stockfish": True,

            # Engine Settings
            "num-cores": 1,
            "hashtable-ram": 1024,
            "depth": 15,
            "mate-finder-value": 5,
            "multipv": 3,
            "highmatechance": False,

            # Auto Move Settings
            "legit-auto-move": False,
            "auto-move-time": 5000,
            "auto-move-time-random": 2000,
            "auto-move-time-random-div": 10,
            "auto-move-time-random-multi": 1000,
            "best-move-chance": 30,
            "random-best-move": False,

            # Premove Settings
            "premove-enabled": False,
            "max-premoves": 3,
            "premove-time": 1000,
            "premove-time-random": 500,
            "premove-time-random-div": 100,
            "premove-time-random-multi": 1,

            # Visual Settings
            "show-hints": True,
            "move-analysis": True,
            "depth-bar": True,
            "evaluation-bar": True,

            # Misc Settings
            "text-to-speech": False,
            "performance-monitoring": False,
            "auto-save-settings": True,
            "notification-level": "normal"
        }
        self.settings = self.load_settings()

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
        return self.default_settings.copy()

    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value
        if self.get_setting("auto-save-settings", True):
            self.save_settings()

    def get_all_settings(self):
        return self.settings.copy()

    def update_settings(self, new_settings):
        self.settings.update(new_settings)
        self.save_settings()

class ChessEngineGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BetterMint Modded - Advanced Chess Engine Manager")
        self.setMinimumSize(900, 700)
        self.resize(1200, 800)

        # Initialize settings manager
        self.settings_manager = SettingsManager()

        # Server thread
        self.server_thread = None
        self.server_running = False

        # Performance monitoring
        self.performance_data = []
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self.update_performance_metrics)

        self.setup_ui()
        self.apply_styles()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.load_gui_settings()

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
        open_web_action.triggered.connect(lambda: os.system("start http://localhost:8000"))
        server_menu.addAction(open_web_action)

        # Tools Menu
        tools_menu = menubar.addMenu('Tools')

        performance_action = QAction('Performance Monitor', self)
        performance_action.setCheckable(True)
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

        # Set splitter sizes (30% left, 70% right)
        main_splitter.setSizes([300, 700])

    def create_left_panel(self):
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)

        # Title
        title_label = QLabel("BetterMint Modded")
        title_label.setObjectName("main_title")
        title_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title_label)

        # Engine Selection
        self.setup_engine_section(left_layout)

        # Server Status
        self.setup_server_status_section(left_layout)

        # Control Buttons
        self.setup_control_buttons(left_layout)

        # Performance Monitor (if enabled)
        self.performance_widget = self.create_performance_widget()
        self.performance_widget.setVisible(False)
        left_layout.addWidget(self.performance_widget)

        left_layout.addStretch()
        return left_widget

    def create_right_panel(self):
        # Create tabbed settings interface
        self.settings_tabs = QTabWidget()
        self.settings_tabs.setObjectName("settings_tabs")

        # Engine Settings Tab
        self.engine_settings_tab = self.create_engine_settings_tab()
        self.settings_tabs.addTab(self.engine_settings_tab, "Engine")

        # Auto-Move Settings Tab
        self.automove_settings_tab = self.create_automove_settings_tab()
        self.settings_tabs.addTab(self.automove_settings_tab, "Auto-Move")

        # Premove Settings Tab
        self.premove_settings_tab = self.create_premove_settings_tab()
        self.settings_tabs.addTab(self.premove_settings_tab, "Premoves")

        # Visual Settings Tab
        self.visual_settings_tab = self.create_visual_settings_tab()
        self.settings_tabs.addTab(self.visual_settings_tab, "Visual")

        # Advanced Settings Tab
        self.advanced_settings_tab = self.create_advanced_settings_tab()
        self.settings_tabs.addTab(self.advanced_settings_tab, "Advanced")

        # Monitoring Tab
        self.monitoring_tab = self.create_monitoring_tab()
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

        self.status_label = QLabel("Server: Stopped")
        self.status_label.setObjectName("status_stopped")
        status_layout.addWidget(self.status_label)

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

    def create_engine_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
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

        # Cores
        engine_layout.addWidget(QLabel("CPU Cores:"), 0, 0)
        self.cores_spin = QSpinBox()
        self.cores_spin.setRange(1, 16)
        self.cores_spin.setValue(self.settings_manager.get_setting("num-cores"))
        self.cores_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("num-cores", x))
        engine_layout.addWidget(self.cores_spin, 0, 1)

        # Hash table
        engine_layout.addWidget(QLabel("Hash Table (MB):"), 1, 0)
        self.hash_spin = QSpinBox()
        self.hash_spin.setRange(64, 8192)
        self.hash_spin.setSingleStep(64)
        self.hash_spin.setValue(self.settings_manager.get_setting("hashtable-ram"))
        self.hash_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("hashtable-ram", x))
        engine_layout.addWidget(self.hash_spin, 1, 1)

        # Depth
        engine_layout.addWidget(QLabel("Search Depth:"), 2, 0)
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 50)
        self.depth_spin.setValue(self.settings_manager.get_setting("depth"))
        self.depth_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("depth", x))
        engine_layout.addWidget(self.depth_spin, 2, 1)

        # MultiPV
        engine_layout.addWidget(QLabel("Analysis Lines:"), 3, 0)
        self.multipv_spin = QSpinBox()
        self.multipv_spin.setRange(1, 10)
        self.multipv_spin.setValue(self.settings_manager.get_setting("multipv"))
        self.multipv_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("multipv", x))
        engine_layout.addWidget(self.multipv_spin, 3, 1)

        # Mate finder
        engine_layout.addWidget(QLabel("Mate Finder Distance:"), 4, 0)
        self.mate_finder_spin = QSpinBox()
        self.mate_finder_spin.setRange(1, 20)
        self.mate_finder_spin.setValue(self.settings_manager.get_setting("mate-finder-value"))
        self.mate_finder_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("mate-finder-value", x))
        engine_layout.addWidget(self.mate_finder_spin, 4, 1)

        # High mate chance
        self.mate_chance_checkbox = QCheckBox("Prioritize Mate Search")
        self.mate_chance_checkbox.setChecked(self.settings_manager.get_setting("highmatechance"))
        self.mate_chance_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("highmatechance", x))
        engine_layout.addWidget(self.mate_chance_checkbox, 5, 0, 1, 2)

        layout.addWidget(engine_group)
        layout.addStretch()

        return widget

    def create_automove_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Auto-Move Configuration
        automove_group = QGroupBox("Auto-Move Configuration")
        automove_group.setObjectName("settings_group")
        automove_layout = QGridLayout(automove_group)

        # Enable auto-move
        self.automove_checkbox = QCheckBox("Enable Legit Auto-Move")
        self.automove_checkbox.setChecked(self.settings_manager.get_setting("legit-auto-move"))
        self.automove_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("legit-auto-move", x))
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
        self.random_best_checkbox = QCheckBox("Random Best Move Selection")
        self.random_best_checkbox.setChecked(self.settings_manager.get_setting("random-best-move"))
        self.random_best_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("random-best-move", x))
        automove_layout.addWidget(self.random_best_checkbox, 4, 0, 1, 2)

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

        return widget

    def create_premove_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Premove Configuration
        premove_group = QGroupBox("Premove Configuration")
        premove_group.setObjectName("settings_group")
        premove_layout = QGridLayout(premove_group)

        # Enable premoves
        self.premove_checkbox = QCheckBox("Enable Premoves")
        self.premove_checkbox.setChecked(self.settings_manager.get_setting("premove-enabled"))
        self.premove_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("premove-enabled", x))
        premove_layout.addWidget(self.premove_checkbox, 0, 0, 1, 2)

        # Max premoves
        premove_layout.addWidget(QLabel("Max Premoves:"), 1, 0)
        self.max_premoves_spin = QSpinBox()
        self.max_premoves_spin.setRange(1, 10)
        self.max_premoves_spin.setValue(self.settings_manager.get_setting("max-premoves"))
        self.max_premoves_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("max-premoves", x))
        premove_layout.addWidget(self.max_premoves_spin, 1, 1)

        # Premove delay
        premove_layout.addWidget(QLabel("Premove Delay (ms):"), 2, 0)
        self.premove_delay_spin = QSpinBox()
        self.premove_delay_spin.setRange(100, 5000)
        self.premove_delay_spin.setSingleStep(50)
        self.premove_delay_spin.setValue(self.settings_manager.get_setting("premove-time"))
        self.premove_delay_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("premove-time", x))
        premove_layout.addWidget(self.premove_delay_spin, 2, 1)

        # Premove random
        premove_layout.addWidget(QLabel("Random Delay (ms):"), 3, 0)
        self.premove_random_spin = QSpinBox()
        self.premove_random_spin.setRange(0, 2000)
        self.premove_random_spin.setSingleStep(50)
        self.premove_random_spin.setValue(self.settings_manager.get_setting("premove-time-random"))
        self.premove_random_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("premove-time-random", x))
        premove_layout.addWidget(self.premove_random_spin, 3, 1)

        layout.addWidget(premove_group)

        # Advanced Premove Timing
        premove_timing_group = QGroupBox("Advanced Premove Timing")
        premove_timing_group.setObjectName("settings_group")
        premove_timing_layout = QGridLayout(premove_timing_group)

        # Premove random divider
        premove_timing_layout.addWidget(QLabel("Random Divider:"), 0, 0)
        self.premove_div_spin = QSpinBox()
        self.premove_div_spin.setRange(1, 500)
        self.premove_div_spin.setValue(self.settings_manager.get_setting("premove-time-random-div"))
        self.premove_div_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("premove-time-random-div", x))
        premove_timing_layout.addWidget(self.premove_div_spin, 0, 1)

        # Premove random multiplier
        premove_timing_layout.addWidget(QLabel("Random Multiplier:"), 1, 0)
        self.premove_multi_spin = QSpinBox()
        self.premove_multi_spin.setRange(1, 100)
        self.premove_multi_spin.setValue(self.settings_manager.get_setting("premove-time-random-multi"))
        self.premove_multi_spin.valueChanged.connect(lambda x: self.settings_manager.set_setting("premove-time-random-multi", x))
        premove_timing_layout.addWidget(self.premove_multi_spin, 1, 1)

        layout.addWidget(premove_timing_group)
        layout.addStretch()

        return widget

    def create_visual_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Visual Features
        visual_group = QGroupBox("Visual Features")
        visual_group.setObjectName("settings_group")
        visual_layout = QVBoxLayout(visual_group)

        # Show hints
        self.hints_checkbox = QCheckBox("Show Move Hints")
        self.hints_checkbox.setChecked(self.settings_manager.get_setting("show-hints"))
        self.hints_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("show-hints", x))
        visual_layout.addWidget(self.hints_checkbox)

        # Move analysis
        self.analysis_checkbox = QCheckBox("Move Analysis")
        self.analysis_checkbox.setChecked(self.settings_manager.get_setting("move-analysis"))
        self.analysis_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("move-analysis", x))
        visual_layout.addWidget(self.analysis_checkbox)

        # Depth bar
        self.depth_bar_checkbox = QCheckBox("Depth Progress Bar")
        self.depth_bar_checkbox.setChecked(self.settings_manager.get_setting("depth-bar"))
        self.depth_bar_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("depth-bar", x))
        visual_layout.addWidget(self.depth_bar_checkbox)

        # Evaluation bar
        self.eval_bar_checkbox = QCheckBox("Evaluation Bar")
        self.eval_bar_checkbox.setChecked(self.settings_manager.get_setting("evaluation-bar"))
        self.eval_bar_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("evaluation-bar", x))
        visual_layout.addWidget(self.eval_bar_checkbox)

        layout.addWidget(visual_group)

        # Audio Features
        audio_group = QGroupBox("Audio Features")
        audio_group.setObjectName("settings_group")
        audio_layout = QVBoxLayout(audio_group)

        # Text to speech
        self.tts_checkbox = QCheckBox("Text-to-Speech (Best Moves)")
        self.tts_checkbox.setChecked(self.settings_manager.get_setting("text-to-speech"))
        self.tts_checkbox.toggled.connect(lambda x: self.settings_manager.set_setting("text-to-speech", x))
        audio_layout.addWidget(self.tts_checkbox)

        layout.addWidget(audio_group)
        layout.addStretch()

        return widget

    def create_advanced_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Performance Settings
        perf_group = QGroupBox("Performance & Monitoring")
        perf_group.setObjectName("settings_group")
        perf_layout = QVBoxLayout(perf_group)

        # Performance monitoring
        self.perf_monitor_checkbox = QCheckBox("Enable Performance Monitoring")
        self.perf_monitor_checkbox.setChecked(self.settings_manager.get_setting("performance-monitoring"))
        self.perf_monitor_checkbox.toggled.connect(self.toggle_performance_monitoring)
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
        return widget

    def create_monitoring_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Connection Monitor
        conn_group = QGroupBox("Connection Monitor")
        conn_group.setObjectName("settings_group")
        conn_layout = QVBoxLayout(conn_group)

        # Connection table
        self.connection_table = QTableWidget()
        self.connection_table.setColumnCount(4)
        self.connection_table.setHorizontalHeaderLabels(["Client", "Connected", "Last Activity", "Status"])
        self.connection_table.horizontalHeader().setStretchLastSection(True)
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
        clear_log_btn.clicked.connect(lambda: self.activity_log.clear())
        log_controls.addWidget(clear_log_btn)

        export_log_btn = QPushButton("Export Log")
        export_log_btn.clicked.connect(self.export_log)
        log_controls.addWidget(export_log_btn)

        log_controls.addStretch()
        log_layout.addLayout(log_controls)

        layout.addWidget(log_group)

        return widget

    def apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['darker_gray']};
                color: {COLORS['white']};
            }}

            QTabWidget#settings_tabs {{
                background-color: {COLORS['darker_gray']};
                border: none;
            }}

            QTabWidget#settings_tabs::pane {{
                border: 2px solid {COLORS['dark_gray']};
                border-radius: 8px;
                background-color: {COLORS['darker_gray']};
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
                font-weight: bold;
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
                font-weight: bold;
                color: {COLORS['white']};
                border: 2px solid {COLORS['dark_gray']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
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
                font-size: 24px;
                font-weight: bold;
                color: {COLORS['light_green']};
                margin: 10px 0;
            }}

            QFrame#engine_option {{
                background-color: {COLORS['dark_gray']};
                border: 1px solid {COLORS['dark_gray']};
                border-radius: 6px;
                margin: 2px;
            }}

            QCheckBox#engine_checkbox, QCheckBox#maia_checkbox {{
                font-weight: bold;
                color: {COLORS['white']};
                spacing: 8px;
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
                font-weight: bold;
            }}

            QLabel#status_unavailable {{
                color: {COLORS['error_red']};
                font-weight: bold;
            }}

            QLabel#description {{
                color: {COLORS['white']};
                font-size: 11px;
            }}

            QLabel#config_label {{
                color: {COLORS['white']};
                font-weight: bold;
                margin-bottom: 5px;
            }}

            QComboBox#strength_combo {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS['white']};
                font-weight: bold;
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
            }}

            QSlider#nodes_slider {{
                height: 25px;
            }}

            QSlider#nodes_slider::groove:horizontal {{
                background: {COLORS['dark_gray']};
                height: 6px;
                border-radius: 3px;
            }}

            QSlider#nodes_slider::handle:horizontal {{
                background: {COLORS['light_green']};
                width: 20px;
                height: 20px;
                border-radius: 10px;
                margin: -7px 0;
            }}

            QLabel#nodes_display {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS['white']};
                font-weight: bold;
                text-align: center;
            }}

            QLabel#status_stopped {{
                color: {COLORS['error_red']};
                font-weight: bold;
            }}

            QLabel#status_running {{
                color: {COLORS['success_green']};
                font-weight: bold;
            }}

            QLabel#status_info {{
                color: {COLORS['white']};
                font-weight: bold;
            }}

            QPushButton#start_button {{
                background-color: {COLORS['success_green']};
                color: {COLORS['white']};
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}

            QPushButton#start_button:hover {{
                background-color: #229954;
            }}

            QPushButton#start_button:disabled {{
                background-color: #666;
                color: #999;
            }}

            QPushButton#stop_button {{
                background-color: {COLORS['error_red']};
                color: {COLORS['white']};
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}

            QPushButton#stop_button:hover {{
                background-color: #c0392b;
            }}

            QPushButton#stop_button:disabled {{
                background-color: #666;
                color: #999;
            }}

            QSpinBox {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 5px;
                color: {COLORS['white']};
                font-weight: bold;
            }}

            QLineEdit {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS['white']};
                font-weight: bold;
            }}

            QProgressBar#progress_bar {{
                border: 2px solid {COLORS['dark_gray']};
                border-radius: 4px;
                text-align: center;
                color: {COLORS['white']};
                font-weight: bold;
            }}

            QProgressBar#progress_bar::chunk {{
                background-color: {COLORS['light_green']};
                border-radius: 2px;
            }}

            QTableWidget {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                color: {COLORS['white']};
                gridline-color: {COLORS['darker_gray']};
            }}

            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {COLORS['darker_gray']};
            }}

            QTableWidget::item:selected {{
                background-color: {COLORS['light_green']};
            }}

            QHeaderView::section {{
                background-color: {COLORS['light_green']};
                color: {COLORS['white']};
                padding: 8px;
                border: none;
                font-weight: bold;
            }}

            QTextEdit#activity_log {{
                background-color: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
                border-radius: 4px;
                color: {COLORS['white']};
                font-family: Consolas, Monaco, monospace;
            }}

            QPushButton {{
                background-color: {COLORS['light_green']};
                color: {COLORS['white']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
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
            }}

            QMenuBar {{
                background-color: {COLORS['dark_gray']};
                color: {COLORS['white']};
                border-bottom: 1px solid {COLORS['light_green']};
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
            }}

            QMenu::item {{
                padding: 8px 20px;
            }}

            QMenu::item:selected {{
                background-color: {COLORS['light_green']};
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

    def on_maia_toggle(self, checked):
        self.maia_config_frame.setVisible(checked)

    def check_stockfish_available(self):
        return os.path.exists("engines/stockfish/stockfish.exe")

    def check_leela_available(self):
        return os.path.exists("engines/leela/lc0.exe")

    def get_available_maia_weights(self):
        weights = []
        for i in range(1100, 2000, 100):
            pattern = f"weights/maia-{i}.pb.gz"
            if os.path.exists(pattern):
                weights.append(str(i))
        return weights

    def toggle_performance_monitoring(self, enabled):
        self.settings_manager.set_setting("performance-monitoring", enabled)
        self.performance_widget.setVisible(enabled)
        if enabled:
            self.performance_timer.start(1000)  # Update every second
            self.log_activity("Performance monitoring enabled")
        else:
            self.performance_timer.stop()
            self.log_activity("Performance monitoring disabled")

    def update_performance_metrics(self):
        # Simulate performance metrics (in real implementation, get actual values)
        import psutil
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

    def log_activity(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append(f"[{timestamp}] {message}")

    def start_server(self):
        selected_engines = []

        if self.stockfish_checkbox.isChecked():
            if self.check_stockfish_available():
                selected_engines.append({
                    'path': 'engines/stockfish/stockfish.exe',
                    'is_maia': False,
                    'config': {},
                    'name': 'Stockfish'
                })
            else:
                QMessageBox.critical(self, "Error", "Stockfish not found")
                return

        if self.leela_checkbox.isChecked():
            if self.check_leela_available():
                config = {}
                if self.maia_checkbox.isChecked():
                    strength = self.strength_combo.currentText()
                    weights_path = f"weights/maia-{strength}.pb.gz"
                    if os.path.exists(weights_path):
                        nodes_value = self.nodes_slider.value() / 1000.0
                        config = {
                            'weights_file': weights_path,
                            'nodes_per_second_limit': nodes_value,
                            'use_slowmover': False
                        }
                    else:
                        QMessageBox.critical(self, "Error", f"Maia weights not found: {weights_path}")
                        return

                engine_name = "Leela"
                if self.maia_checkbox.isChecked():
                    engine_name += f" + Maia {self.strength_combo.currentText()}"

                selected_engines.append({
                    'path': 'engines/leela/lc0.exe',
                    'is_maia': self.maia_checkbox.isChecked(),
                    'config': config,
                    'name': engine_name
                })
            else:
                QMessageBox.critical(self, "Error", "Leela not found")
                return

        if not selected_engines:
            QMessageBox.warning(self, "Warning", "Please select at least one engine")
            return

        book_config = {}
        tablebase_config = {}

        try:
            self.server_thread = ServerThread(selected_engines, book_config, tablebase_config, self.settings_manager)
            self.server_thread.status_changed.connect(self.on_server_status_changed)
            self.server_thread.start()

            self.server_running = True

            # Update UI
            self.status_label.setText("Server: Starting...")
            self.status_label.setObjectName("status_running")
            self.engines_label.setText(f"Active Engines: {len(selected_engines)}")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            self.log_activity(f"Server started with {len(selected_engines)} engines")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start server: {str(e)}")
            self.server_running = False

    def stop_server(self):
        if self.server_thread and self.server_thread.isRunning():
            self.server_thread.terminate()
            self.server_thread.wait()

        self.server_running = False

        self.status_label.setText("Server: Stopped")
        self.status_label.setObjectName("status_stopped")
        self.engines_label.setText("Active Engines: 0")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self.log_activity("Server stopped")

    def on_server_status_changed(self, status, color):
        self.status_label.setText(f"Server: {status}")
        self.server_status_label.setText(f"Server: {status}")

    # Menu actions
    def new_profile(self):
        self.settings_manager.settings = self.settings_manager.default_settings.copy()
        self.load_gui_settings()
        self.log_activity("New profile created")

    def load_profile(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Profile", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    profile_data = json.load(f)
                self.settings_manager.settings.update(profile_data)
                self.load_gui_settings()
                self.log_activity(f"Profile loaded from {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load profile: {str(e)}")

    def save_profile(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Profile", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.settings_manager.settings, f, indent=2)
                self.log_activity(f"Profile saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save profile: {str(e)}")

    def export_settings(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Settings", "betterMint_export.json", "JSON Files (*.json)")
        if file_path:
            try:
                export_data = {
                    "settings": self.settings_manager.settings,
                    "export_date": datetime.now().isoformat(),
                    "version": "3.0.0"
                }
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                self.log_activity(f"Settings exported to {file_path}")
                QMessageBox.information(self, "Success", "Settings exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export settings: {str(e)}")

    def import_settings(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Settings", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    import_data = json.load(f)

                if "settings" in import_data:
                    self.settings_manager.settings.update(import_data["settings"])
                else:
                    self.settings_manager.settings.update(import_data)

                self.load_gui_settings()
                self.log_activity(f"Settings imported from {file_path}")
                QMessageBox.information(self, "Success", "Settings imported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import settings: {str(e)}")

    def clear_logs(self):
        self.activity_log.clear()

    def export_log(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Log", f"betterMint_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.activity_log.toPlainText())
                QMessageBox.information(self, "Success", "Log exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export log: {str(e)}")

    def clear_cache(self):
        # Clear any cache files
        cache_files = glob.glob("*.cache") + glob.glob("*.tmp")
        for file in cache_files:
            try:
                os.remove(file)
            except:
                pass
        self.log_activity("Cache cleared")
        QMessageBox.information(self, "Success", "Cache cleared successfully!")

    def reset_to_defaults(self):
        reply = QMessageBox.question(self, "Reset Settings",
                                    "Are you sure you want to reset all settings to defaults?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.settings_manager.settings = self.settings_manager.default_settings.copy()
            self.settings_manager.save_settings()
            self.load_gui_settings()
            self.log_activity("Settings reset to defaults")

    def show_about(self):
        QMessageBox.about(self, "About BetterMint Modded",
                         "BetterMint Modded v3.0.0\n\n"
                         "Advanced Chess Analysis Tool\n"
                         "Server-side managed settings\n\n"
                         "Enhanced by Claude AI\n"
                         "Original BetterMint by BetterMint Team")

    def load_gui_settings(self):
        """Load all settings into GUI elements"""
        try:
            # Engine settings
            self.api_url_edit.setText(self.settings_manager.get_setting("url-api-stockfish"))
            self.api_checkbox.setChecked(self.settings_manager.get_setting("api-stockfish"))
            self.cores_spin.setValue(self.settings_manager.get_setting("num-cores"))
            self.hash_spin.setValue(self.settings_manager.get_setting("hashtable-ram"))
            self.depth_spin.setValue(self.settings_manager.get_setting("depth"))
            self.multipv_spin.setValue(self.settings_manager.get_setting("multipv"))
            self.mate_finder_spin.setValue(self.settings_manager.get_setting("mate-finder-value"))
            self.mate_chance_checkbox.setChecked(self.settings_manager.get_setting("highmatechance"))

            # Auto-move settings
            self.automove_checkbox.setChecked(self.settings_manager.get_setting("legit-auto-move"))
            self.automove_delay_spin.setValue(self.settings_manager.get_setting("auto-move-time"))
            self.automove_random_spin.setValue(self.settings_manager.get_setting("auto-move-time-random"))
            self.best_move_spin.setValue(self.settings_manager.get_setting("best-move-chance"))
            self.random_best_checkbox.setChecked(self.settings_manager.get_setting("random-best-move"))
            self.random_div_spin.setValue(self.settings_manager.get_setting("auto-move-time-random-div"))
            self.random_multi_spin.setValue(self.settings_manager.get_setting("auto-move-time-random-multi"))

            # Premove settings
            self.premove_checkbox.setChecked(self.settings_manager.get_setting("premove-enabled"))
            self.max_premoves_spin.setValue(self.settings_manager.get_setting("max-premoves"))
            self.premove_delay_spin.setValue(self.settings_manager.get_setting("premove-time"))
            self.premove_random_spin.setValue(self.settings_manager.get_setting("premove-time-random"))
            self.premove_div_spin.setValue(self.settings_manager.get_setting("premove-time-random-div"))
            self.premove_multi_spin.setValue(self.settings_manager.get_setting("premove-time-random-multi"))

            # Visual settings
            self.hints_checkbox.setChecked(self.settings_manager.get_setting("show-hints"))
            self.analysis_checkbox.setChecked(self.settings_manager.get_setting("move-analysis"))
            self.depth_bar_checkbox.setChecked(self.settings_manager.get_setting("depth-bar"))
            self.eval_bar_checkbox.setChecked(self.settings_manager.get_setting("evaluation-bar"))
            self.tts_checkbox.setChecked(self.settings_manager.get_setting("text-to-speech"))

            # Advanced settings
            self.perf_monitor_checkbox.setChecked(self.settings_manager.get_setting("performance-monitoring"))
            self.autosave_checkbox.setChecked(self.settings_manager.get_setting("auto-save-settings"))

            notif_level = self.settings_manager.get_setting("notification-level", "normal")
            self.notif_combo.setCurrentText(notif_level.title())

        except Exception as e:
            print(f"Error loading GUI settings: {e}")

    def closeEvent(self, event):
        if self.server_running:
            self.stop_server()

        # Save window state
        settings = QSettings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

        event.accept()

# Engine classes and FastAPI setup remain the same as before, but with API enhancements...

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

class EngineChess:
    def __init__(self, path_engine, is_maia=False, maia_config=None, book_config=None, tablebase_config=None):
        self._engine = subprocess.Popen(
            path_engine,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.queueOutput = Queue()
        self.thread = Thread(target=enqueue_output, args=(self._engine.stdout, self.queueOutput))
        self.thread.daemon = True
        self.thread.start()

        self._command_queue = Queue()
        self._queue_lock = Lock()
        self._has_quit_command_been_sent = False
        self._current_turn = "w"
        self.is_maia = is_maia
        self.maia_config = maia_config or {}
        self.book_config = book_config or {}
        self.tablebase_config = tablebase_config or {}
        self.is_initialized = False

        self.opening_book = None
        self.tablebase_path = None
        self.setup_book_and_tablebase()

    def setup_book_and_tablebase(self):
        if self.book_config.get('enabled') and self.book_config.get('book_file'):
            book_file = self.book_config['book_file']
            if os.path.exists(book_file):
                self.opening_book = book_file
                print(f"Loaded opening book: {book_file}")

        if self.tablebase_config.get('enabled') and self.tablebase_config.get('tablebase_path'):
            tb_path = self.tablebase_config['tablebase_path']
            if os.path.exists(tb_path):
                self.tablebase_path = tb_path
                print(f"Loaded tablebase path: {tb_path}")

    def put(self, cmd):
        with self._queue_lock:
            self._command_queue.put(cmd)

    def send_next_command(self):
        with self._queue_lock:
            if not self._command_queue.empty():
                cmd = self._command_queue.get()
                if self._engine.stdin and not self._has_quit_command_been_sent:
                    self._engine.stdin.write(f"{cmd}\n")
                    self._engine.stdin.flush()
                    if cmd == "quit":
                        self._has_quit_command_been_sent = True

    def initialize_maia(self):
        if self.is_maia and not self.is_initialized:
            print("Initializing Maia chess engine...")

            self.put("uci")
            time.sleep(1)

            if 'weights_file' in self.maia_config:
                self.put(f"setoption name WeightsFile value {self.maia_config['weights_file']}")

            self.put("setoption name Threads value 1")
            self.put("setoption name MinibatchSize value 1")
            self.put("setoption name MaxPrefetch value 0")

            nodes_limit = self.maia_config.get('nodes_per_second_limit', 0.001)
            self.put(f"setoption name NodesPerSecondLimit value {nodes_limit}")

            if self.maia_config.get('use_slowmover', False):
                self.put("setoption name SlowMover value 0")

            if self.opening_book:
                self.put(f"setoption name Book value true")
                self.put(f"setoption name BookFile value {self.opening_book}")

            if self.tablebase_path:
                self.put(f"setoption name SyzygyPath value {self.tablebase_path}")

            self.put("isready")
            self.is_initialized = True
            print("Maia initialization complete!")
        elif not self.is_maia and not self.is_initialized:
            self.put("uci")
            time.sleep(0.5)

            if self.opening_book:
                for book_option in ["Book", "BookFile", "OwnBook", "UseBook"]:
                    self.put(f"setoption name {book_option} value true")
                self.put(f"setoption name BookFile value {self.opening_book}")

            if self.tablebase_path:
                for tb_option in ["SyzygyPath", "TablebaseePath", "Tablebase", "TbPath"]:
                    self.put(f"setoption name {tb_option} value {self.tablebase_path}")

            self.put("isready")
            self.is_initialized = True

    def _read_line(self) -> str:
        if not self._engine.stdout:
            raise BrokenPipeError()
        if self._engine.poll() is not None:
            raise Exception("The engine process has crashed")

        try:
            line = self.queueOutput.get_nowait()
        except Empty:
            return ""

        return line.strip()

    def read_line(self) -> str:
        self.send_next_command()
        return self._read_line()

def create_fastapi_app(engines, engine_configs, settings_manager):
    app = FastAPI(title="BetterMint Modded API", version="3.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )

    active_connections = set()

    @app.get("/api/settings")
    async def get_settings():
        """Get all current settings"""
        return settings_manager.get_all_settings()

    @app.post("/api/settings")
    async def update_settings(settings: Settings):
        """Update settings"""
        try:
            settings_manager.update_settings(settings.settings)
            return {"status": "success", "message": "Settings updated"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/settings/{key}")
    async def get_setting(key: str):
        """Get a specific setting"""
        value = settings_manager.get_setting(key)
        if value is None:
            raise HTTPException(status_code=404, detail="Setting not found")
        return {"key": key, "value": value}

    @app.post("/api/settings/{key}")
    async def set_setting(key: str, value: dict):
        """Set a specific setting"""
        try:
            settings_manager.set_setting(key, value["value"])
            return {"status": "success", "key": key, "value": value["value"]}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/health")
    async def health_check():
        return JSONResponse({
            "status": "healthy",
            "engines": len(engines),
            "active_connections": len(active_connections),
            "maia_engines": sum(1 for engine in engines if engine.is_maia),
            "settings_count": len(settings_manager.get_all_settings())
        })

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        nonlocal active_connections

        active_connections.add(websocket)
        await websocket.accept()

        try:
            async def process_client_command(data):
                if data.startswith("go"):
                    for engine in engines:
                        if engine.is_maia:
                            if "nodes" not in data:
                                engine.put("go nodes 1")
                            else:
                                engine.put(data)
                        else:
                            engine.put(data)
                elif data.startswith("ucinewgame"):
                    for engine in engines:
                        engine.put("ucinewgame")
                        if engine.is_maia:
                            engine.put("isready")
                        elif not engine.is_initialized:
                            engine.initialize_maia()
                else:
                    for engine in engines:
                        engine.put(data)

            async def handle_client():
                while websocket.client_state == WebSocketState.CONNECTED:
                    try:
                        data = await websocket.receive_text()
                        asyncio.create_task(process_client_command(data))
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        print(f"Error receiving data: {e}")
                        break

            asyncio.create_task(handle_client())

            while True:
                try:
                    responses = [engine.read_line() for engine in engines]
                    responses = list(filter(None, responses))

                    if responses:
                        for res in responses:
                            disconnected_connections = set()
                            for conn in active_connections:
                                try:
                                    if conn.client_state == WebSocketState.CONNECTED:
                                        await conn.send_text(res)
                                    else:
                                        disconnected_connections.add(conn)
                                except Exception as e:
                                    disconnected_connections.add(conn)

                            active_connections -= disconnected_connections
                    else:
                        await asyncio.sleep(0.01)
                except Exception as e:
                    print(f"Error in main loop: {e}")
                    break

        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"Error in WebSocket: {e}")
        finally:
            active_connections.discard(websocket)
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.close()
            except:
                pass

    @app.get("/")
    async def get():
        engine_info = []
        for i, config in enumerate(engine_configs):
            engine_info.append(f"Engine {i+1}: {config['name']}")

        return HTMLResponse(f"""<!DOCTYPE html>
<html>
    <head>
        <title>BetterMint Modded - WebSocket Interface</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

            * {{
                box-sizing: border-box;
            }}

            body {{
                font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                background: {COLORS['darker_gray']};
                color: {COLORS['white']};
                line-height: 1.5;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
                min-height: 100vh;
            }}
            .header {{
                text-align: center;
                margin-bottom: 40px;
                padding: 20px;
                background: {COLORS['dark_gray']};
                border-radius: 12px;
            }}
            .header h1 {{
                font-weight: 700;
                font-size: 32px;
                color: {COLORS['white']};
                margin: 0 0 15px 0;
            }}
            .status {{
                color: {COLORS['light_green']};
                font-weight: 700;
                margin: 8px 0;
                font-size: 16px;
                display: inline-block;
                background: rgba(105, 146, 62, 0.1);
                padding: 5px 15px;
                border-radius: 20px;
                margin: 0 10px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-bottom: 30px;
            }}
            .card {{
                background: {COLORS['dark_gray']};
                padding: 25px;
                border-radius: 12px;
                border: 1px solid {COLORS['light_green']};
            }}
            .card h3 {{
                font-weight: 700;
                margin: 0 0 20px 0;
                color: {COLORS['light_green']};
                font-size: 18px;
                border-bottom: 2px solid {COLORS['light_green']};
                padding-bottom: 10px;
            }}
            .engine-list {{
                background: {COLORS['darker_gray']};
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid {COLORS['light_green']};
                margin-bottom: 20px;
            }}
            .quick-commands {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 10px;
                margin-bottom: 20px;
            }}
            .quick-commands button {{
                background: {COLORS['light_green']};
                color: {COLORS['white']};
                border: none;
                padding: 12px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 700;
                font-family: 'Montserrat', sans-serif;
                transition: all 0.2s ease;
                font-size: 12px;
            }}
            .quick-commands button:hover {{
                background: {COLORS['dark_green']};
                transform: translateY(-1px);
            }}
            .input-group {{
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }}
            #messageText {{
                flex: 1;
                padding: 12px 16px;
                border: 2px solid {COLORS['light_green']};
                border-radius: 6px;
                background: {COLORS['darker_gray']};
                color: {COLORS['white']};
                font-family: 'Montserrat', sans-serif;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s ease;
            }}
            #messageText:focus {{
                border-color: {COLORS['dark_green']};
            }}
            .form-button {{
                background: {COLORS['light_green']};
                color: {COLORS['white']};
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 700;
                font-family: 'Montserrat', sans-serif;
                transition: all 0.2s ease;
                font-size: 14px;
                min-width: 80px;
            }}
            .form-button:hover {{
                background: {COLORS['dark_green']};
                transform: translateY(-1px);
            }}
            .form-button.secondary {{
                background: {COLORS['dark_gray']};
                border: 2px solid {COLORS['light_green']};
            }}
            .form-button.secondary:hover {{
                background: {COLORS['darker_gray']};
            }}
            #messages {{
                height: 400px;
                overflow-y: auto;
                border: 2px solid {COLORS['dark_gray']};
                padding: 20px;
                background: {COLORS['darker_gray']};
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                list-style: none;
                margin: 0;
                scrollbar-width: thin;
                scrollbar-color: {COLORS['light_green']} {COLORS['dark_gray']};
            }}
            #messages::-webkit-scrollbar {{
                width: 8px;
            }}
            #messages::-webkit-scrollbar-track {{
                background: {COLORS['dark_gray']};
                border-radius: 4px;
            }}
            #messages::-webkit-scrollbar-thumb {{
                background: {COLORS['light_green']};
                border-radius: 4px;
            }}
            #messages li {{
                margin: 3px 0;
                color: {COLORS['white']};
                padding: 2px 0;
                border-bottom: 1px solid rgba(75, 72, 71, 0.3);
            }}
            .connection-indicator {{
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: 700;
                font-size: 12px;
                z-index: 1000;
            }}
            .connected {{
                background: {COLORS['success_green']};
                color: {COLORS['white']};
            }}
            .disconnected {{
                background: {COLORS['error_red']};
                color: white;
            }}

            @media (max-width: 768px) {{
                .grid {{
                    grid-template-columns: 1fr;
                }}
                .quick-commands {{
                    grid-template-columns: repeat(2, 1fr);
                }}
            }}
        </style>
    </head>
    <body>
        <div class="connection-indicator disconnected" id="connectionStatus">
            Connecting...
        </div>

        <div class="container">
            <div class="header">
                <h1>♛ BetterMint Modded v3.0.0</h1>
                <div>
                    <span class="status">Engines: {len(engines)}</span>
                    <span class="status">Connections: <span id="connectionCount">{len(active_connections)}</span></span>
                </div>
            </div>

            <div class="grid">
                <div class="card">
                    <h3>📊 Engine Information</h3>
                    <div class="engine-list">
                        {'<br>'.join(f"<strong>{info}</strong>" for info in engine_info)}
                    </div>

                    <h3>⚡ Quick Commands</h3>
                    <div class="quick-commands">
                        <button onclick="sendQuickCommand('uci')">UCI Info</button>
                        <button onclick="sendQuickCommand('isready')">Ready Check</button>
                        <button onclick="sendQuickCommand('ucinewgame')">New Game</button>
                        <button onclick="sendQuickCommand('position startpos')">Start Position</button>
                        <button onclick="sendQuickCommand('go nodes 1')">Quick Move</button>
                        <button onclick="sendQuickCommand('go depth 10')">Deep Search</button>
                        <button onclick="sendQuickCommand('go movetime 5000')">5 Second Think</button>
                        <button onclick="sendQuickCommand('stop')">Stop Analysis</button>
                    </div>
                </div>

                <div class="card">
                    <h3>💬 Send UCI Command</h3>
                    <form action="" onsubmit="sendMessage(event)">
                        <div class="input-group">
                            <input type="text" id="messageText" autocomplete="off" placeholder="Type UCI command (e.g., go depth 15)..."/>
                            <button type="submit" class="form-button">Send</button>
                            <button type="button" onclick="clearMessages()" class="form-button secondary">Clear</button>
                        </div>
                    </form>

                    <div style="background: rgba(105, 146, 62, 0.1); padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                        <strong>💡 Settings Management:</strong><br>
                        • All engine settings are managed in the GUI application<br>
                        • Settings sync automatically with connected clients<br>
                        • Visit the server GUI for complete configuration
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>📝 Engine Responses</h3>
                <ul id='messages'></ul>
            </div>
        </div>

        <script>
            let ws;
            let reconnectAttempts = 0;
            const maxReconnectAttempts = 5;

            function connect() {{
                const connectionStatus = document.getElementById('connectionStatus');
                connectionStatus.textContent = 'Connecting...';
                connectionStatus.className = 'connection-indicator disconnected';

                ws = new WebSocket("ws://localhost:8000/ws");

                ws.onopen = function(event) {{
                    reconnectAttempts = 0;
                    connectionStatus.textContent = 'Connected';
                    connectionStatus.className = 'connection-indicator connected';
                    console.log('Connected to BetterMint Modded server');
                }};

                ws.onmessage = function(event) {{
                    var messages = document.getElementById('messages');
                    var message = document.createElement('li');
                    var content = document.createTextNode(event.data);
                    message.appendChild(content);
                    messages.appendChild(message);
                    messages.scrollTop = messages.scrollHeight;

                    if (messages.children.length > 1000) {{
                        messages.removeChild(messages.firstChild);
                    }}
                }};

                ws.onclose = function(event) {{
                    connectionStatus.textContent = 'Disconnected';
                    connectionStatus.className = 'connection-indicator disconnected';

                    if (reconnectAttempts < maxReconnectAttempts) {{
                        reconnectAttempts++;
                        connectionStatus.textContent = `Reconnecting... (${reconnectAttempts}/${maxReconnectAttempts})`;
                        setTimeout(connect, 2000 * reconnectAttempts);
                    }} else {{
                        connectionStatus.textContent = 'Connection Failed';
                    }}
                }};

                ws.onerror = function(error) {{
                    console.error('WebSocket error:', error);
                    connectionStatus.textContent = 'Connection Error';
                    connectionStatus.className = 'connection-indicator disconnected';
                }};
            }}

            function sendMessage(event) {{
                var input = document.getElementById("messageText");
                if (ws && ws.readyState === WebSocket.OPEN) {{
                    ws.send(input.value);
                }} else {{
                    alert("WebSocket is not connected.");
                }}
                input.value = '';
                event.preventDefault();
            }}

            function sendQuickCommand(command) {{
                if (ws && ws.readyState === WebSocket.OPEN) {{
                    ws.send(command);
                }} else {{
                    alert("WebSocket is not connected.");
                }}
            }}

            function clearMessages() {{
                document.getElementById('messages').innerHTML = '';
            }}

            window.onload = function() {{
                connect();
            }};
        </script>
    </body>
</html>
""")

    return app

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("BetterMint Modded")
    app.setApplicationVersion("3.0.0")
    app.setOrganizationName("BetterMint Team")

    window = ChessEngineGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
