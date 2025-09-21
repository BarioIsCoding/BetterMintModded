"""
Chess.com web view integration for BetterMint Modded GUI
Playwright-powered browser automation with extension support and visual streaming
"""

import os
import asyncio
import logging
import traceback
import time
import threading
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import io

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile

# Image processing for screenshots
try:
    from PIL import Image, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Playwright with availability checking
try:
    from playwright.async_api import (
        async_playwright, Browser, BrowserContext, Page, 
        TimeoutError as PlaywrightTimeoutError
    )
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("Playwright not available - browser integration disabled")
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None
    Browser = None
    BrowserContext = None
    Page = None
    PlaywrightTimeoutError = Exception


class PlaywrightChessController(QObject):
    """Manages a real Chrome browser with full extension support via Playwright"""
    
    # Qt Signals for communication
    page_loaded = Signal(str)  # URL loaded
    extension_data_updated = Signal(dict)  # Extension sent data
    move_suggested = Signal(str)  # Best move from extension
    error_occurred = Signal(str)  # Error message
    connection_status_changed = Signal(bool)  # Connected/disconnected
    initialization_progress = Signal(str)  # Progress updates during init
    screenshot_updated = Signal(str)  # Base64 encoded screenshot
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.extension_loaded = False
        self.loop = None
        self.thread = None
        self.is_closing = False
        self.polling_task = None
        self.screenshot_task = None
        self.last_screenshot_time = 0
        
    async def initialize(self):
        """Initialize Playwright and launch browser with extension"""
        try:
            if not PLAYWRIGHT_AVAILABLE:
                raise ImportError("Playwright is not installed. Install with: pip install playwright")
            
            self.initialization_progress.emit("Starting Playwright...")
            
            # Initialize Playwright
            self.playwright = await async_playwright().start()
            logger.info("Playwright started successfully")
            
            self.initialization_progress.emit("Validating extension path...")
            
            # Get and validate extension path
            script_dir = Path(__file__).parent.parent.parent
            extension_dir = script_dir / "BetterMintModded"
            
            if not extension_dir.exists():
                raise FileNotFoundError(f"Extension directory not found at: {extension_dir}")
            
            if not (extension_dir / "manifest.json").exists():
                raise FileNotFoundError(f"Extension manifest.json not found in: {extension_dir}")
            
            logger.info(f"Extension found at: {extension_dir}")
            
            self.initialization_progress.emit("Preparing Chrome profile...")
            
            # Prepare Chrome profile directory
            profile_dir = script_dir / "chrome_profile"
            profile_dir.mkdir(exist_ok=True)
            
            self.initialization_progress.emit("Launching Chrome browser...")
            
            # Launch Chrome with extension and reasonable timeout
            try:
                self.context = await asyncio.wait_for(
                    self.playwright.chromium.launch_persistent_context(
                        user_data_dir=str(profile_dir),
                        headless=False,  # Keep visible for debugging
                        args=[
                            f'--load-extension={extension_dir}',
                            f'--disable-extensions-except={extension_dir}',
                            '--disable-web-security',  # For development
                            '--allow-running-insecure-content',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-infobars',
                            '--no-first-run',
                        ],
                        viewport={'width': 1280, 'height': 720},
                        ignore_default_args=['--disable-extensions']
                    ),
                    timeout=30.0  # 30 second timeout for browser launch
                )
            except asyncio.TimeoutError:
                raise TimeoutError("Chrome browser launch timed out after 30 seconds")
            
            logger.info("Chrome browser launched successfully")
            
            self.initialization_progress.emit("Creating browser page...")
            
            # Create page
            self.page = await self.context.new_page()
            logger.info("Browser page created")
            
            self.initialization_progress.emit("Setting up extension bridge...")
            
            # Set up extension communication
            await self.setup_extension_bridge()
            
            self.initialization_progress.emit("Navigating to Chess.com...")
            
            # Navigate to Chess.com with timeout
            try:
                await asyncio.wait_for(
                    self.page.goto('https://www.chess.com', wait_until='networkidle'),
                    timeout=15.0
                )
            except asyncio.TimeoutError:
                logger.warning("Chess.com navigation timed out, but continuing...")
                await self.page.goto('https://www.chess.com')
            
            logger.info("Navigation to Chess.com completed")
            
            self.extension_loaded = True
            self.connection_status_changed.emit(True)
            self.page_loaded.emit('https://www.chess.com')
            self.initialization_progress.emit("Ready - Chess.com loaded with extension support")
            
            # Start data polling in background (non-blocking)
            self.polling_task = asyncio.create_task(self.start_data_polling())
            
            # Start screenshot streaming if PIL is available
            if PIL_AVAILABLE:
                self.screenshot_task = asyncio.create_task(self.start_screenshot_streaming())
            else:
                logger.warning("PIL not available - screenshot streaming disabled")
            
        except Exception as e:
            error_msg = f"Failed to initialize Playwright: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.error_occurred.emit(error_msg)
            self.connection_status_changed.emit(False)
            self.initialization_progress.emit(f"Error: {str(e)}")
            
            # Cleanup on error
            await self.cleanup_on_error()
    
    async def cleanup_on_error(self):
        """Clean up resources when initialization fails"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def setup_extension_bridge(self):
        """Set up communication bridge with the extension"""
        if not self.page:
            return
            
        try:
            # Inject bridge script to communicate with extension
            await self.page.add_init_script("""
                // Bridge for extension communication
                window.betterMintBridge = {
                    sendToQt: (data) => {
                        window.qtBridge = window.qtBridge || [];
                        window.qtBridge.push(data);
                    },
                    
                    onExtensionData: (callback) => {
                        window.addEventListener('betterMintExtensionData', callback);
                    }
                };
                
                // Listen for extension messages
                window.addEventListener('message', (event) => {
                    if (event.source !== window) return;
                    
                    if (event.data.type === 'BETTER_MINT_EXTENSION_DATA') {
                        window.betterMintBridge.sendToQt(event.data.payload);
                        window.dispatchEvent(new CustomEvent('betterMintExtensionData', {
                            detail: event.data.payload
                        }));
                    }
                });
                
                console.log('BetterMint bridge initialized');
            """)
            logger.info("Extension bridge set up successfully")
        except Exception as e:
            logger.error(f"Failed to setup extension bridge: {e}")
    
    async def start_screenshot_streaming(self):
        """Start taking periodic screenshots for streaming"""
        logger.info("Starting screenshot streaming...")
        
        try:
            while self.page and not self.page.is_closed() and not self.is_closing:
                current_time = time.time()
                
                # Take screenshot every 1 second
                if current_time - self.last_screenshot_time >= 1.0:
                    try:
                        # Take screenshot
                        screenshot_bytes = await self.page.screenshot(
                            type='png',
                            full_page=False,
                            timeout=3000  # 3 second timeout
                        )
                        
                        if screenshot_bytes:
                            # Process screenshot in a non-blocking way
                            processed_screenshot = await self.process_screenshot(screenshot_bytes)
                            if processed_screenshot:
                                self.screenshot_updated.emit(processed_screenshot)
                            
                        self.last_screenshot_time = current_time
                        
                    except Exception as e:
                        if not self.is_closing:
                            logger.debug(f"Screenshot error: {e}")  # Use debug level to avoid spam
                
                await asyncio.sleep(0.2)  # Check every 200ms, but only capture every 1s
                
        except Exception as e:
            if not self.is_closing:
                logger.error(f"Screenshot streaming crashed: {e}")
        finally:
            logger.info("Screenshot streaming stopped")
    
    async def process_screenshot(self, screenshot_bytes: bytes) -> Optional[str]:
        """Process screenshot with blur effect and convert to base64"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            # Resize for performance (maintain aspect ratio)
            max_width = 800
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.LANCZOS)
            
            # Apply gentle blur (CPU-friendly)
            blurred_image = image.filter(ImageFilter.GaussianBlur(radius=3))
            
            # Convert back to bytes
            buffer = io.BytesIO()
            blurred_image.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            # Encode to base64
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{base64_image}"
            
        except Exception as e:
            logger.debug(f"Screenshot processing error: {e}")
            return None
    
    async def start_data_polling(self):
        """Start polling for extension data (runs in background)"""
        logger.info("Starting data polling...")
        
        try:
            while self.page and not self.page.is_closed() and not self.is_closing:
                try:
                    # Get data from extension bridge
                    bridge_data = await self.page.evaluate("() => window.qtBridge || []")
                    
                    if bridge_data:
                        for data in bridge_data:
                            self.extension_data_updated.emit(data)
                        
                        # Clear processed data
                        await self.page.evaluate("() => window.qtBridge = []")
                    
                    # Check for best moves
                    best_move = await self.page.evaluate("""
                        () => {
                            const moveElement = document.querySelector('.best-move-indicator');
                            return moveElement ? moveElement.textContent : null;
                        }
                    """)
                    
                    if best_move:
                        self.move_suggested.emit(best_move)
                        
                except Exception as e:
                    if not self.is_closing:
                        logger.error(f"Polling error: {e}")
                
                await asyncio.sleep(1.5)  # Poll every 500ms
                
        except Exception as e:
            if not self.is_closing:
                logger.error(f"Data polling crashed: {e}")
        finally:
            logger.info("Data polling stopped")
    
    async def make_move(self, move: str):
        """Make a chess move on the board"""
        if not self.page:
            return False
            
        try:
            # Execute move via extension or direct DOM manipulation
            result = await self.page.evaluate(f"""
                (move) => {{
                    if (window.BetterMintExtension && window.BetterMintExtension.makeMove) {{
                        return window.BetterMintExtension.makeMove(move);
                    }}
                    // Fallback to direct move execution
                    return false;
                }}
            """, move)
            
            return result
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to make move: {str(e)}")
            return False
    
    async def get_game_state(self) -> Dict[str, Any]:
        """Get current game state from Chess.com"""
        if not self.page:
            return {}
            
        try:
            game_state = await self.page.evaluate("""
                () => {
                    // Extract game state from Chess.com's page
                    const board = document.querySelector('.board');
                    const gameInfo = document.querySelector('.game-info');
                    
                    return {
                        boardState: board ? board.dataset.fen || 'unknown' : 'no-board',
                        isPlayerTurn: document.querySelector('.clock.player-clock.active') ? true : false,
                        gameType: gameInfo ? gameInfo.textContent.trim() : 'unknown',
                        timeRemaining: document.querySelector('.clock-time') ? 
                            document.querySelector('.clock-time').textContent : 'unknown'
                    };
                }
            """)
            
            return game_state
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to get game state: {str(e)}")
            return {}
    
    async def close(self):
        """Clean up Playwright resources"""
        self.is_closing = True
        logger.info("Starting Playwright cleanup...")
        
        try:
            # Cancel polling task
            if self.polling_task:
                self.polling_task.cancel()
                try:
                    await self.polling_task
                except asyncio.CancelledError:
                    pass
            
            # Cancel screenshot task
            if self.screenshot_task:
                self.screenshot_task.cancel()
                try:
                    await self.screenshot_task
                except asyncio.CancelledError:
                    pass
            
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            logger.info("Playwright cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def start_async_loop(self):
        """Start the async event loop in a separate thread"""
        def run_loop():
            print("DEBUG: Starting async loop thread...")
            try:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                print("DEBUG: Created new event loop")
                
                # Start initialization as a task (non-blocking)
                init_task = self.loop.create_task(self.initialize())
                print("DEBUG: Created initialization task")
                
                # Run the loop
                self.loop.run_forever()
                
            except Exception as e:
                error_msg = f"Async loop error: {e}"
                print(f"DEBUG: {error_msg}")
                logger.error(error_msg)
                # Use Qt.QueuedConnection for thread-safe signal emission
                self.error_occurred.emit(f"Async loop failed: {str(e)}")
            finally:
                print("DEBUG: Async loop ended")
                logger.info("Async loop ended")
        
        print("DEBUG: About to start thread...")
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()
        print("DEBUG: Thread started")
    
    def stop_async_loop(self):
        """Stop the async event loop"""
        if self.loop and self.loop.is_running():
            # Schedule cleanup and loop stop
            future = asyncio.run_coroutine_threadsafe(self.close(), self.loop)
            try:
                future.result(timeout=5.0)  # Wait up to 5 seconds for cleanup
            except:
                logger.warning("Cleanup timed out")
            
            self.loop.call_soon_threadsafe(self.loop.stop)


class EnhancedChessComWebView(QWebEngineView):
    """Enhanced web view that works with Playwright backend"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        print("DEBUG: EnhancedChessComWebView initializing...")
        
        # Initialize attributes first
        self.is_playwright_active = False
        self.current_screenshot_b64 = ""
        
        # Initialize Playwright controller only if available
        if PLAYWRIGHT_AVAILABLE:
            print("DEBUG: Playwright is available, creating controller...")
            self.playwright_controller = PlaywrightChessController(self)
            self.setup_controller_connections()
        else:
            print("DEBUG: Playwright not available")
            self.playwright_controller = None
        
        # Create basic WebView for GUI
        self.setup_webview()
        
        # Auto-start the browser after a short delay
        if self.playwright_controller:
            print("DEBUG: Setting up auto-start timer...")
            QTimer.singleShot(50, self.start_playwright_browser)  # Start after 1 second
        
    def setup_controller_connections(self):
        """Connect Playwright controller signals"""
        if not self.playwright_controller:
            return
            
        self.playwright_controller.page_loaded.connect(self.on_playwright_page_loaded)
        self.playwright_controller.extension_data_updated.connect(self.on_extension_data)
        self.playwright_controller.move_suggested.connect(self.on_move_suggested)
        self.playwright_controller.error_occurred.connect(self.on_error)
        self.playwright_controller.connection_status_changed.connect(self.on_connection_status_changed)
        self.playwright_controller.initialization_progress.connect(self.on_initialization_progress)
        self.playwright_controller.screenshot_updated.connect(self.on_screenshot_updated)
    
    def get_status_html(self):
        """Generate the HTML template for status display"""
        return f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    
                    body {{ 
                        background: #1a1a1a; 
                        color: #fff; 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                        height: 100vh;
                        overflow: hidden;
                        position: relative;
                    }}
                    
                    .background {{
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background-image: url('{self.current_screenshot_b64}');
                        background-size: cover;
                        background-position: center;
                        background-repeat: no-repeat;
                        filter: blur(3px);
                        transform: scale(1.05);
                        z-index: 1;
                        transition: background-image 0.3s ease;
                    }}
                    
                    .overlay {{
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0, 0, 0, 0.7);
                        z-index: 2;
                    }}
                    
                    .container {{
                        position: relative;
                        z-index: 3;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        padding: 20px;
                        text-align: center;
                    }}
                    
                    .main-message {{
                        background: rgba(45, 45, 45, 0.9);
                        padding: 30px;
                        border-radius: 12px;
                        border: 2px solid #4CAF50;
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                        backdrop-filter: blur(10px);
                        max-width: 500px;
                        margin-bottom: 20px;
                    }}
                    
                    .logo {{
                        font-size: 28px;
                        font-weight: bold;
                        color: #4CAF50;
                        margin-bottom: 15px;
                        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
                    }}
                    
                    .instruction {{
                        font-size: 18px;
                        color: #ffffff;
                        margin-bottom: 15px;
                        font-weight: 500;
                    }}
                    
                    .status {{
                        background: rgba(30, 30, 30, 0.8);
                        padding: 15px;
                        border-radius: 8px;
                        margin: 15px 0;
                        border-left: 4px solid #4CAF50;
                        font-size: 14px;
                        color: #e0e0e0;
                    }}
                    
                    .status.error {{
                        border-left-color: #f44336;
                        color: #ffcccb;
                    }}
                    
                    .progress {{
                        background: rgba(60, 60, 60, 0.8);
                        height: 8px;
                        border-radius: 4px;
                        margin: 15px 0;
                        overflow: hidden;
                        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
                    }}
                    
                    .progress-bar {{
                        height: 100%;
                        background: linear-gradient(90deg, #4CAF50, #45a049);
                        width: 0%;
                        transition: width 0.3s ease;
                        box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
                    }}
                    
                    .hint {{
                        font-size: 12px;
                        color: #888;
                        margin-top: 15px;
                        font-style: italic;
                    }}
                    
                    .browser-preview {{
                        position: fixed;
                        bottom: 20px;
                        right: 20px;
                        width: 200px;
                        height: 120px;
                        border: 2px solid #4CAF50;
                        border-radius: 8px;
                        background: rgba(0, 0, 0, 0.8);
                        overflow: hidden;
                        z-index: 4;
                        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
                    }}
                    
                    .browser-preview .preview-image {{
                        width: 100%;
                        height: 100%;
                        object-fit: cover;
                        filter: brightness(0.8);
                    }}
                    
                    .browser-preview .preview-label {{
                        position: absolute;
                        bottom: 0;
                        left: 0;
                        right: 0;
                        background: rgba(0, 0, 0, 0.9);
                        color: #4CAF50;
                        font-size: 10px;
                        padding: 2px 6px;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="background" id="background"></div>
                <div class="overlay"></div>
                
                <div class="container">
                    <div class="main-message">
                        <div class="logo">BetterMint Modded</div>
                        <div class="instruction">Please check the opened Chromium window</div>
                        <div class="status" id="status">Initializing browser...</div>
                        <div class="progress">
                            <div class="progress-bar" id="progress"></div>
                        </div>
                        <div class="hint">The Chess.com interface will open in a separate Chrome window with the BetterMint extension loaded</div>
                    </div>
                </div>
                
                <div class="browser-preview" id="preview" style="display: none;">
                    <img class="preview-image" id="preview-image" src="" alt="Browser Preview">
                    <div class="preview-label">Live Preview</div>
                </div>
                
                <script>
                    // Update background image function
                    function updateBackground(imageData) {{
                        const background = document.getElementById('background');
                        if (imageData && imageData.length > 0) {{
                            background.style.backgroundImage = `url(${{imageData}})`;
                            
                            // Show preview
                            const preview = document.getElementById('preview');
                            const previewImage = document.getElementById('preview-image');
                            previewImage.src = imageData;
                            preview.style.display = 'block';
                        }}
                    }}
                    
                    // Function to be called from Qt
                    window.updateScreenshot = updateBackground;
                </script>
            </body>
        </html>
        """
    
    def setup_webview(self):
        """Set up the Qt WebView component"""
        # Create custom profile for the Qt view (status display)
        self.profile = QWebEngineProfile("ChessComStatus", self)
        self.profile.setPersistentStoragePath(os.path.join(os.getcwd(), "webview_storage"))
        
        # Create page with custom profile
        self.page_obj = QWebEnginePage(self.profile, self)
        self.setPage(self.page_obj)
        
        # Load initial status page
        if PLAYWRIGHT_AVAILABLE and PIL_AVAILABLE:
            html_content = self.get_status_html()
        elif PLAYWRIGHT_AVAILABLE and not PIL_AVAILABLE:
            html_content = """
                <html>
                    <head>
                        <style>
                            body { 
                                background: #1a1a1a; 
                                color: #fff; 
                                font-family: 'Segoe UI', Arial, sans-serif; 
                                text-align: center; 
                                padding: 50px;
                                margin: 0;
                            }
                            .container {
                                max-width: 600px;
                                margin: 0 auto;
                            }
                            h2 { 
                                color: #4CAF50; 
                                margin-bottom: 20px;
                            }
                            .warning {
                                background: #2d2d2d; 
                                padding: 20px; 
                                border-radius: 8px; 
                                margin: 20px 0;
                                border-left: 4px solid #ff9800;
                                color: #ffcc80;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h2>BetterMint Modded</h2>
                            <div>Please check the opened Chromium window</div>
                            <div class="warning">Note: Screenshot streaming disabled (PIL not available)</div>
                            <small>Install Pillow with: pip install Pillow</small>
                        </div>
                    </body>
                </html>
            """
        else:
            html_content = """
                <html>
                    <head>
                        <style>
                            body { 
                                background: #1a1a1a; 
                                color: #fff; 
                                font-family: Arial; 
                                text-align: center; 
                                padding: 50px; 
                            }
                        </style>
                    </head>
                    <body>
                        <h2>BetterMint Modded</h2>
                        <div style="color: #f44336;">Playwright not available</div>
                        <p>Install Playwright with: <code>pip install playwright</code></p>
                    </body>
                </html>
            """
        
        self.setHtml(html_content)
    
    def start_playwright_browser(self):
        """Start the Playwright-controlled browser"""
        if self.playwright_controller:
            self.playwright_controller.start_async_loop()
        else:
            self.on_error("Playwright not available - install with: pip install playwright")
    
    def on_playwright_page_loaded(self, url: str):
        """Handle Playwright page load"""
        self.is_playwright_active = True
        # Update the status view
        self.page().runJavaScript("""
            document.getElementById('status').innerHTML = 'Connected to Chess.com - Extension Active';
            document.getElementById('status').className = 'status';
            document.getElementById('progress').style.width = '100%';
        """)
    
    def on_initialization_progress(self, message: str):
        """Handle initialization progress updates"""
        # Estimate progress based on message content
        progress = 0
        if "Starting" in message:
            progress = 10
        elif "Validating" in message:
            progress = 20
        elif "Preparing" in message:
            progress = 30
        elif "Launching" in message:
            progress = 50
        elif "Creating" in message:
            progress = 70
        elif "Setting up" in message:
            progress = 80
        elif "Navigating" in message:
            progress = 90
        elif "Ready" in message:
            progress = 100
        
        # Escape quotes in the message for JavaScript
        escaped_message = message.replace("'", "\\'").replace('"', '\\"')
        
        self.page().runJavaScript(f"""
            document.getElementById('status').innerHTML = '{escaped_message}';
            document.getElementById('progress').style.width = '{progress}%';
        """)
    
    def on_screenshot_updated(self, screenshot_b64: str):
        """Handle new screenshot from Playwright"""
        self.current_screenshot_b64 = screenshot_b64
        
        # Update the background image
        self.page().runJavaScript(f"""
            if (window.updateScreenshot) {{
                window.updateScreenshot('{screenshot_b64}');
            }}
        """)
    
    def on_extension_data(self, data: dict):
        """Handle extension data updates"""
        logger.info(f"Extension data received: {data}")
        # Process extension data as needed
    
    def on_move_suggested(self, move: str):
        """Handle move suggestions from extension"""
        logger.info(f"Best move suggested: {move}")
        # Update UI or trigger auto-move logic
    
    def on_error(self, error: str):
        """Handle Playwright errors"""
        logger.error(f"Playwright error: {error}")
        # Escape quotes in the error message for JavaScript
        escaped_error = error.replace("'", "\\'").replace('"', '\\"')
        
        self.page().runJavaScript(f"""
            const statusEl = document.getElementById('status');
            statusEl.innerHTML = 'Error: {escaped_error}';
            statusEl.className = 'status error';
        """)
    
    def on_connection_status_changed(self, connected: bool):
        """Handle connection status changes"""
        self.is_playwright_active = connected
        status = "Connected to Chess.com" if connected else "Disconnected"
        color_class = "status" if connected else "status error"
        
        self.page().runJavaScript(f"""
            const statusEl = document.getElementById('status');
            statusEl.innerHTML = '{status}';
            statusEl.className = '{color_class}';
        """)
    
    def make_chess_move(self, move: str):
        """Make a move using Playwright (async wrapper)"""
        if not self.is_playwright_active or not self.playwright_controller:
            return False
            
        # Schedule the async operation with timeout
        if self.playwright_controller.loop:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.playwright_controller.make_move(move),
                    self.playwright_controller.loop
                )
                return future.result(timeout=5.0)
            except asyncio.TimeoutError:
                logger.error("Move timeout")
                return False
        return False
    
    def get_current_game_state(self) -> Dict[str, Any]:
        """Get game state using Playwright (async wrapper)"""
        if not self.is_playwright_active or not self.playwright_controller:
            return {}
            
        if self.playwright_controller.loop:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.playwright_controller.get_game_state(),
                    self.playwright_controller.loop
                )
                return future.result(timeout=5.0)
            except asyncio.TimeoutError:
                logger.error("Game state timeout")
                return {}
        return {}
    
    def closeEvent(self, event):
        """Clean up on close"""
        if self.playwright_controller:
            self.playwright_controller.stop_async_loop()
        super().closeEvent(event)


# Create alias for backward compatibility
ChessComWebView = EnhancedChessComWebView