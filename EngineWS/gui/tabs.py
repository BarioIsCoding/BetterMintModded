"""
BetterMint Modded GUI Tabs Module
Imports and re-exports all individual tab components for backward compatibility
"""

# Import individual tab components
from .engine_settings_tab import EngineSettingsTab
from .automove_settings_tab import AutoMoveSettingsTab
from .premove_settings_tab import PremoveSettingsTab
from .visual_settings_tab import VisualSettingsTab
from .advanced_settings_tab import AdvancedSettingsTab
from .monitoring_tab import MonitoringTab
from .chess_com_webview import (
    ChessComWebView, 
    EnhancedChessComWebView, 
    PlaywrightChessController,
    PLAYWRIGHT_AVAILABLE
)

# Re-export all classes for backward compatibility
__all__ = [
    'EngineSettingsTab',
    'AutoMoveSettingsTab', 
    'PremoveSettingsTab',
    'VisualSettingsTab',
    'AdvancedSettingsTab',
    'MonitoringTab',
    'ChessComWebView',
    'EnhancedChessComWebView',
    'PlaywrightChessController',
    'PLAYWRIGHT_AVAILABLE'
]

# Version information
__version__ = "3.0.0"
__author__ = "BarioIsCool"
__description__ = "Modular GUI tabs for BetterMint Modded chess engine interface"