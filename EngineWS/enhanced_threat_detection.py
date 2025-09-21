"""
Enhanced Threat Detection System for BetterMint Modded
More accurate threat analysis with better filtering and detection
"""

import chess
from typing import Dict, List, Optional, Tuple
from constants import server_logger


class EnhancedThreatDetector:
    """Enhanced threat detection with improved accuracy and filtering"""
    
    @staticmethod
    def detect_all_threats(board: chess.Board, min_threat_value: float = 1.0, 
                          max_player_threats: int = 5, max_opponent_threats: int = 3) -> Dict[str, List[Dict[str, str]]]:
        """Detect all significant threats and return as arrow data
        
        Args:
            board: Current chess board position
            min_threat_value: Minimum piece value to consider as threat (pawns = 1.0)
            max_player_threats: Maximum number of player threat arrows to show
            max_opponent_threats: Maximum number of opponent threat arrows to show
        
        Returns:
        {
            'player_threats': [{'from': 'e2', 'to': 'e4', 'target': 'd5', 'threat_type': 'capture', 'value': 3.0, 'strength': 850}],
            'opponent_threats': [{'from': 'f7', 'to': 'f5', 'target': 'e4', 'threat_type': 'attack', 'value': 1.0, 'strength': 510}]
        }
        """
        player_threats = []
        opponent_threats = []
        
        try:
            current_turn = board.turn
            
            # Detect player threats (what current player can threaten with their moves)
            player_threats = EnhancedThreatDetector._detect_player_threats(board, current_turn, min_threat_value)
            
            # Detect opponent threats (what opponent threatens right now)
            opponent_threats = EnhancedThreatDetector._detect_opponent_threats(board, not current_turn, min_threat_value)
            
            # Filter and prioritize threats with custom limits
            player_threats = EnhancedThreatDetector._filter_and_prioritize_threats(player_threats, max_player_threats)
            opponent_threats = EnhancedThreatDetector._filter_and_prioritize_threats(opponent_threats, max_opponent_threats)
            
        except Exception as e:
            server_logger.error(f"Error detecting threats: {e}")
        
        return {
            'player_threats': player_threats,
            'opponent_threats': opponent_threats
        }
    
    @staticmethod
    def _detect_player_threats(board: chess.Board, color: bool, min_value: float) -> List[Dict[str, str]]:
        """Detect threats that the current player can make with their legal moves"""
        threats = []
        
        try:
            if board.turn != color:
                return threats
            
            # Analyze each legal move for threats
            for move in board.legal_moves:
                move_threats = EnhancedThreatDetector._analyze_move_threats(board, move, min_value)
                threats.extend(move_threats)
                
        except Exception as e:
            server_logger.warning(f"Error detecting player threats: {e}")
        
        return threats
    
    @staticmethod
    def _detect_opponent_threats(board: chess.Board, opponent_color: bool, min_value: float) -> List[Dict[str, str]]:
        """Detect current threats from opponent pieces"""
        threats = []
        
        try:
            # Look at all opponent pieces and what they currently threaten
            for square in chess.SQUARES:
                piece = board.piece_at(square)
                if piece and piece.color == opponent_color:
                    piece_threats = EnhancedThreatDetector._analyze_piece_current_threats(
                        board, square, opponent_color, min_value
                    )
                    threats.extend(piece_threats)
                    
        except Exception as e:
            server_logger.warning(f"Error detecting opponent threats: {e}")
        
        return threats
    
    @staticmethod
    def _analyze_move_threats(board: chess.Board, move: chess.Move, min_value: float) -> List[Dict[str, str]]:
        """Analyze all threats created by a specific move"""
        threats = []
        
        try:
            from_square = chess.square_name(move.from_square)
            to_square = chess.square_name(move.to_square)
            moving_piece = board.piece_at(move.from_square)
            
            if not moving_piece:
                return threats
            
            # 1. Direct capture threat
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    piece_value = EnhancedThreatDetector._get_piece_value(captured_piece.piece_type)
                    if piece_value >= min_value:
                        threats.append({
                            'from': from_square,
                            'to': to_square,
                            'target': to_square,
                            'threat_type': 'capture',
                            'value': piece_value
                        })
            
            # 2. Check threat
            board_copy = board.copy()
            board_copy.push(move)
            if board_copy.is_check():
                enemy_king_square = board_copy.king(not board.turn)
                if enemy_king_square:
                    threats.append({
                        'from': from_square,
                        'to': to_square,
                        'target': chess.square_name(enemy_king_square),
                        'threat_type': 'check',
                        'value': 10.0  # High priority for checks
                    })
            
            # 3. Discovered attacks (move reveals attack from another piece)
            discovered_threats = EnhancedThreatDetector._check_discovered_attacks(board, move, min_value)
            threats.extend(discovered_threats)
            
            # 4. New attacks from the moved piece
            new_attacks = EnhancedThreatDetector._check_new_attacks_from_move(board_copy, move.to_square, board.turn, min_value)
            for attack in new_attacks:
                attack['from'] = from_square
                attack['to'] = to_square
                threats.append(attack)
                
        except Exception as e:
            server_logger.warning(f"Error analyzing move threats for {move}: {e}")
        
        return threats
    
    @staticmethod
    def _analyze_piece_current_threats(board: chess.Board, piece_square: int, color: bool, min_value: float) -> List[Dict[str, str]]:
        """Analyze current threats from a specific piece"""
        threats = []
        
        try:
            piece = board.piece_at(piece_square)
            if not piece or piece.color != color:
                return threats
            
            from_square_name = chess.square_name(piece_square)
            attacks = board.attacks(piece_square)
            
            for target_square in attacks:
                target_piece = board.piece_at(target_square)
                
                # Only show threats to enemy pieces
                if target_piece and target_piece.color != color:
                    piece_value = EnhancedThreatDetector._get_piece_value(target_piece.piece_type)
                    
                    if piece_value >= min_value:
                        threat_type = 'check_threat' if target_piece.piece_type == chess.KING else 'attack'
                        
                        threats.append({
                            'from': from_square_name,
                            'to': chess.square_name(target_square),
                            'target': chess.square_name(target_square),
                            'threat_type': threat_type,
                            'value': piece_value
                        })
                        
        except Exception as e:
            server_logger.warning(f"Error analyzing piece threats at {piece_square}: {e}")
        
        return threats
    
    @staticmethod
    def _check_discovered_attacks(board: chess.Board, move: chess.Move, min_value: float) -> List[Dict[str, str]]:
        """Check for discovered attacks when a piece moves"""
        discovered_threats = []
        
        try:
            # Make the move to see what's revealed
            board_copy = board.copy()
            board_copy.push(move)
            
            from_square_name = chess.square_name(move.from_square)
            to_square_name = chess.square_name(move.to_square)
            
            # Look for pieces of our color that now attack enemy pieces
            for square in chess.SQUARES:
                piece = board_copy.piece_at(square)
                if piece and piece.color == board.turn and square != move.to_square:
                    
                    # Check if this piece now attacks something it couldn't before
                    current_attacks = board_copy.attacks(square)
                    
                    # Check what this piece attacked before the move
                    board_before = board.copy()
                    previous_attacks = board_before.attacks(square)
                    
                    # Find new attacks
                    new_attacks = current_attacks - previous_attacks
                    
                    for target_square in new_attacks:
                        target_piece = board_copy.piece_at(target_square)
                        if target_piece and target_piece.color != board.turn:
                            piece_value = EnhancedThreatDetector._get_piece_value(target_piece.piece_type)
                            
                            if piece_value >= min_value:
                                discovered_threats.append({
                                    'from': from_square_name,
                                    'to': to_square_name,
                                    'target': chess.square_name(target_square),
                                    'threat_type': 'discovered_attack',
                                    'value': piece_value
                                })
                                
        except Exception as e:
            server_logger.warning(f"Error checking discovered attacks: {e}")
        
        return discovered_threats
    
    @staticmethod
    def _check_new_attacks_from_move(board: chess.Board, piece_square: int, color: bool, min_value: float) -> List[Dict[str, str]]:
        """Check what the moved piece now attacks from its new position"""
        new_attacks = []
        
        try:
            attacks = board.attacks(piece_square)
            
            for target_square in attacks:
                target_piece = board.piece_at(target_square)
                if target_piece and target_piece.color != color:
                    piece_value = EnhancedThreatDetector._get_piece_value(target_piece.piece_type)
                    
                    if piece_value >= min_value:
                        threat_type = 'check' if target_piece.piece_type == chess.KING else 'new_attack'
                        
                        new_attacks.append({
                            'target': chess.square_name(target_square),
                            'threat_type': threat_type,
                            'value': piece_value
                        })
                        
        except Exception as e:
            server_logger.warning(f"Error checking new attacks from {piece_square}: {e}")
        
        return new_attacks
    
    @staticmethod
    def _filter_and_prioritize_threats(threats: List[Dict[str, str]], max_threats: int = 8) -> List[Dict[str, str]]:
        """Filter and prioritize threats by strength with custom limits"""
        if not threats:
            return threats
        
        # Remove duplicates (same from-to combination)
        unique_threats = []
        seen_moves = set()
        
        for threat in threats:
            move_key = f"{threat['from']}-{threat['to']}"
            if move_key not in seen_moves:
                seen_moves.add(move_key)
                unique_threats.append(threat)
        
        # Calculate strength score for each threat and add it to the threat data
        for threat in unique_threats:
            threat['strength'] = EnhancedThreatDetector._calculate_threat_strength(threat)
        
        # Sort by strength (highest first)
        unique_threats.sort(key=lambda x: x['strength'], reverse=True)
        
        # Limit number of threats to user-specified maximum
        return unique_threats[:max_threats]
    
    @staticmethod
    def _calculate_threat_strength(threat: Dict[str, str]) -> float:
        """Calculate numerical strength score for threat sorting
        
        Returns a score where higher = stronger threat
        Components:
        - Threat type base score (check=1000, capture=800, etc.)
        - Piece value bonus (queen=90, rook=50, etc.)
        - Tactical bonuses (discovered attack, fork, etc.)
        """
        
        # Base scores by threat type (higher = more important)
        type_scores = {
            'check': 1000,           # Checking the king is highest priority
            'checkmate': 2000,       # Mate threats (if we add this later)
            'check_threat': 900,     # Threatening to check
            'capture': 800,          # Direct captures
            'discovered_attack': 700, # Discovered attacks (often tactical)
            'fork': 750,             # Forks (attacking multiple pieces)
            'pin': 650,              # Pins (restricting movement)
            'skewer': 680,           # Skewers (if we add this later)
            'new_attack': 600,       # New attacks from moved piece
            'attack': 500,           # General attacks on pieces
            'defense': 300           # Defensive moves (if we add this later)
        }
        
        threat_type = threat.get('threat_type', 'attack')
        base_score = type_scores.get(threat_type, 400)
        
        # Piece value bonus (multiply by 10 for significant impact)
        piece_value = threat.get('value', 0)
        value_bonus = piece_value * 10
        
        # Additional tactical bonuses
        tactical_bonus = 0
        
        # Bonus for threats against valuable pieces
        if piece_value >= 9:  # Queen
            tactical_bonus += 50
        elif piece_value >= 5:  # Rook
            tactical_bonus += 25
        elif piece_value >= 3:  # Minor pieces
            tactical_bonus += 10
        
        # Bonus for special threat types
        if threat_type == 'discovered_attack':
            tactical_bonus += 30  # Discovered attacks are often powerful
        elif threat_type == 'fork':
            tactical_bonus += 25  # Forks are tactically strong
        elif threat_type == 'pin':
            tactical_bonus += 20  # Pins restrict opponent
        
        # Calculate final strength
        strength = base_score + value_bonus + tactical_bonus
        
        # Add small random component to break ties consistently
        import random
        tie_breaker = random.uniform(0, 1)
        
        return strength + tie_breaker
    
    @staticmethod
    def _get_piece_value(piece_type: int) -> float:
        """Get the standard value of a piece type"""
        values = {
            chess.PAWN: 1.0,
            chess.KNIGHT: 3.0,
            chess.BISHOP: 3.0,
            chess.ROOK: 5.0,
            chess.QUEEN: 9.0,
            chess.KING: 100.0  # Highest priority
        }
        
        return values.get(piece_type, 0.0)
    
    @staticmethod
    def should_show_threat_for_move(move_evaluation: Optional[float], threshold: float = -1.5) -> bool:
        """Determine if threat arrows should be shown for a move based on its evaluation
        
        Args:
            move_evaluation: Evaluation of the move in pawns (None if unknown)
            threshold: Minimum evaluation to show threats (default -1.5 pawns)
            
        Returns:
            True if threats should be shown for this move
        """
        if move_evaluation is None:
            return True  # Show threats if we don't know the evaluation
        
        # Don't show threats for very bad moves
        return move_evaluation > threshold