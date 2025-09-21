"""
Enhanced data models for BetterMint Modded with complete intelligence settings and new controls
"""

import chess
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class Settings(BaseModel):
    """Settings model for API"""
    settings: Dict[str, Any]

class PerformanceData(BaseModel):
    """Performance monitoring data"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    engine_depth: int
    evaluation_time: float

class ConnectionInfo:
    """WebSocket connection information"""
    def __init__(self, client_id: str, websocket):
        self.client_id = client_id
        self.websocket = websocket
        self.connected_time = datetime.now()
        self.last_activity = datetime.now()
        self.status = "Connected"
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for serialization"""
        return {
            'client_id': self.client_id,
            'connected_time': self.connected_time.strftime("%H:%M:%S"),
            'last_activity': self.last_activity.strftime("%H:%M:%S"),
            'status': self.status
        }

class MoveEvaluation:
    """Chess move evaluation data"""
    def __init__(self, move: str, score: float, depth: int = 0):
        self.move = move
        self.score = score
        self.depth = depth
        self.is_aggressive = False
        self.is_defensive = False
        self.is_trade = False
        self.trade_value = 0.0

class MoveCandidate:
    """Detailed move candidate with analysis data"""
    def __init__(self, move: str, from_square: str, to_square: str, 
                 score_cp: Optional[int] = None, score_pawns: float = 0.0, 
                 depth: int = 0, mate_in: Optional[int] = None, 
                 pv_line: List[str] = None, nodes: int = 0):
        self.move = move
        self.from_square = from_square
        self.to_square = to_square
        self.score_cp = score_cp
        self.score_pawns = score_pawns
        self.depth = depth
        self.mate_in = mate_in
        self.pv_line = pv_line or []
        self.nodes = nodes
        
        # Analysis characteristics
        self.is_aggressive = False
        self.is_passive = False
        self.is_tactical = False
        self.is_positional = False
        self.is_capture = False
        self.is_check = False
        self.is_book_move = False
        self.is_castling = False
        self.is_en_passant = False
        self.is_promotion = False
        self.creates_pin = False
        self.is_trade = False
        self.trade_value = 0.0
        self.moving_piece_type = None
        self.enables_stalemate = False
        
        # Intelligence tracking
        self.original_score_pawns = score_pawns  # Store original engine evaluation
        self.intelligence_modified = False       # Track if intelligence modified this move
        self.intelligence_multiplier = 1.0      # Track the total multiplier applied
        
        # Move quality assessment
        self.quality_score = 0.0  # 0-100 scale
        self.quality_label = "Unknown"  # "Excellent", "Good", "Inaccuracy", etc.
        
    def analyze_move_characteristics(self, board: Optional[chess.Board] = None):
        """Analyze move characteristics if board position is available"""
        if not board:
            return
            
        try:
            chess_move = chess.Move.from_uci(self.move)
            
            # Check if move is capture
            self.is_capture = board.is_capture(chess_move)
            
            # Check if move is castling
            self.is_castling = board.is_castling(chess_move)
            
            # Check if move is en passant
            self.is_en_passant = board.is_en_passant(chess_move)
            
            # Check if move is promotion
            if chess_move.promotion:
                self.is_promotion = True
            
            # Check if move gives check
            board_copy = board.copy()
            board_copy.push(chess_move)
            self.is_check = board_copy.is_check()
            
            # Check if move enables stalemate
            if board_copy.is_stalemate():
                self.enables_stalemate = True
            
            # Determine moving piece type
            piece = board.piece_at(chess_move.from_square)
            if piece:
                self.moving_piece_type = piece.piece_type
                
                # Analyze aggressiveness (attacks, advances)
                if self.is_capture or self.is_check:
                    self.is_tactical = True
                    self.is_aggressive = True
                
                # Central control indicates positional play
                to_file = chess.square_file(chess_move.to_square)
                to_rank = chess.square_rank(chess_move.to_square)
                if 2 <= to_file <= 5 and 2 <= to_rank <= 5:  # Central squares
                    self.is_positional = True
        
        except:
            pass  # Invalid move or analysis failed
    
    def apply_intelligence_modification(self, new_score_pawns: float, multiplier: float):
        """Apply intelligence modification to this candidate"""
        self.original_score_pawns = self.score_pawns  # Store original if not already stored
        self.score_pawns = new_score_pawns
        self.score_cp = int(new_score_pawns * 100) if new_score_pawns is not None else self.score_cp
        self.intelligence_modified = True
        self.intelligence_multiplier = multiplier
    
    def get_intelligence_modification_info(self) -> Dict[str, Any]:
        """Get information about intelligence modifications applied"""
        return {
            'modified': self.intelligence_modified,
            'original_score': self.original_score_pawns,
            'modified_score': self.score_pawns,
            'multiplier': self.intelligence_multiplier,
            'score_change': self.score_pawns - self.original_score_pawns if self.intelligence_modified else 0.0
        }
    
    def assign_quality_rating(self):
        """Assign quality rating based on evaluation and characteristics"""
        if self.mate_in is not None:
            if self.mate_in > 0:
                self.quality_score = 100
                self.quality_label = "Mate"
            else:
                self.quality_score = 0
                self.quality_label = "Mate Against"
        elif self.score_cp is not None:
            # Convert centipawn score to quality (very rough approximation)
            if self.score_cp > 200:
                self.quality_score = 95
                self.quality_label = "Excellent"
            elif self.score_cp > 50:
                self.quality_score = 85
                self.quality_label = "Good"
            elif self.score_cp > -25:
                self.quality_score = 75
                self.quality_label = "Decent"
            elif self.score_cp > -100:
                self.quality_score = 50
                self.quality_label = "Inaccuracy"
            elif self.score_cp > -300:
                self.quality_score = 25
                self.quality_label = "Mistake"
            else:
                self.quality_score = 10
                self.quality_label = "Blunder"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'move': self.move,
            'from_square': self.from_square,
            'to_square': self.to_square,
            'score_cp': self.score_cp,
            'score_pawns': self.score_pawns,
            'original_score_pawns': self.original_score_pawns,
            'depth': self.depth,
            'mate_in': self.mate_in,
            'pv_line': self.pv_line,
            'nodes': self.nodes,
            'is_aggressive': self.is_aggressive,
            'is_passive': self.is_passive,
            'is_tactical': self.is_tactical,
            'is_positional': self.is_positional,
            'is_capture': self.is_capture,
            'is_check': self.is_check,
            'is_book_move': self.is_book_move,
            'is_castling': self.is_castling,
            'is_en_passant': self.is_en_passant,
            'is_promotion': self.is_promotion,
            'creates_pin': self.creates_pin,
            'moving_piece_type': self.moving_piece_type,
            'enables_stalemate': self.enables_stalemate,
            'intelligence_modified': self.intelligence_modified,
            'intelligence_multiplier': self.intelligence_multiplier,
            'quality_score': self.quality_score,
            'quality_label': self.quality_label
        }

class GameState:
    """Complete server-side game state tracking"""
    def __init__(self):
        # Board state
        self.current_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.current_board: Optional[chess.Board] = None
        self.position_history: List[str] = []
        
        # Game information
        self.move_number = 1
        self.turn = 'w'  # 'w' or 'b'
        self.game_phase = "opening"  # "opening", "middlegame", "endgame"
        self.piece_count = 32
        
        # Game status
        self.is_check = False
        self.is_checkmate = False
        self.is_stalemate = False
        self.is_draw = False
        self.game_result = "*"  # "*", "1-0", "0-1", "1/2-1/2"
        
        # Analysis state
        self.current_evaluation = 0.0  # In pawns
        self.evaluation_history: List[float] = []
        self.last_move: Optional[str] = None
        self.last_move_quality = "Unknown"
        
        # Intelligence tracking
        self.intelligence_active = False
        self.last_intelligence_decision = None  # "used", "avoided", "disabled"
        self.intelligence_avoided_count = 0
        self.total_move_count = 0
        
        # Timing state
        self.move_times: List[float] = []  # Move times in seconds
        self.total_game_time = 0.0
        self.last_move_time = 0.0
        
        # Opening state
        self.opening_name = "Unknown"
        self.moves_from_book = 0
        self.still_in_book = True
        
        # Tactical state
        self.tactics_available = []  # List of tactical motifs
        self.threats_present = []    # Current threats on board
        
        # Performance metrics
        self.positions_analyzed = 0
        self.total_nodes_searched = 0
        self.average_depth = 0.0
        
        # Server state
        self.last_update_time = datetime.now()
        self.analysis_active = False
        self.waiting_for_move = False
    
    def update_from_fen(self, fen: str):
        """Update game state from FEN string"""
        try:
            self.current_fen = fen
            self.current_board = chess.Board(fen)
            
            # Update basic state
            self.move_number = self.current_board.fullmove_number
            self.turn = 'w' if self.current_board.turn else 'b'
            self.piece_count = len(self.current_board.piece_map())
            
            # Update game status
            self.is_check = self.current_board.is_check()
            self.is_checkmate = self.current_board.is_checkmate()
            self.is_stalemate = self.current_board.is_stalemate()
            self.is_draw = self.current_board.is_insufficient_material() or \
                          self.current_board.is_seventyfive_moves() or \
                          self.current_board.is_fivefold_repetition()
            
            # Determine game result
            if self.is_checkmate:
                self.game_result = "0-1" if self.current_board.turn else "1-0"
            elif self.is_stalemate or self.is_draw:
                self.game_result = "1/2-1/2"
            else:
                self.game_result = "*"
            
            # Update game phase
            self._update_game_phase()
            
            # Add to position history
            if fen not in self.position_history[-5:]:  # Avoid immediate duplicates
                self.position_history.append(fen)
            
            # Limit history size
            if len(self.position_history) > 100:
                self.position_history = self.position_history[-50:]
                
            self.last_update_time = datetime.now()
            
        except Exception as e:
            print(f"Error updating game state from FEN: {e}")
    
    def track_intelligence_decision(self, decision: str):
        """Track intelligence decision for statistics"""
        self.last_intelligence_decision = decision
        self.total_move_count += 1
        
        if decision == "avoided":
            self.intelligence_avoided_count += 1
    
    def get_intelligence_usage_rate(self) -> float:
        """Get percentage of moves where intelligence was used"""
        if self.total_move_count == 0:
            return 0.0
        
        intelligence_used = self.total_move_count - self.intelligence_avoided_count
        return (intelligence_used / self.total_move_count) * 100.0
    
    def _update_game_phase(self):
        """Determine current game phase based on material and move number"""
        if not self.current_board:
            return
            
        # Count major and minor pieces
        major_pieces = 0
        minor_pieces = 0
        
        for square in chess.SQUARES:
            piece = self.current_board.piece_at(square)
            if piece and piece.piece_type != chess.PAWN and piece.piece_type != chess.KING:
                if piece.piece_type in [chess.QUEEN, chess.ROOK]:
                    major_pieces += 1
                else:
                    minor_pieces += 1
        
        # Determine phase
        if self.move_number <= 12:
            self.game_phase = "opening"
        elif major_pieces <= 2 and minor_pieces <= 2:
            self.game_phase = "endgame"
        else:
            self.game_phase = "middlegame"
    
    def add_evaluation_point(self, evaluation: float):
        """Add evaluation point to history"""
        self.current_evaluation = evaluation
        self.evaluation_history.append(evaluation)
        
        # Limit history size
        if len(self.evaluation_history) > 200:
            self.evaluation_history = self.evaluation_history[-100:]
    
    def add_move_time(self, move_time: float):
        """Add move time to history"""
        self.last_move_time = move_time
        self.move_times.append(move_time)
        self.total_game_time += move_time
        
        # Limit history size
        if len(self.move_times) > 100:
            self.move_times = self.move_times[-50:]
    
    def get_evaluation_trend(self, moves: int = 5) -> str:
        """Get recent evaluation trend"""
        if len(self.evaluation_history) < moves:
            return "insufficient_data"
            
        recent_evals = self.evaluation_history[-moves:]
        
        # Calculate trend
        start_eval = recent_evals[0]
        end_eval = recent_evals[-1]
        
        if end_eval > start_eval + 0.3:
            return "improving"
        elif end_eval < start_eval - 0.3:
            return "declining"
        else:
            return "stable"
    
    def get_position_complexity(self) -> float:
        """Estimate position complexity (0.0 to 1.0)"""
        if not self.current_board:
            return 0.5
            
        complexity = 0.0
        
        # More pieces = more complex
        piece_factor = self.piece_count / 32.0
        complexity += piece_factor * 0.3
        
        # More legal moves = more complex
        legal_moves = len(list(self.current_board.legal_moves))
        move_factor = min(legal_moves / 40.0, 1.0)  # Cap at 40 moves
        complexity += move_factor * 0.3
        
        # Tactical elements add complexity
        if self.is_check:
            complexity += 0.2
        
        # Opening positions are generally less complex
        if self.game_phase == "opening":
            complexity *= 0.7
        elif self.game_phase == "endgame":
            complexity *= 0.8
        
        return min(complexity, 1.0)
    
    def is_critical_position(self) -> bool:
        """Determine if current position is critical (requires more thinking)"""
        # Check for tactical indicators
        if self.is_check or self.is_checkmate:
            return True
        
        # Check evaluation swings
        if len(self.evaluation_history) >= 2:
            eval_diff = abs(self.evaluation_history[-1] - self.evaluation_history[-2])
            if eval_diff > 0.5:  # Significant evaluation change
                return True
        
        # Check for complex positions
        if self.get_position_complexity() > 0.8:
            return True
        
        # Check for time pressure indicators
        if len(self.move_times) >= 3:
            recent_times = self.move_times[-3:]
            if all(t < 2.0 for t in recent_times):  # Recent fast moves might indicate time pressure
                return True
        
        return False
    
    def reset_for_new_game(self):
        """Reset state for a new game"""
        self.__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'current_fen': self.current_fen,
            'move_number': self.move_number,
            'turn': self.turn,
            'game_phase': self.game_phase,
            'piece_count': self.piece_count,
            'is_check': self.is_check,
            'is_checkmate': self.is_checkmate,
            'is_stalemate': self.is_stalemate,
            'is_draw': self.is_draw,
            'game_result': self.game_result,
            'current_evaluation': self.current_evaluation,
            'last_move': self.last_move,
            'last_move_quality': self.last_move_quality,
            'opening_name': self.opening_name,
            'moves_from_book': self.moves_from_book,
            'still_in_book': self.still_in_book,
            'total_game_time': self.total_game_time,
            'last_move_time': self.last_move_time,
            'positions_analyzed': self.positions_analyzed,
            'total_nodes_searched': self.total_nodes_searched,
            'average_depth': self.average_depth,
            'analysis_active': self.analysis_active,
            'waiting_for_move': self.waiting_for_move,
            'position_complexity': self.get_position_complexity(),
            'evaluation_trend': self.get_evaluation_trend(),
            'is_critical_position': self.is_critical_position(),
            'intelligence_active': self.intelligence_active,
            'last_intelligence_decision': self.last_intelligence_decision,
            'intelligence_usage_rate': self.get_intelligence_usage_rate()
        }

class IntelligenceSettings:
    """Complete intelligence feature settings with new controls"""
    def __init__(self, 
                 intelligence_enabled: bool = False,
                 # NEW: Intelligence Control Settings
                 avoid_low_intelligence: bool = False,
                 low_intelligence_threshold: float = -1.5,
                 # Move Multipliers
                 aggressiveness_contempt: float = 1.0,
                 passiveness_contempt: float = 1.0,
                 trading_preference: float = 0.0,
                 capture_preference: float = 1.0,
                 castle_preference: float = 1.0,
                 en_passant_preference: float = 1.0,
                 promotion_preference: float = 1.0,
                 # Boolean Preferences
                 prefer_early_castling: bool = False,
                 prefer_pins: bool = False,
                 prefer_side_castle: bool = False,
                 castle_side: Optional[str] = None,  # "kingside" or "queenside"
                 # Piece Movement Preferences
                 pawn_preference: float = 1.0,
                 knight_preference: float = 1.0,
                 bishop_preference: float = 1.0,
                 rook_preference: float = 1.0,
                 queen_preference: float = 1.0,
                 king_preference: float = 1.0,
                 # Emotional Behavior
                 stay_equal: bool = False,
                 stalemate_probability: float = 0.0,
                 always_promote_queen: bool = False,
                 checkmate_immediately: bool = False):
        
        self.intelligence_enabled = intelligence_enabled
        
        # NEW: Intelligence Control Settings
        self.avoid_low_intelligence = avoid_low_intelligence
        self.low_intelligence_threshold = max(-3.0, min(-1.0, low_intelligence_threshold))  # Clamp to range
        
        # Move Multipliers
        self.aggressiveness_contempt = aggressiveness_contempt
        self.passiveness_contempt = passiveness_contempt
        self.trading_preference = trading_preference
        self.capture_preference = capture_preference
        self.castle_preference = castle_preference
        self.en_passant_preference = en_passant_preference
        self.promotion_preference = promotion_preference
        # Boolean Preferences
        self.prefer_early_castling = prefer_early_castling
        self.prefer_pins = prefer_pins
        self.prefer_side_castle = prefer_side_castle
        self.castle_side = castle_side
        # Piece Movement Preferences
        self.pawn_preference = pawn_preference
        self.knight_preference = knight_preference
        self.bishop_preference = bishop_preference
        self.rook_preference = rook_preference
        self.queen_preference = queen_preference
        self.king_preference = king_preference
        # Emotional Behavior
        self.stay_equal = stay_equal
        self.stalemate_probability = stalemate_probability
        self.always_promote_queen = always_promote_queen
        self.checkmate_immediately = checkmate_immediately
    
    def is_fully_disabled(self) -> bool:
        """Check if intelligence is completely disabled"""
        return not self.intelligence_enabled
    
    def should_avoid_low_intelligence(self) -> bool:
        """Check if low intelligence avoidance is enabled"""
        return self.intelligence_enabled and self.avoid_low_intelligence
    
    def get_threshold(self) -> float:
        """Get the clamped threshold value"""
        return max(-3.0, min(-1.0, self.low_intelligence_threshold))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'intelligence_enabled': self.intelligence_enabled,
            'avoid_low_intelligence': self.avoid_low_intelligence,
            'low_intelligence_threshold': self.low_intelligence_threshold,
            'aggressiveness_contempt': self.aggressiveness_contempt,
            'passiveness_contempt': self.passiveness_contempt,
            'trading_preference': self.trading_preference,
            'capture_preference': self.capture_preference,
            'castle_preference': self.castle_preference,
            'en_passant_preference': self.en_passant_preference,
            'promotion_preference': self.promotion_preference,
            'prefer_early_castling': self.prefer_early_castling,
            'prefer_pins': self.prefer_pins,
            'prefer_side_castle': self.prefer_side_castle,
            'castle_side': self.castle_side,
            'pawn_preference': self.pawn_preference,
            'knight_preference': self.knight_preference,
            'bishop_preference': self.bishop_preference,
            'rook_preference': self.rook_preference,
            'queen_preference': self.queen_preference,
            'king_preference': self.king_preference,
            'stay_equal': self.stay_equal,
            'stalemate_probability': self.stalemate_probability,
            'always_promote_queen': self.always_promote_queen,
            'checkmate_immediately': self.checkmate_immediately
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntelligenceSettings':
        """Create from dictionary"""
        return cls(
            intelligence_enabled=data.get('intelligence_enabled', False),
            avoid_low_intelligence=data.get('avoid_low_intelligence', False),
            low_intelligence_threshold=data.get('low_intelligence_threshold', -1.5),
            aggressiveness_contempt=data.get('aggressiveness_contempt', 1.0),
            passiveness_contempt=data.get('passiveness_contempt', 1.0),
            trading_preference=data.get('trading_preference', 0.0),
            capture_preference=data.get('capture_preference', 1.0),
            castle_preference=data.get('castle_preference', 1.0),
            en_passant_preference=data.get('en_passant_preference', 1.0),
            promotion_preference=data.get('promotion_preference', 1.0),
            prefer_early_castling=data.get('prefer_early_castling', False),
            prefer_pins=data.get('prefer_pins', False),
            prefer_side_castle=data.get('prefer_side_castle', False),
            castle_side=data.get('castle_side', None),
            pawn_preference=data.get('pawn_preference', 1.0),
            knight_preference=data.get('knight_preference', 1.0),
            bishop_preference=data.get('bishop_preference', 1.0),
            rook_preference=data.get('rook_preference', 1.0),
            queen_preference=data.get('queen_preference', 1.0),
            king_preference=data.get('king_preference', 1.0),
            stay_equal=data.get('stay_equal', False),
            stalemate_probability=data.get('stalemate_probability', 0.0),
            always_promote_queen=data.get('always_promote_queen', False),
            checkmate_immediately=data.get('checkmate_immediately', False)
        )

class ExtensionCommand:
    """Represents a command to be sent to the extension"""
    def __init__(self, command_type: str, data: Dict[str, Any] = None, delay_ms: int = 0):
        self.command_type = command_type
        self.data = data or {}
        self.delay_ms = delay_ms
        self.timestamp = datetime.now()
    
    def to_string(self) -> str:
        """Convert to extension command string"""
        if self.command_type == "move_command":
            move = self.data.get('move', '')
            if self.delay_ms > 0:
                return f"move_command {move} delay_ms {self.delay_ms}"
            else:
                return f"move_command {move}"
        
        elif self.command_type == "visual_update":
            import json
            return f"visual_update {json.dumps(self.data)}"
        
        elif self.command_type == "evaluation_update":
            score = self.data.get('score', 0)
            is_mate = self.data.get('is_mate', False)
            return f"evaluation_update {score} {str(is_mate).lower()}"
        
        elif self.command_type == "depth_update":
            progress = self.data.get('progress', 0)
            return f"depth_update {progress}"
        
        else:
            return ""

class AnalysisSession:
    """Tracks a single analysis session with depth progression"""
    def __init__(self, target_depth: int = 15):
        self.target_depth = target_depth
        self.current_depth = 0
        self.start_time = datetime.now()
        self.candidates: List[MoveCandidate] = []
        self.nodes_searched = 0
        self.is_complete = False
        self.mate_found = False
        self.best_move: Optional[str] = None
        
        # Intelligence tracking
        self.intelligence_applied = False
        self.intelligence_avoided = False
        self.original_best_move: Optional[str] = None
        self.intelligence_decision_reason = ""
    
    def update_progress(self, depth: int, candidates: List[MoveCandidate] = None):
        """Update analysis progress"""
        self.current_depth = max(self.current_depth, depth)
        if candidates:
            self.candidates = candidates
        
        # Check for completion
        if self.current_depth >= self.target_depth:
            self.is_complete = True
    
    def set_intelligence_decision(self, applied: bool, avoided: bool, reason: str = "", original_move: str = ""):
        """Track intelligence decision for this analysis"""
        self.intelligence_applied = applied
        self.intelligence_avoided = avoided
        self.intelligence_decision_reason = reason
        self.original_best_move = original_move
    
    def get_progress_percentage(self) -> float:
        """Get progress as percentage"""
        return min((self.current_depth / self.target_depth) * 100, 100.0)
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'target_depth': self.target_depth,
            'current_depth': self.current_depth,
            'progress_percentage': self.get_progress_percentage(),
            'elapsed_time': self.get_elapsed_time(),
            'nodes_searched': self.nodes_searched,
            'is_complete': self.is_complete,
            'mate_found': self.mate_found,
            'best_move': self.best_move,
            'original_best_move': self.original_best_move,
            'candidate_count': len(self.candidates),
            'intelligence_applied': self.intelligence_applied,
            'intelligence_avoided': self.intelligence_avoided,
            'intelligence_decision_reason': self.intelligence_decision_reason
        }