"""
Constants and color scheme for BetterMint Modded
Enhanced with comprehensive logging configuration and Rodent IV engine support
"""

import os
import logging
import logging.handlers
from pathlib import Path

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

# Application metadata
APP_NAME = "BetterMint Modded"
APP_VERSION = "MINT Beta 2c 26092025 Features"
APP_ORGANIZATION = "BetterMint Team"

# Server configuration
DEFAULT_PORT = 8000
DEFAULT_HOST = "localhost"

# Engine paths
STOCKFISH_PATH = 'engines/stockfish/stockfish.exe'
LEELA_PATH = 'engines/leela/lc0.exe'
RODENT_PATH = 'engines/rodent/rodent-iv-plain.exe'  # NEW: Rodent IV engine support
MAIA_WEIGHTS_PATH = 'weights/maia-{}.pb.gz'

# Performance monitoring
PERFORMANCE_UPDATE_INTERVAL = 1000  # milliseconds
CONNECTION_UPDATE_INTERVAL = 2000   # milliseconds

# WebSocket settings
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY_BASE = 2000  # milliseconds

# GUI settings
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 750
WINDOW_DEFAULT_WIDTH = 1400
WINDOW_DEFAULT_HEIGHT = 900

# Icon settings
ICON_DIR = Path(__file__).parent / "icons"
ICON_FILES = [
    "icon.png",  # Large size
]

# Message history limit
MAX_MESSAGE_HISTORY = 1000

# Logging configuration
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Log levels
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Log formats
DETAILED_FORMAT = '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s'
SIMPLE_FORMAT = '%(asctime)s | %(levelname)-8s | %(message)s'
PERFORMANCE_FORMAT = '%(asctime)s | PERF | %(name)s | %(message)s'

def setup_logging(log_level='INFO', enable_file_logging=True, enable_performance_logging=True):
    """
    Set up comprehensive logging system for BetterMint Modded
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_file_logging: Whether to log to files
        enable_performance_logging: Whether to enable performance logging
    """
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVELS.get(log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with color support
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Custom formatter with colors for console
    class ColoredFormatter(logging.Formatter):
        """Custom formatter with colors for different log levels"""
        
        COLORS = {
            'DEBUG': '\033[36m',      # Cyan
            'INFO': '\033[32m',       # Green  
            'WARNING': '\033[33m',    # Yellow
            'ERROR': '\033[31m',      # Red
            'CRITICAL': '\033[35m',   # Magenta
        }
        RESET = '\033[0m'
        
        def format(self, record):
            # Add color to levelname
            levelname_color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{levelname_color}{record.levelname}{self.RESET}"
            return super().format(record)
    
    console_formatter = ColoredFormatter(SIMPLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    if enable_file_logging:
        # Main application log with rotation
        main_log_file = LOG_DIR / "betterMint_modded.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(DETAILED_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Error log (ERROR and CRITICAL only)
        error_log_file = LOG_DIR / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,   # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
        
        # Engine communication log
        engine_log_file = LOG_DIR / "engine_communication.log"
        engine_handler = logging.handlers.RotatingFileHandler(
            engine_log_file,
            maxBytes=20*1024*1024,  # 20MB for high-volume engine logs
            backupCount=3
        )
        engine_handler.setLevel(logging.DEBUG)
        engine_handler.addFilter(lambda record: record.name.startswith('engine'))
        engine_handler.setFormatter(file_formatter)
        root_logger.addHandler(engine_handler)
        
        if enable_performance_logging:
            # Performance log
            perf_log_file = LOG_DIR / "performance.log" 
            perf_handler = logging.handlers.RotatingFileHandler(
                perf_log_file,
                maxBytes=5*1024*1024,   # 5MB
                backupCount=2
            )
            perf_handler.setLevel(logging.DEBUG)
            perf_handler.addFilter(lambda record: 'PERF' in record.getMessage())
            perf_formatter = logging.Formatter(PERFORMANCE_FORMAT)
            perf_handler.setFormatter(perf_formatter)
            root_logger.addHandler(perf_handler)

def get_logger(name):
    """
    Get a logger instance for a specific module
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)

def log_performance(logger, operation, duration=None, **kwargs):
    """
    Log performance metrics
    
    Args:
        logger: Logger instance
        operation: Operation name
        duration: Operation duration in seconds
        **kwargs: Additional metrics to log
    """
    metrics = {
        'operation': operation,
        **kwargs
    }
    
    if duration is not None:
        metrics['duration_ms'] = round(duration * 1000, 2)
    
    metric_str = ' | '.join([f"{k}={v}" for k, v in metrics.items()])
    logger.info(f"PERF | {metric_str}")

def log_uci_command(logger, direction, engine_name, command, response_time=None):
    """
    Log UCI engine commands and responses
    
    Args:
        logger: Logger instance
        direction: 'SEND' or 'RECV'
        engine_name: Name of the engine
        command: UCI command/response
        response_time: Response time in seconds (for RECV only)
    """
    timestamp_info = ""
    if response_time is not None:
        timestamp_info = f" | time={response_time:.3f}s"
    
    logger.debug(f"UCI | {direction} | {engine_name} | {command.strip()}{timestamp_info}")

# Initialize logging on import with default settings
setup_logging()

# Create module-level loggers for common use
main_logger = get_logger('betterMint.main')
engine_logger = get_logger('engine')
server_logger = get_logger('server') 
gui_logger = get_logger('gui')
playwright_logger = get_logger('playwright')