"""
Enhanced game state management utilities
"""

import chess
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import GameState, MoveCandidate

class GameStateAnalyzer:
    """Advanced game state analysis utilities"""
    
    @staticmethod
    def analyze_position_characteristics(board: chess.Board) -> Dict[str, Any]:
        """Analyze characteristics of a chess position"""
        if not board:
            return {}
        
        characteristics = {
            'material_balance': 0,
            'piece_activity': 0.0,
            'king_safety_white': 0.0,
            'king_safety_black': 0.0,
            'center_control': 0.0,
            'pawn_structure_score': 0.0,
            'tactical_complexity': 0.0
        }
        
        try:
            # Material balance calculation
            piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, 
                          chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
            
            white_material = sum(piece_values.get(piece.piece_type, 0) 
                               for piece in board.piece_map().values() 
                               if piece.color == chess.WHITE)
            black_material = sum(piece_values.get(piece.piece_type, 0) 
                               for piece in board.piece_map().values() 
                               if piece.color == chess.BLACK)
            
            characteristics['material_balance'] = white_material - black_material
            
            # Center control (simplified)
            center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
            white_center = sum(1 for sq in center_squares 
                             if board.piece_at(sq) and board.piece_at(sq).color == chess.WHITE)
            black_center = sum(1 for sq in center_squares 
                             if board.piece_at(sq) and board.piece_at(sq).color == chess.BLACK)
            
            characteristics['center_control'] = (white_center - black_center) / 4.0
            
            # Tactical complexity (number of legal moves as proxy)
            legal_moves = len(list(board.legal_moves))
            characteristics['tactical_complexity'] = min(legal_moves / 40.0, 1.0)
            
        except Exception as e:
            server_logger.warning(f"Position analysis error: {e}")
        
        return characteristics
    
    @staticmethod
    def detect_tactical_motifs(board: chess.Board) -> List[str]:
        """Detect common tactical motifs in position"""
        if not board:
            return []
        
        motifs = []
        
        try:
            # Check for checks
            if board.is_check():
                motifs.append("check")
            
            # Check for captures available
            legal_moves = list(board.legal_moves)
            captures = [move for move in legal_moves if board.is_capture(move)]
            if captures:
                motifs.append("captures_available")
            
            # Check for castling availability
            if board.has_kingside_castling_rights(board.turn):
                motifs.append("kingside_castling")
            if board.has_queenside_castling_rights(board.turn):
                motifs.append("queenside_castling")
            
            # Check for en passant
            if board.ep_square:
                motifs.append("en_passant")
            
        except Exception as e:
            server_logger.warning(f"Tactical motif detection error: {e}")
        
        return motifs
    
    @staticmethod
    def estimate_game_phase(board: chess.Board) -> str:
        """Estimate current game phase"""
        if not board:
            return "unknown"
        
        try:
            # Count pieces
            piece_count = len(board.piece_map())
            
            # Count major pieces (queens and rooks)
            major_pieces = sum(1 for piece in board.piece_map().values() 
                             if piece.piece_type in [chess.QUEEN, chess.ROOK])
            
            # Phase determination
            if board.fullmove_number <= 10 and piece_count >= 28:
                return "opening"
            elif piece_count <= 12 or major_pieces <= 4:
                return "endgame"
            else:
                return "middlegame"
        
        except Exception:
            return "unknown"
