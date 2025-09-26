"""
Settings management for BetterMint Modded
Updated to include comprehensive intelligence settings with disable and threshold controls
ENHANCED: Added Rodent IV personality support and threat arrows
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from models import IntelligenceSettings

class SettingsManager:
    """Manages application settings with persistence and Rodent personality support"""
    
    def __init__(self, settings_file: str = "betterMint_settings.json"):
        self.settings_file = settings_file
        self.personalities_dir = Path("personalities")
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
            "show-threat-arrows": False,  # NEW: Show threat arrows
            "max-player-threats": 5,      # NEW: Maximum player threat arrows
            "max-opponent-threats": 3,    # NEW: Maximum opponent threat arrows

            # Misc Settings
            "text-to-speech": False,
            "performance-monitoring": False,
            "auto-save-settings": True,
            "notification-level": "normal",
            
            # Text-to-Speech Settings
            "tts-rate": 150,                    # Speech rate in words per minute
            "tts-volume": 0.8,                  # Volume level (0.0 to 1.0)
            "tts-voice": "",                    # Selected voice name
            "tts-announce-player": True,        # Announce player moves
            "tts-announce-engine": True,        # Announce engine moves

            # Intelligence Settings - Complete Set with New Controls
            "intelligence_enabled": False,
            
            # NEW: Intelligence Control Settings
            "avoid_low_intelligence": False,    # Enable threshold checking
            "low_intelligence_threshold": -1.5, # Threshold for avoiding low intelligence (-3.0 to -1.0)
            
            # Move Multipliers
            "aggressiveness_contempt": 1.0,
            "passiveness_contempt": 1.0,
            "trading_preference": 0.0,
            "capture_preference": 1.0,
            "castle_preference": 1.0,
            "en_passant_preference": 1.0,
            "promotion_preference": 1.0,
            
            # Boolean Preferences
            "prefer_early_castling": False,
            "prefer_pins": False,
            "prefer_side_castle": False,
            "castle_side": None,  # "kingside", "queenside", or None
            
            # Piece Movement Preferences
            "pawn_preference": 1.0,
            "knight_preference": 1.0,
            "bishop_preference": 1.0,
            "rook_preference": 1.0,
            "queen_preference": 1.0,
            "king_preference": 1.0,
            
            # Emotional Behavior
            "stay_equal": False,
            "stalemate_probability": 0.0,
            "always_promote_queen": False,
            "checkmate_immediately": False,
            
            # NEW: Rodent IV Personality Settings
            "rodent_personalities_enabled": False,
            "selected_rodent_personality": "tal.txt",  # Default to Tal personality
        }
        self.settings = self.load_settings()
        self.intelligence_settings = self.load_intelligence_settings()
        self.ensure_personalities_directory()

    def ensure_personalities_directory(self):
        """Create personalities directory and default files if they don't exist"""
        try:
            self.personalities_dir.mkdir(exist_ok=True)
            
            # Create default Tal personality if it doesn't exist
            tal_file = self.personalities_dir / "tal.txt"
            if not tal_file.exists():
                tal_personality = """setoption name PawnValueMg value 90
setoption name KnightValueMg value 380
setoption name BishopValueMg value 390
setoption name RookValueMg value 530
setoption name QueenValueMg value 1160
setoption name PawnValueEg value 110
setoption name KnightValueEg value 360
setoption name BishopValueEg value 370
setoption name RookValueEg value 650
setoption name QueenValueEg value 1190
setoption name KeepPawn value 8
setoption name KeepKnight value 10
setoption name KeepBishop value 10
setoption name KeepRook value 0
setoption name KeepQueen value 20
setoption name BishopPairMg value 70
setoption name BishopPairEg value 70
setoption name KnightPair value -10
setoption name RookPair value -11
setoption name KnightLikesClosed value 5
setoption name RookLikesOpen value 3
setoption name ExchangeImbalance value 10
setoption name MinorVsQueen value 4
setoption name Material value 100
setoption name OwnAttack value 450
setoption name OppAttack value 100
setoption name OwnMobility value 75
setoption name OppMobility value 50
setoption name FlatMobility value 50
setoption name KingTropism value 80
setoption name PrimaryPstWeight value 58
setoption name SecondaryPstWeight value 40
setoption name PiecePressure value 190
setoption name PassedPawns value 127
setoption name PawnStructure value 90
setoption name Lines value 100
setoption name Outposts value 78
setoption name Space value 100
setoption name PawnShield value 189
setoption name PawnStorm value 181
setoption name DoubledPawnMg value -8
setoption name DoubledPawnEg value -21
setoption name IsolatedPawnMg value -7
setoption name IsolatedPawnEg value -7
setoption name IsolatedOnOpenMg value -13
setoption name BackwardPawnMg value -2
setoption name BackwardPawnEg value -1
setoption name BackwardOnOpenMg value -10
setoption name FianchBase value 13
setoption name FianchKing value 20
setoption name ReturningB value 10
setoption name PawnMass value 100
setoption name PawnChains value 100
setoption name PrimaryPstStyle value 4
setoption name SecondaryPstStyle value 1
setoption name blockedcpawn value -17
setoption name Contempt value 0
setoption name SlowMover value 100
setoption name Selectivity value 175
setoption name SearchSkill value 10
setoption name BookFilter value 20"""
                
                with open(tal_file, 'w', encoding='utf-8') as f:
                    f.write(tal_personality)
                print(f"Created default Tal personality: {tal_file}")
                
        except Exception as e:
            print(f"Error setting up personalities directory: {e}")

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or return defaults"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Clean up deprecated intelligence settings
                    self.clean_deprecated_intelligence_settings(loaded)
                    # Merge with defaults to ensure all keys exist
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
        return self.default_settings.copy()
    
    def clean_deprecated_intelligence_settings(self, settings: Dict[str, Any]):
        """Remove deprecated intelligence settings to avoid conflicts"""
        deprecated_keys = [
            "intelligence-aggressiveness",
            "intelligence-defensiveness", 
            "intelligence-trading-preference",
            "intelligence-stay-equal",
            "intelligence-human-timing",
            "intelligence-human-timing-divider",
            "intelligence-simple-thinking",
            "intelligence-simple-thinking-boost",
            "intelligence-trading_preference",
            "intelligence-stay_equal",
            "intelligence-human_timing",
            "intelligence-human_timing_divider",
            "intelligence-simple_thinking",
            "intelligence-simple_thinking_boost"
        ]
        
        for key in deprecated_keys:
            settings.pop(key, None)
        
        print("Cleaned up deprecated intelligence settings")

    def load_intelligence_settings(self) -> IntelligenceSettings:
        """Load intelligence settings from main settings"""
        try:
            intel_data = {
                'intelligence_enabled': self.settings.get('intelligence_enabled', False),
                
                # NEW: Intelligence Control Settings
                'avoid_low_intelligence': self.settings.get('avoid_low_intelligence', False),
                'low_intelligence_threshold': self.settings.get('low_intelligence_threshold', -1.5),
                
                'aggressiveness_contempt': self.settings.get('aggressiveness_contempt', 1.0),
                'passiveness_contempt': self.settings.get('passiveness_contempt', 1.0),
                'trading_preference': self.settings.get('trading_preference', 0.0),
                'capture_preference': self.settings.get('capture_preference', 1.0),
                'castle_preference': self.settings.get('castle_preference', 1.0),
                'en_passant_preference': self.settings.get('en_passant_preference', 1.0),
                'promotion_preference': self.settings.get('promotion_preference', 1.0),
                'prefer_early_castling': self.settings.get('prefer_early_castling', False),
                'prefer_pins': self.settings.get('prefer_pins', False),
                'prefer_side_castle': self.settings.get('prefer_side_castle', False),
                'castle_side': self.settings.get('castle_side', None),
                'pawn_preference': self.settings.get('pawn_preference', 1.0),
                'knight_preference': self.settings.get('knight_preference', 1.0),
                'bishop_preference': self.settings.get('bishop_preference', 1.0),
                'rook_preference': self.settings.get('rook_preference', 1.0),
                'queen_preference': self.settings.get('queen_preference', 1.0),
                'king_preference': self.settings.get('king_preference', 1.0),
                'stay_equal': self.settings.get('stay_equal', False),
                'stalemate_probability': self.settings.get('stalemate_probability', 0.0),
                'always_promote_queen': self.settings.get('always_promote_queen', False),
                'checkmate_immediately': self.settings.get('checkmate_immediately', False),
            }
            return IntelligenceSettings.from_dict(intel_data)
        except Exception as e:
            print(f"Error loading intelligence settings: {e}")
            return IntelligenceSettings()

    def save_settings(self):
        """Save settings to file"""
        try:
            # Update intelligence settings in main settings
            if hasattr(self, 'intelligence_settings'):
                intel_dict = self.intelligence_settings.to_dict()
                for key, value in intel_dict.items():
                    self.settings[key] = value
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any):
        """Set a specific setting value"""
        self.settings[key] = value
        if self.get_setting("auto-save-settings", True):
            self.save_settings()

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary"""
        return self.settings.copy()

    def update_settings(self, new_settings: Dict[str, Any]):
        """Update multiple settings at once"""
        self.settings.update(new_settings)
        # Refresh intelligence settings
        self.intelligence_settings = self.load_intelligence_settings()
        self.save_settings()
    
    def update_intelligence_setting(self, key: str, value: Any):
        """Update a specific intelligence setting"""
        try:
            # Update in main settings
            self.settings[key] = value
            
            # Update in intelligence settings object if it has the attribute
            if hasattr(self.intelligence_settings, key):
                setattr(self.intelligence_settings, key, value)
            
            # Force save
            if self.get_setting("auto-save-settings", True):
                self.save_settings()
                
            print(f"Saved intelligence setting: {key} = {value}")
            
        except Exception as e:
            print(f"Error updating intelligence setting {key}: {e}")
    
    def get_intelligence_settings(self) -> IntelligenceSettings:
        """Get intelligence settings object"""
        return self.intelligence_settings

    def is_intelligence_fully_disabled(self) -> bool:
        """Check if intelligence is completely disabled"""
        return not self.intelligence_settings.intelligence_enabled

    def should_avoid_low_intelligence(self) -> bool:
        """Check if low intelligence avoidance is enabled"""
        return (self.intelligence_settings.intelligence_enabled and 
                self.intelligence_settings.avoid_low_intelligence)

    def get_low_intelligence_threshold(self) -> float:
        """Get the threshold for avoiding low intelligence moves"""
        threshold = self.intelligence_settings.low_intelligence_threshold
        # Clamp to valid range
        return max(-3.0, min(-1.0, threshold))

    # NEW: Rodent Personality Management Methods
    
    def get_available_personalities(self) -> List[str]:
        """Get list of available personality files"""
        try:
            if not self.personalities_dir.exists():
                return []
            
            personalities = []
            for file_path in self.personalities_dir.glob("*.txt"):
                # Security: Only allow .txt files and use basename to prevent path traversal
                filename = os.path.basename(str(file_path))
                if filename.endswith('.txt') and len(filename) < 100:  # Reasonable filename length limit
                    personalities.append(filename)
            
            personalities.sort()  # Alphabetical order
            return personalities
            
        except Exception as e:
            print(f"Error getting available personalities: {e}")
            return []
    
    def parse_personality_file(self, filename: str) -> Dict[str, str]:
        """Parse a personality file and return UCI options, filtering out book commands"""
        personality_data = {}
        
        try:
            # Security: Validate filename and prevent path traversal
            safe_filename = os.path.basename(filename)
            if not safe_filename.endswith('.txt'):
                return personality_data
            
            file_path = self.personalities_dir / safe_filename
            if not file_path.exists():
                return personality_data
            
            # Limit file size to prevent resource exhaustion
            if file_path.stat().st_size > 1024 * 1024:  # 1MB limit
                print(f"Personality file {filename} too large, skipping")
                return personality_data
            
            # Options to exclude (book and path-dependent settings)
            excluded_options = {
                'guidebookfile', 'mainbookfile', 'bookfile', 'openbookfile',
                'personalityfile', 'logfile', 'debugfile'
            }
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f):
                    if line_num > 1000:  # Limit number of lines
                        break
                        
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith(';') or line.startswith('#'):
                        continue
                    
                    # Parse UCI setoption commands
                    if line.lower().startswith('setoption name '):
                        try:
                            # Extract option name and value
                            parts = line.split(' value ', 1)
                            if len(parts) == 2:
                                option_part = parts[0].replace('setoption name ', '', 1).strip()
                                value_part = parts[1].strip()
                                
                                # Security: Check if option should be excluded
                                option_lower = option_part.lower()
                                if option_lower not in excluded_options:
                                    # Limit value length
                                    if len(value_part) < 100:
                                        personality_data[option_part] = value_part
                        except Exception as e:
                            print(f"Error parsing line in {filename}: {line} - {e}")
                            continue
            
            print(f"Loaded {len(personality_data)} options from {filename}")
            
        except Exception as e:
            print(f"Error parsing personality file {filename}: {e}")
        
        return personality_data
    
    def get_personality_display_name(self, filename: str) -> str:
        """Get display name for personality (filename without .txt)"""
        if filename.endswith('.txt'):
            return filename[:-4].title()
        return filename
    
    def is_rodent_personalities_enabled(self) -> bool:
        """Check if Rodent personalities are enabled"""
        return self.get_setting('rodent_personalities_enabled', False)
    
    def get_selected_rodent_personality(self) -> str:
        """Get the currently selected Rodent personality"""
        return self.get_setting('selected_rodent_personality', 'tal.txt')
    
    def set_rodent_personalities_enabled(self, enabled: bool):
        """Enable or disable Rodent personalities"""
        self.set_setting('rodent_personalities_enabled', enabled)
    
    def set_selected_rodent_personality(self, filename: str):
        """Set the selected Rodent personality"""
        # Security: Validate filename
        safe_filename = os.path.basename(filename)
        if safe_filename.endswith('.txt') and len(safe_filename) < 100:
            self.set_setting('selected_rodent_personality', safe_filename)
    
    def get_rodent_personality_options(self) -> Dict[str, str]:
        """Get UCI options for the currently selected Rodent personality"""
        if not self.is_rodent_personalities_enabled():
            return {}
        
        selected_personality = self.get_selected_rodent_personality()
        return self.parse_personality_file(selected_personality)

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.default_settings.copy()
        self.intelligence_settings = IntelligenceSettings()
        self.save_settings()

    def export_settings(self, filepath: str) -> bool:
        """Export settings to a file"""
        try:
            export_data = {
                "settings": self.settings,
                "version": "MINT Beta 2c 26092025 Features",
                "export_date": datetime.now().isoformat()
            }
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting settings: {e}")
            return False

    def import_settings(self, filepath: str) -> bool:
        """Import settings from a file"""
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
            
            if "settings" in import_data:
                self.settings.update(import_data["settings"])
            else:
                self.settings.update(import_data)
            
            self.intelligence_settings = self.load_intelligence_settings()
            self.save_settings()
            return True
        except Exception as e:
            print(f"Error importing settings: {e}")
            return False