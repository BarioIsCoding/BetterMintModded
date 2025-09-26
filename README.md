# BetterMint Modded 🍡
**A modification of BotSolver's BetterMint** 💚

~~Releases as BETA on **Sunday**. Stay tuned!~~ Released!

New update 26/09/2025: Improvements

`MINT Beta 2c 26092025 Features`

What's new?
* Improved startup stability
* Quality of life
* **Custom engines**
* Extension fix
* Engine store
* Removed Playwright Chromium browser
* Extension installation instructions

![BetterMint Modded Logo](https://github.com/BarioIsCoding/BetterMintModded/blob/main/EngineWS/icons/icon-256.png?raw=true)

*Bridging the gap between chess engines and human play*

Note: In contrast to ChessMint, __this is not a cheating tool.__ This is a chess learning tool to improve your knowledge and skyrocket your elo! Do **not** use this in real games.

![BetterMint Modded Logo](https://github.com/BarioIsCoding/BetterMintModded/blob/main/EngineWS/icons/icon-32.png?raw=true)   ![Downloads](https://img.shields.io/github/downloads/BarioIsCoding/BetterMintModded/total?style=for-the-badge)

Please join the [Discord server](https://discord.gg/BGmNdcXvt3) for bugs, pull request, future updates, BETA access, and conversation.

* Free to use
* No spyware
* No microtransactions
* No ads
* No donations required
  
Just a gift by the chess community! 🎁

## Examples 🫱🏻‍🫲🏻
<img width="480" height="480" alt="image" src="https://github.com/user-attachments/assets/9a91bb2e-0826-44f4-807b-fdb0282fd133" />
<img width="720" height="480" alt="image" src="https://github.com/user-attachments/assets/4d3b3121-e16e-4e54-80dc-d5b53c97efdb" />

## Features 🔥
### 🤖 Rich Engine Configuration
* Chess Engine (Stockfish/Leela/Maia/Rodent)
* Search Depth
* Analysis Lines (multipv)
* Mate Finder (broken)
### 📖 Learning Features & Visuals
* Opening Books
* Threat Arrows (customizable)
* Analysis Badges
* Evaluation Bar 
### ♟️ Automove & Premoves
* Random Best Move
* Probabilistic line selection
* Max Premoves
### 🧠 Intelligence & Personality 
* Customizable timing (Base/Random/Multiplier/Divider)
* Aggressiveness contempt
* Passiveness contempt
* Other preferences (trading, capture, castle, en passant, promotion)
* Prefer Early Castling
* Perfer Specific Castle Side (Kingside/Queenside)
* Prefer Pins
* Individual Piece Preferences (Pawn, Knight, Bishop, Rook, Queen, King)
* Stalemate Probability
* Stay Equal Mode
* Always Promote to Queen
* Checkmate immediately
* Rodent premade personalities
* Rodent custom personalities
### ♥️ Quality of Life 
* Web Interface (UCI Log)
* Verbose logging
* Performance monitoring
* Auto-Save Settings
* Clear Cache
* Reset to default
* Auto extension configuration via Playwright's Chromium
* Advanced Cleanup functions
* Connection Monitor (Activity Log)
* Profile & Settings Import/Export
* BetterMint Config Backwards Compatibility (WIP)
* Config encryption (WIP)
* Fully free forever

## 🚀 Installation

### Prerequisites
- **Python 3.8+** (recommended: Python 3.9-3.11)
- **Windows 10/11** (primary support)
- **Google Chrome** (for extension)
- **4GB+ RAM** (8GB+ recommended for Leela)

### Quick Start

1. **Download via MintyInstall (in Releases)**

2. **Run the tool**:
   ```batch
   cd BetterMint/EngineWS
   RunWindows.bat
   ```

### Manual Installation (MintyInstall still required)

If RunWindows.bat or RunUnix.sh fails:

```batch
# Navigate to the EngineWS directory
cd BetterMint/EngineWS

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Chrome Extension Setup

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `BetterMint/BetterMintModded` folder
5. The extension should now appear in your extensions list

## 🛠️ Development

### Project Architecture
- **Frontend**: Chrome extension (JavaScript)
- **Backend**: Python FastAPI server
- **GUI**: PySide6 desktop application
- **Engines**: UCI protocol communication
- **AI Models**: Maia neural networks via Leela backend
  
### Contributing
This project is in early ALPHA. If you encounter issues:
1. Check the console/log output
2. Verify all engines are properly installed
3. Ensure Chrome extension permissions are granted
4. Report bugs with detailed logs

## 📋 Requirements

### System Requirements
- **OS**: Windows 10/11 (primary), Linux/macOS (experimental)
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 2GB free space (more for additional engines/books)
- **Network**: Internet connection for extension functionality

### Python Dependencies
See `requirements.txt` for complete list. Key dependencies:
- `PySide6`: GUI framework
- `fastapi`: Web server
- `websockets`: Real-time communication
- `python-chess`: Chess logic and UCI communication
- `numpy`: Numerical operations

## 🎓 Attribution

BetterMint Modded is a fork of:
- **BotSolver's BetterMint** (original fork)
- **thedemon's ChessMint** (original base project)

### Chess Engines
- **Stockfish**: Open source chess engine
- **Leela Chess Zero**: Neural network chess engine
- **Maia**: Human-like chess AI from Microsoft Research

### Special Thanks
- Original ChessMint developers
- BotSolver for the BetterMint fork
- Stockfish and Leela development teams
- Maia research team at Microsoft

## 📜 License

This project is free and open source. 

**Note**: Individual chess engines and neural networks may have their own licenses. Please respect the licensing terms of:
- Stockfish (GPL v3)
- Leela Chess Zero (GPL v3)
- Rodent (GPL v3)
- Maia weights (research license)

We unfortunately use a restrictive copyleft license due to the `python-chess` package.
In the future, we may replace the library with our custom code (almost done!) to make this project fully open!

## 🚨 Disclaimer

**ALPHA SOFTWARE**: This is early alpha software. Expect bugs and incomplete features.

**Usage**: This tool is designed for learning and analysis. Use responsibly and in accordance with chess platform terms of service.

**Support**: As this is a small community project, support is limited. Please be patient and provide detailed bug reports.

We are not affiliated, associated, authorized, endorsed by, or in any way officially connected with Chess.com, BotSolvers, sakiodre (formerly thedemons), or any of its subsidiaries or its affiliates. The official Chess.com website can be found at https://chess.com.
The name Chess.com as well as related names, marks, emblems and images are registered trademarks of their respective owners.



## 💶 Donate
You can donate via **XMR** to support this project: 
`88BCjwGV46FAdGXGKRssWd5XL4knBCmgS8w4ird4UeWH9xXqG9nr6yL3coFb6UxWAFFxuX2acTcvUAyN3utGZtcVUskGPAT`


*BetterMint Modded - Bridging the gap between chess engines and human play*
