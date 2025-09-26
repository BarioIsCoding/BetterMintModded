#!/usr/bin/env python3
"""
BetterMint Modded - Advanced Chess Engine Manager
Fixed main entry point addressing Unicode, Qt, and logging issues
Added version checking and personalities folder migration
FIXED: import * syntax error and QUiLoader hanging issue
"""

import sys
import os
import time
import traceback
import shutil
import urllib.request
import urllib.error
from pathlib import Path

# CRITICAL: Fix Windows Unicode console issues FIRST
if sys.platform == 'win32':
    try:
        # Set Windows console to UTF-8 mode
        os.system('chcp 65001 > nul 2>&1')
        
        # Reconfigure stdout/stderr for UTF-8 if possible
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        # Fallback: will handle Unicode issues in logging setup
        pass

# Record startup time
STARTUP_TIME = time.time()

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Basic logging setup (fallback if enhanced logging fails)
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    stream=sys.stdout
)

def safe_log(message, level=logging.INFO):
    """Safe logging that handles Unicode issues on Windows"""
    try:
        # Replace problematic Unicode characters
        safe_message = str(message)
        if sys.platform == 'win32':
            replacements = {
                '\u2713': '[OK]',    # Checkmark
                '\u2717': '[FAIL]',  # X mark
                '\u2022': '-',       # Bullet
                '\u2192': '->',      # Right arrow
                '\u2190': '<-',      # Left arrow
            }
            for unicode_char, replacement in replacements.items():
                safe_message = safe_message.replace(unicode_char, replacement)
        
        # Limit message length to prevent spam
        if len(safe_message) > 500:
            safe_message = safe_message[:500] + "...truncated"
            
        logging.log(level, safe_message)
    except Exception:
        # Ultimate fallback
        print(f"[{level}] {str(message)[:200]}")


def get_current_version() -> str:
    """Get current version from version file"""
    try:
        version_file = Path(PROJECT_ROOT) / "version"
        if version_file.exists():
            with open(version_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        else:
            safe_log("Version file not found, assuming version MINT Beta 2c 26092025 Features", logging.WARNING)
            return "MINT Beta 2c 26092025 Features"
    except Exception as e:
        safe_log(f"Error reading version file: {e}", logging.WARNING)
        return "MINT Beta 2c 26092025 Features"


def get_latest_version() -> str:
    """Get latest version from GitHub"""
    try:
        url = "https://raw.githubusercontent.com/BarioIsCoding/BetterMintModded/refs/heads/main/version"
        
        # Create request with user agent to avoid potential blocking
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'BetterMintModded/MINT Beta 2c 26092025 Features')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                latest_version = response.read().decode('utf-8').strip()
                safe_log(f"Latest version from GitHub: {latest_version}")
                return latest_version
            else:
                safe_log(f"HTTP {response.status} when checking for updates", logging.WARNING)
                return None
                
    except urllib.error.URLError as e:
        safe_log(f"Network error checking for updates: {e}", logging.WARNING)
        return None
    except Exception as e:
        safe_log(f"Error checking for updates: {e}", logging.WARNING)
        return None


def check_for_updates() -> bool:
    """Check for updates and return True if update is available"""
    try:
        current_version = get_current_version()
        latest_version = get_latest_version()
        
        if latest_version is None:
            safe_log("Could not check for updates - network or server issue")
            return False
        
        safe_log(f"Version check: Current={current_version}, Latest={latest_version}")
        
        # Simple string comparison - assumes semantic versioning
        if current_version != latest_version:
            safe_log(f"Update available: {current_version} -> {latest_version}")
            return True
        else:
            safe_log("You are running the latest version")
            return False
            
    except Exception as e:
        safe_log(f"Error during version check: {e}", logging.ERROR)
        return False


def show_update_dialog(current_version: str, latest_version: str) -> bool:
    """Show update dialog and return True if user wants to update"""
    try:
        # Try tkinter first to avoid QApplication conflicts
        import tkinter as tk
        from tkinter import messagebox
        
        # Create hidden root window
        root = tk.Tk()
        root.withdraw()
        
        # Show message box
        result = messagebox.askyesno(
            "BetterMint Modded - Update Available",
            f"A new version of BetterMint Modded is available!\n\n"
            f"Current version: {current_version}\n"
            f"Latest version: {latest_version}\n\n"
            f"Would you like to visit the download page?",
            icon='info'
        )
        
        root.destroy()
        return result
        
    except ImportError:
        # Fallback to console if tkinter not available
        safe_log("GUI libraries not available, using console prompt")
        print(f"\n{'='*50}")
        print("UPDATE AVAILABLE")
        print(f"{'='*50}")
        print(f"Current version: {current_version}")
        print(f"Latest version: {latest_version}")
        print(f"{'='*50}")
        
        while True:
            response = input("Would you like to visit the download page? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    except Exception as e:
        safe_log(f"Error showing update dialog: {e}", logging.ERROR)
        return False


def open_update_page():
    """Open the GitHub update page in default browser"""
    try:
        import webbrowser
        update_url = "https://github.com/BarioIsCoding/BetterMintModded/tree/main"
        webbrowser.open(update_url)
        safe_log(f"Opened update page: {update_url}")
    except Exception as e:
        safe_log(f"Error opening update page: {e}", logging.ERROR)
        print(f"Please visit: https://github.com/BarioIsCoding/BetterMintModded/tree/main")


def migrate_personalities_folder():
    """Migrate personalities folder from engines/rodent/personalities to root"""
    try:
        # Define source and destination paths
        source_dir = Path(PROJECT_ROOT) / "engines" / "rodent" / "personalities"
        dest_dir = Path(PROJECT_ROOT) / "personalities"
        
        # Check if source directory exists
        if not source_dir.exists():
            safe_log("No personalities folder found in engines/rodent/personalities")
            return True  # Not an error, just nothing to migrate
        
        safe_log(f"Found personalities folder at: {source_dir}")
        
        # Create destination directory if it doesn't exist
        dest_dir.mkdir(exist_ok=True)
        
        # Count files to migrate
        personality_files = list(source_dir.glob("*.txt"))
        if not personality_files:
            safe_log("No personality files (.txt) found to migrate")
            return True
        
        safe_log(f"Migrating {len(personality_files)} personality files...")
        
        # Migrate each personality file
        migrated_count = 0
        for personality_file in personality_files:
            try:
                dest_file = dest_dir / personality_file.name
                
                # If destination file already exists, skip it
                if dest_file.exists():
                    safe_log(f"Skipping {personality_file.name} - already exists in destination")
                    continue
                
                # Copy the file
                shutil.copy2(personality_file, dest_file)
                safe_log(f"Migrated: {personality_file.name}")
                migrated_count += 1
                
            except Exception as e:
                safe_log(f"Error migrating {personality_file.name}: {e}", logging.WARNING)
        
        if migrated_count > 0:
            safe_log(f"Successfully migrated {migrated_count} personality files")
            
            # Try to remove the source directory if it's empty
            try:
                remaining_files = list(source_dir.iterdir())
                if not remaining_files:
                    source_dir.rmdir()
                    safe_log("Removed empty source personalities directory")
                else:
                    safe_log(f"Source directory contains {len(remaining_files)} other files, keeping it")
            except Exception as e:
                safe_log(f"Could not remove source directory: {e}", logging.WARNING)
        else:
            safe_log("No files needed migration")
        
        return True
        
    except Exception as e:
        safe_log(f"Error during personalities migration: {e}", logging.ERROR)
        return False


def load_application_icon():
    """Load application icon from icons directory with fallback support"""
    try:
        from PySide6.QtGui import QIcon
        from PySide6.QtCore import QSize
        
        # FIXED: Import specific constants instead of import *
        try:
            from constants import ICON_DIR, ICON_FILES
        except ImportError:
            # Fallback if constants not available
            icons_dir = Path(PROJECT_ROOT) / "icons"
            icon_files = ["icon.png", "icon-16.png", "icon-32.png", "icon-48.png"]
            ICON_DIR = icons_dir
            ICON_FILES = icon_files
        
        icon = QIcon()
        icon_loaded = False
        
        for icon_file in ICON_FILES:
            icon_path = ICON_DIR / icon_file
            if icon_path.exists():
                safe_log(f"Loading icon: {icon_path}")
                
                # For PNG files with size indicators, add with specific size
                if icon_file.startswith("icon-") and icon_file.endswith(".png"):
                    try:
                        size_str = icon_file.replace("icon-", "").replace(".png", "")
                        size = int(size_str)
                        icon.addFile(str(icon_path), QSize(size, size))
                        icon_loaded = True
                    except ValueError:
                        # If size parsing fails, add without size
                        icon.addFile(str(icon_path))
                        icon_loaded = True
                else:
                    # Add without specific size for SVG, ICO, and generic PNG
                    icon.addFile(str(icon_path))
                    icon_loaded = True
        
        if icon_loaded:
            safe_log("Application icon loaded successfully")
            return icon
        else:
            safe_log("No icon files found in icons directory", logging.WARNING)
            return None
            
    except ImportError:
        safe_log("QIcon not available for icon loading", logging.WARNING)
        return None
    except Exception as e:
        safe_log(f"Error loading application icon: {e}", logging.WARNING)
        return None

def set_application_icon(app):
    """Set the application icon for taskbar and system"""
    try:
        icon = load_application_icon()
        if icon and not icon.isNull():
            app.setWindowIcon(icon)
            safe_log("Application icon set successfully")
            return True
        else:
            safe_log("Failed to set application icon - no valid icon found", logging.WARNING)
            return False
    except Exception as e:
        safe_log(f"Error setting application icon: {e}", logging.WARNING)
        return False
    
def setup_windows_taskbar_icon():
    """
    Set Windows App User Model ID to ensure custom taskbar icon shows
    Must be called BEFORE creating QApplication
    """
    if sys.platform == 'win32':
        try:
            import ctypes
            # Set unique App User Model ID for Windows taskbar grouping
            app_id = 'BetterMintTeam.BetterMintModded.ChessEngine.MINT Beta 2c 26092025 Features'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            safe_log("Windows App User Model ID set for taskbar icon")
            return True
        except Exception as e:
            safe_log(f"Failed to set Windows App User Model ID: {e}", logging.WARNING)
            return False
    return True

def setup_qt_application():
    """Set up Qt application with proper high DPI configuration"""
    try:
        safe_log("Setting up Qt application")

        # CRITICAL: Set Windows taskbar ID BEFORE creating QApplication
        setup_windows_taskbar_icon()

        # Import Qt components
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        
        # CRITICAL: Set high DPI attributes BEFORE creating QApplication
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Enable better high DPI scaling if available
        if hasattr(Qt, 'AA_Use96Dpi'):
            QApplication.setAttribute(Qt.AA_Use96Dpi, False)
            
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Set application metadata
        app.setApplicationName("BetterMint Modded")
        app.setApplicationVersion("MINT Beta 2c 26092025 Features")
        app.setOrganizationName("BetterMint Team")
        set_application_icon(app)
        
        # Enable proper shutdown behavior
        app.setQuitOnLastWindowClosed(True)
        
        safe_log("Qt application configured successfully")
        return app
        
    except ImportError as e:
        safe_log(f"CRITICAL: PySide6 not available: {e}", logging.CRITICAL)
        print("ERROR: PySide6 is required but not installed.")
        print("Install with: pip install PySide6")
        return None
    except Exception as e:
        safe_log(f"CRITICAL: Qt setup failed: {e}", logging.CRITICAL)
        return None

def initialize_enhanced_logging():
    """Initialize enhanced logging system if available"""
    try:
        # FIXED: Import specific constants instead of import *
        from constants import setup_logging, main_logger, APP_NAME, APP_VERSION
        
        # Set up enhanced logging
        setup_logging(
            log_level='INFO',
            enable_file_logging=True,
            enable_performance_logging=True
        )
        
        main_logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
        main_logger.info(f"Project root: {PROJECT_ROOT}")
        return main_logger
        
    except Exception as e:
        safe_log(f"Enhanced logging failed, using basic logging: {e}", logging.WARNING)
        return None

def check_dependencies():
    """Check for required dependencies and files"""
    safe_log("Checking dependencies")
    
    missing_components = []
    warnings = []
    
    # Check critical directories
    required_dirs = ['gui']
    for dir_name in required_dirs:
        dir_path = Path(PROJECT_ROOT) / dir_name
        if not dir_path.exists():
            missing_components.append(f"Directory: {dir_name}")
    
    # Check optional directories
    optional_dirs = ['engines', 'weights', 'templates', 'logs']
    for dir_name in optional_dirs:
        dir_path = Path(PROJECT_ROOT) / dir_name
        if not dir_path.exists():
            warnings.append(f"Optional directory missing: {dir_name}")
            # Create logs directory if missing
            if dir_name == 'logs':
                try:
                    dir_path.mkdir(exist_ok=True)
                    safe_log(f"Created {dir_name} directory")
                except Exception:
                    pass
    
    # Check for engine executables (with fallback paths)
    engine_warnings = []
    try:
        # Try to get paths from constants, fallback to defaults
        try:
            from constants import STOCKFISH_PATH, LEELA_PATH
        except ImportError:
            # Fallback paths
            STOCKFISH_PATH = Path(PROJECT_ROOT) / 'engines' / 'stockfish' / 'stockfish.exe'
            LEELA_PATH = Path(PROJECT_ROOT) / 'engines' / 'leela' / 'lc0.exe'
        
        if not Path(STOCKFISH_PATH).exists():
            engine_warnings.append("Stockfish engine not found")
        if not Path(LEELA_PATH).exists():
            engine_warnings.append("Leela Chess Zero engine not found")
            
        if engine_warnings:
            warnings.extend(engine_warnings)
            if len(engine_warnings) == 2:
                warnings.append("No chess engines available - limited functionality")
                
    except Exception:
        warnings.append("Could not check engine availability")
    
    # Report results
    if missing_components:
        safe_log(f"CRITICAL: Missing required components: {missing_components}", logging.ERROR)
        return False
    
    if warnings:
        for warning in warnings:
            safe_log(f"WARNING: {warning}", logging.WARNING)
    
    safe_log("Dependency check completed")
    return True

def create_main_window():
    """Create the main application window with QUiLoader hang workaround"""
    try:
        safe_log("Creating main window")
        
        # CRITICAL FIX: Import GUI components AFTER QApplication is created
        # This prevents QUiLoader hanging issues on Windows when run from batch files
        safe_log("Importing GUI module (may take a moment on first run)")
        print("try")
        # Pre-import any QUiLoader-related components to work around PySide6 bug
        try:
            from PySide6.QtUiTools import QUiLoader
            # Create a dummy loader to initialize the QUiLoader subsystem
            dummy_loader = QUiLoader()
            safe_log("QUiLoader subsystem initialized successfully")
            del dummy_loader  # Clean up
        except Exception as loader_error:
            safe_log(f"QUiLoader pre-initialization failed: {loader_error}", logging.WARNING)
            # Continue anyway - the GUI module might not use QUiLoader
        
        # Ensure the GUI directory is in the Python path
        gui_dir = os.path.join(PROJECT_ROOT, 'gui')
        if gui_dir not in sys.path:
            sys.path.insert(0, gui_dir)
            safe_log(f"Added GUI directory to path: {gui_dir}")
        
        # Now import the main GUI module
        try:
            # Try direct import first
            from gui.main_window import ChessEngineGUI
            safe_log("Successfully imported ChessEngineGUI from gui.main_window")
        except ImportError as import_error:
            safe_log(f"Direct import failed: {import_error}", logging.WARNING)
            # Try alternative import methods
            try:
                # Method 2: Import main_window module then get the class
                import gui.main_window as main_window_module
                ChessEngineGUI = main_window_module.ChessEngineGUI
                safe_log("Successfully imported via module import")
            except ImportError:
                # Method 3: Direct file import (last resort)
                import importlib.util
                main_window_path = os.path.join(PROJECT_ROOT, 'gui', 'main_window.py')
                spec = importlib.util.spec_from_file_location("main_window", main_window_path)
                main_window_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(main_window_module)
                ChessEngineGUI = main_window_module.ChessEngineGUI
                safe_log("Successfully imported via file import")
        
        # Create main window
        safe_log("Instantiating main window...")
        window = ChessEngineGUI()
        
        safe_log(f"Main window created: {window.windowTitle()}")
        return window
        
    except ImportError as e:
        safe_log(f"CRITICAL: Failed to import GUI components: {e}", logging.CRITICAL)
        safe_log(f"Import traceback: {traceback.format_exc()}", logging.DEBUG)
        
        # Try to provide more helpful error information
        if "gui.main_window" in str(e):
            safe_log("The gui/main_window.py file may be missing or have import issues", logging.ERROR)
        elif "QUiLoader" in str(e):
            safe_log("QUiLoader import failed - this is a known PySide6 issue", logging.ERROR)
            safe_log("Try downgrading to PySide6 6.5.3 or using PySide6-Essentials", logging.ERROR)
        
        return None
    except Exception as e:
        safe_log(f"CRITICAL: Failed to create main window: {e}", logging.CRITICAL)
        safe_log(f"Window creation traceback: {traceback.format_exc()}", logging.DEBUG)
        return None

def main():
    """Main entry point with comprehensive error handling"""
    
    # Initialize logging
    logger = initialize_enhanced_logging()
    log_func = logger.info if logger else safe_log
    
    log_func("=" * 60)
    log_func("STARTING BetterMint Modded vMINT Beta 2c 26092025 Features")
    log_func("=" * 60)
    
    exit_code = 1  # Default to error
    app = None
    window = None
    
    try:
        # Phase 0: Migrate personalities folder
        log_func("Phase 0: Migrating personalities folder")
        migrate_personalities_folder()
        
        # Phase 0.5: Check for updates
        log_func("Phase 0.5: Checking for updates")
        try:
            if check_for_updates():
                current_version = get_current_version()
                latest_version = get_latest_version()
                
                if latest_version and show_update_dialog(current_version, latest_version):
                    open_update_page()
                    # Continue running the application after showing update
                    log_func("Update dialog shown, continuing with application startup")
        except Exception as e:
            safe_log(f"Update check failed: {e}", logging.WARNING)
            log_func("Continuing with application startup despite update check failure")
        
        # Phase 1: Dependency check
        log_func("Phase 1: Dependency validation")
        if not check_dependencies():
            safe_log("CRITICAL: Dependency check failed", logging.ERROR)
            print("\nERROR: Missing required components.")
            print("Please ensure all necessary files are present.")
            input("Press Enter to exit...")
            return 1
        
        # Phase 2: Qt application setup
        log_func("Phase 2: Qt application initialization")
        app = setup_qt_application()
        if not app:
            return 1
        
        # Phase 3: Main window creation (AFTER QApplication is created)
        log_func("Phase 3: Main window creation")
        window = create_main_window()
        if not window:
            safe_log("CRITICAL: Main window creation failed", logging.ERROR)
            return 1
        
        # Phase 4: Display window
        log_func("Phase 4: Displaying main window")
        try:
            window.show()
            
            startup_duration = time.time() - STARTUP_TIME
            log_func(f"Application started successfully in {startup_duration:.2f} seconds")
            log_func(f"Main window visible: {window.isVisible()}")
            
        except Exception as e:
            safe_log(f"ERROR: Failed to display window: {e}", logging.ERROR)
            return 1
        
        # Phase 5: Run event loop
        log_func("Phase 5: Starting Qt event loop")
        try:
            exit_code = app.exec()
            log_func(f"Application exited with code: {exit_code}")
            
        except KeyboardInterrupt:
            log_func("Application interrupted by user")
            exit_code = 0
            
    except Exception as e:
        safe_log(f"CRITICAL ERROR in main(): {e}", logging.CRITICAL)
        safe_log(f"Main error traceback: {traceback.format_exc()}", logging.DEBUG)
        
        # Show error dialog if Qt is available
        try:
            if app and window:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    window,
                    "Critical Error",
                    f"BetterMint Modded encountered a critical error:\n\n{str(e)}\n\n"
                    "Check the console and log files for detailed information."
                )
        except Exception:
            # Fallback to console error display
            print(f"\nCRITICAL ERROR: {e}")
            print("Check logs for detailed information.")
            input("Press Enter to exit...")
        
        exit_code = 1
    
    finally:
        # Cleanup
        try:
            if window:
                window.close()
            if app:
                app.quit()
        except Exception as cleanup_error:
            safe_log(f"Cleanup error: {cleanup_error}", logging.WARNING)
        
        total_runtime = time.time() - STARTUP_TIME
        log_func(f"Total runtime: {total_runtime:.2f} seconds")
        log_func("=" * 60)
    
    return exit_code

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler for unhandled exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Handle Ctrl+C gracefully
        safe_log("Application interrupted by user", logging.INFO)
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log unhandled exception
    safe_log("UNHANDLED EXCEPTION:", logging.CRITICAL)
    safe_log(f"Type: {exc_type.__name__}", logging.CRITICAL)
    safe_log(f"Value: {exc_value}", logging.CRITICAL)
    safe_log(f"Traceback: {''.join(traceback.format_tb(exc_traceback))}", logging.CRITICAL)
    
    # Show error to user
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Unhandled Exception",
            f"An unhandled exception occurred:\n\n{exc_type.__name__}: {exc_value}\n\n"
            "Check the console and log files for detailed information."
        )
    except Exception:
        print(f"\nUNHANDLED EXCEPTION: {exc_type.__name__}: {exc_value}")
        print("Check logs for detailed information.")
    
    # Call the default exception handler
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

if __name__ == "__main__":
    # Set up global exception handler
    sys.excepthook = handle_exception
    
    # Ensure we're in the correct directory
    os.chdir(PROJECT_ROOT)
    
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as fatal_error:
        safe_log(f"FATAL ERROR: {fatal_error}", logging.CRITICAL)
        print(f"FATAL ERROR: {fatal_error}")
        sys.exit(1)
