"""
This is a new utility file for command validation and security
"""

import re
import json
from typing import Dict, List, Optional, Any
from constants import server_logger

class ExtensionCommandValidator:
    """Validates and sanitizes commands sent to the extension"""
    
    # Valid move pattern (UCI notation)
    MOVE_PATTERN = re.compile(r'^[a-h][1-8][a-h][1-8][qrnb]?$')
    
    # Valid square pattern
    SQUARE_PATTERN = re.compile(r'^[a-h][1-8]$')
    
    # Valid color pattern (hex colors)
    COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')
    
    @classmethod
    def validate_move_command(cls, move: str, delay_ms: int = 0) -> bool:
        """Validate move command parameters"""
        try:
            # Validate move format
            if not cls.MOVE_PATTERN.match(move):
                server_logger.warning(f"Invalid move format: {move}")
                return False
            
            # Validate delay range
            if not 0 <= delay_ms <= 300000:  # Max 5 minutes
                server_logger.warning(f"Invalid delay: {delay_ms}ms")
                return False
            
            return True
        except Exception as e:
            server_logger.error(f"Move command validation error: {e}")
            return False
    
    @classmethod
    def validate_visual_data(cls, visual_data: Dict[str, Any]) -> bool:
        """Validate visual update data"""
        try:
            # Check top-level structure
            if not isinstance(visual_data, dict):
                return False
            
            # Validate arrows
            if 'arrows' in visual_data:
                if not cls._validate_arrows(visual_data['arrows']):
                    return False
            
            # Validate highlights
            if 'highlights' in visual_data:
                if not cls._validate_highlights(visual_data['highlights']):
                    return False
            
            # Validate effects
            if 'effects' in visual_data:
                if not cls._validate_effects(visual_data['effects']):
                    return False
            
            return True
        except Exception as e:
            server_logger.error(f"Visual data validation error: {e}")
            return False
    
    @classmethod
    def _validate_arrows(cls, arrows: List[Dict]) -> bool:
        """Validate arrow data"""
        if not isinstance(arrows, list) or len(arrows) > 10:  # Limit arrows
            return False
        
        for arrow in arrows:
            if not isinstance(arrow, dict):
                return False
            
            # Required fields
            if not all(key in arrow for key in ['from', 'to', 'color', 'opacity']):
                return False
            
            # Validate squares
            if not (cls.SQUARE_PATTERN.match(arrow['from']) and 
                   cls.SQUARE_PATTERN.match(arrow['to'])):
                return False
            
            # Validate color
            if not cls.COLOR_PATTERN.match(arrow['color']):
                return False
            
            # Validate opacity
            if not isinstance(arrow['opacity'], (int, float)) or not 0 <= arrow['opacity'] <= 1:
                return False
        
        return True
    
    @classmethod
    def _validate_highlights(cls, highlights: List[Dict]) -> bool:
        """Validate highlight data"""
        if not isinstance(highlights, list) or len(highlights) > 8:  # Limit highlights
            return False
        
        for highlight in highlights:
            if not isinstance(highlight, dict):
                return False
            
            # Required fields
            if not all(key in highlight for key in ['square', 'color', 'opacity']):
                return False
            
            # Validate square
            if not cls.SQUARE_PATTERN.match(highlight['square']):
                return False
            
            # Validate color
            if not cls.COLOR_PATTERN.match(highlight['color']):
                return False
            
            # Validate opacity
            if not isinstance(highlight['opacity'], (int, float)) or not 0 <= highlight['opacity'] <= 1:
                return False
        
        return True
    
    @classmethod
    def _validate_effects(cls, effects: List[Dict]) -> bool:
        """Validate effect data"""
        if not isinstance(effects, list) or len(effects) > 5:  # Limit effects
            return False
        
        valid_effect_types = {
            'BestMove', 'Excellent', 'Good', 'Inaccuracy', 'Mistake', 'Blunder',
            'Brilliant', 'GreatFind', 'WinnerWhite', 'WinnerBlack', 'ResignWhite', 'MissedWin'
        }
        
        for effect in effects:
            if not isinstance(effect, dict):
                return False
            
            # Required fields
            if not all(key in effect for key in ['square', 'type']):
                return False
            
            # Validate square
            if not cls.SQUARE_PATTERN.match(effect['square']):
                return False
            
            # Validate effect type
            if effect['type'] not in valid_effect_types:
                return False
        
        return True
    
    @classmethod
    def validate_evaluation_update(cls, score: float, is_mate: bool) -> bool:
        """Validate evaluation update parameters"""
        try:
            # Validate score range
            if is_mate:
                if not -100 <= score <= 100:  # Mate in X moves
                    return False
            else:
                if not -50.0 <= score <= 50.0:  # Evaluation in pawns
                    return False
            
            return True
        except Exception as e:
            server_logger.error(f"Evaluation validation error: {e}")
            return False
    
    @classmethod
    def validate_depth_update(cls, progress: float) -> bool:
        """Validate depth update parameters"""
        try:
            return isinstance(progress, (int, float)) and 0 <= progress <= 100
        except Exception:
            return False

class ExtensionCommandGenerator:
    """Generates validated extension commands"""
    
    def __init__(self, validator: ExtensionCommandValidator = None):
        self.validator = validator or ExtensionCommandValidator()
    
    def create_move_command(self, move: str, delay_ms: int = 0) -> Optional[str]:
        """Create a validated move command"""
        if not self.validator.validate_move_command(move, delay_ms):
            return None
        
        if delay_ms > 0:
            return f"move_command {move} delay_ms {delay_ms}"
        else:
            return f"move_command {move}"
    
    def create_visual_update(self, visual_data: Dict[str, Any]) -> Optional[str]:
        """Create a validated visual update command"""
        if not self.validator.validate_visual_data(visual_data):
            return None
        
        try:
            return f"visual_update {json.dumps(visual_data, separators=(',', ':'))}"
        except (TypeError, ValueError) as e:
            server_logger.error(f"JSON serialization error: {e}")
            return None
    
    def create_evaluation_update(self, score: float, is_mate: bool = False) -> Optional[str]:
        """Create a validated evaluation update command"""
        if not self.validator.validate_evaluation_update(score, is_mate):
            return None
        
        return f"evaluation_update {score:.2f} {str(is_mate).lower()}"
    
    def create_depth_update(self, progress: float) -> Optional[str]:
        """Create a validated depth update command"""
        if not self.validator.validate_depth_update(progress):
            return None
        
        return f"depth_update {progress:.1f}"
