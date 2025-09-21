"""
Enhanced chess engine wrapper with complete intelligence implementation and new controls
FEATURES: Disable Intelligence + Avoid Low Intelligence with threshold comparison
CRITICAL FIX: Checkmate moves now get absolute evaluation of 1000 instead of multiplication
"""

import os
import subprocess
import time
import re
import random
import math
import chess
import chess.engine
from threading import Thread, Lock, Event
from queue import Queue, Empty
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime

from constants import engine_logger
from models import MoveEvaluation, IntelligenceSettings, MoveCandidate, GameState

def enqueue_output(out, queue):
    """Read output from subprocess and queue it"""
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

class EngineChess:
    """Chess engine wrapper with advanced intelligence features and controls"""
    
    def __init__(self, path_engine: str, is_maia: bool = False, 
                 maia_config: Dict = None, book_config: Dict = None, 
                 tablebase_config: Dict = None, intelligence_settings: IntelligenceSettings = None):
        self._engine = subprocess.Popen(
            path_engine,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.queueOutput = Queue()
        self.thread = Thread(target=enqueue_output, args=(self._engine.stdout, self.queueOutput))
        self.thread.daemon = True
        self.thread.start()

        self._command_queue = Queue()
        self._queue_lock = Lock()
        self._has_quit_command_been_sent = False
        self._current_turn = "w"
        self.is_maia = is_maia
        self.maia_config = maia_config or {}
        self.book_config = book_config or {}
        self.tablebase_config = tablebase_config or {}
        self.intelligence_settings = intelligence_settings or IntelligenceSettings()
        self.is_initialized = False

        self.opening_book = None
        self.tablebase_path = None
        self.setup_book_and_tablebase()
        
        # Intelligence features state
        self.current_position_eval = 0.0
        self.piece_count = 32
        self.last_moves = []
        self.move_evaluations = []
        self.current_fen = None
        self.multipv = 3  # Default MultiPV for intelligence
        
        # NEW: Intelligence decision tracking
        self.intelligence_decisions_log = []
        self.total_decisions = 0
        self.intelligence_used_count = 0
        self.intelligence_avoided_count = 0
        
        # Initialize ALL engines immediately
        self.initialize_engine()

        engine_logger.info(f"Engine created: path={path_engine}, is_maia={is_maia}")

    def setup_book_and_tablebase(self):
        """Setup opening book and tablebase paths"""
        if self.book_config.get('enabled') and self.book_config.get('book_file'):
            book_file = self.book_config['book_file']
            if os.path.exists(book_file):
                self.opening_book = book_file
                engine_logger.info(f"Loaded opening book: {book_file}")

        if self.tablebase_config.get('enabled') and self.tablebase_config.get('tablebase_path'):
            tb_path = self.tablebase_config['tablebase_path']
            if os.path.exists(tb_path):
                self.tablebase_path = tb_path
                engine_logger.info(f"Loaded tablebase path: {tb_path}")

    def put(self, cmd: str):
        """Queue a command to be sent to the engine"""
        if not cmd or not cmd.strip():
            engine_logger.debug("Ignoring empty command")
            return
            
        cmd = cmd.strip()
        with self._queue_lock:
            self._command_queue.put(cmd)
            engine_logger.debug(f"Queued command: {cmd}")

    def send_next_command(self):
        """Send the next queued command to the engine"""
        with self._queue_lock:
            if not self._command_queue.empty():
                cmd = self._command_queue.get()
                if self._engine.stdin and not self._has_quit_command_been_sent:
                    self._engine.stdin.write(f"{cmd}\n")
                    self._engine.stdin.flush()
                    engine_logger.debug(f"Sent to engine: {cmd}")
                    if cmd == "quit":
                        self._has_quit_command_been_sent = True

    def initialize_engine(self):
        """Initialize ANY UCI engine (Maia, Leela, Stockfish, etc.)"""
        if self.is_initialized:
            return
            
        engine_logger.info(f"Initializing {'Maia' if self.is_maia else 'UCI'} chess engine...")

        # Send UCI command to enter UCI mode
        self.put("uci")
        time.sleep(0.5)

        # Configure Maia-specific settings
        if self.is_maia and self.maia_config:
            if 'weights_file' in self.maia_config:
                self.put(f"setoption name WeightsFile value {self.maia_config['weights_file']}")
                engine_logger.info(f"Set Maia weights: {self.maia_config['weights_file']}")

            self.put("setoption name Threads value 1")
            self.put("setoption name MinibatchSize value 1")
            self.put("setoption name MaxPrefetch value 0")

            nodes_limit = self.maia_config.get('nodes_per_second_limit', 0.001)
            self.put(f"setoption name NodesPerSecondLimit value {nodes_limit}")

            if self.maia_config.get('use_slowmover', False):
                self.put("setoption name SlowMover value 0")
        else:
            # For non-Maia engines, set MultiPV for intelligence features
            if self.intelligence_settings.intelligence_enabled:
                self.put(f"setoption name MultiPV value {self.multipv}")
                engine_logger.info(f"Set MultiPV to {self.multipv} for intelligence features")

        # Configure opening book for all engines
        if self.opening_book:
            for book_option in ["Book", "BookFile", "OwnBook", "UseBook"]:
                self.put(f"setoption name {book_option} value true")
            self.put(f"setoption name BookFile value {self.opening_book}")
            engine_logger.info(f"Configured opening book: {self.opening_book}")

        # Configure tablebase for all engines
        if self.tablebase_path:
            for tb_option in ["SyzygyPath", "TablebasePath", "Tablebase", "TbPath"]:
                self.put(f"setoption name {tb_option} value {self.tablebase_path}")
            engine_logger.info(f"Configured tablebase: {self.tablebase_path}")

        # Send isready and wait for readyok
        self.put("isready")
        
        # Process all queued commands to ensure initialization completes
        for _ in range(10):
            self.send_next_command()
            time.sleep(0.1)
        
        self.is_initialized = True
        engine_logger.info(f"{'Maia' if self.is_maia else 'UCI'} engine initialization complete!")

    def analyze_position(self, fen: str, depth: int = 15, movetime: int = None) -> List[MoveCandidate]:
        """Analyze position and return candidate moves with evaluations"""
        candidates = []
        self.current_fen = fen
        
        engine_logger.info(f"Analyzing position: {fen[:50]}... depth={depth}")
        
        # Set position
        self.put(f"position fen {fen}")
        
        # Start analysis
        if movetime:
            self.put(f"go movetime {movetime}")
        else:
            self.put(f"go depth {depth}")
        
        # Collect engine output
        info_lines = []
        bestmove = None
        timeout = time.time() + (movetime/1000 if movetime else 30)  # Max 30 seconds
        
        while time.time() < timeout:
            lines = self.read_available_lines()
            
            for line in lines:
                if line.startswith("info"):
                    info_lines.append(line)
                elif line.startswith("bestmove"):
                    bestmove = line.split()[1] if len(line.split()) > 1 else None
                    break
            
            if bestmove:
                break
            
            time.sleep(0.01)
        
        # Parse candidate moves from info lines
        multipv_moves = {}
        
        for line in info_lines:
            if "multipv" in line:
                # Parse MultiPV line
                multipv_match = re.search(r'multipv (\d+)', line)
                pv_match = re.search(r'pv (\S+)', line)
                score_cp_match = re.search(r'score cp (-?\d+)', line)
                score_mate_match = re.search(r'score mate (-?\d+)', line)
                depth_match = re.search(r'depth (\d+)', line)
                
                if multipv_match and pv_match:
                    multipv_idx = int(multipv_match.group(1))
                    move = pv_match.group(1)
                    depth_val = int(depth_match.group(1)) if depth_match else 0
                    
                    if score_mate_match:
                        mate_in = int(score_mate_match.group(1))
                        score_cp = 10000 if mate_in > 0 else -10000
                        score_pawns = 100.0 if mate_in > 0 else -100.0
                    elif score_cp_match:
                        score_cp = int(score_cp_match.group(1))
                        score_pawns = score_cp / 100.0
                    else:
                        score_cp = 0
                        score_pawns = 0.0
                    
                    # Create move candidate
                    try:
                        chess_move = chess.Move.from_uci(move)
                        from_square = chess.square_name(chess_move.from_square)
                        to_square = chess.square_name(chess_move.to_square)
                        
                        candidate = MoveCandidate(
                            move=move,
                            from_square=from_square,
                            to_square=to_square,
                            score_cp=score_cp,
                            score_pawns=score_pawns,
                            depth=depth_val,
                            mate_in=int(score_mate_match.group(1)) if score_mate_match else None
                        )
                        
                        multipv_moves[multipv_idx] = candidate
                        
                    except:
                        engine_logger.warning(f"Failed to parse move: {move}")
            
            elif "pv" in line and not multipv_moves:
                # Single PV line (no MultiPV)
                pv_match = re.search(r'pv (\S+)', line)
                score_cp_match = re.search(r'score cp (-?\d+)', line)
                score_mate_match = re.search(r'score mate (-?\d+)', line)
                depth_match = re.search(r'depth (\d+)', line)
                
                if pv_match:
                    move = pv_match.group(1)
                    depth_val = int(depth_match.group(1)) if depth_match else 0
                    
                    if score_mate_match:
                        mate_in = int(score_mate_match.group(1))
                        score_cp = 10000 if mate_in > 0 else -10000
                        score_pawns = 100.0 if mate_in > 0 else -100.0
                    elif score_cp_match:
                        score_cp = int(score_cp_match.group(1))
                        score_pawns = score_cp / 100.0
                    else:
                        score_cp = 0
                        score_pawns = 0.0
                    
                    try:
                        chess_move = chess.Move.from_uci(move)
                        from_square = chess.square_name(chess_move.from_square)
                        to_square = chess.square_name(chess_move.to_square)
                        
                        candidate = MoveCandidate(
                            move=move,
                            from_square=from_square,
                            to_square=to_square,
                            score_cp=score_cp,
                            score_pawns=score_pawns,
                            depth=depth_val,
                            mate_in=int(score_mate_match.group(1)) if score_mate_match else None
                        )
                        
                        multipv_moves[1] = candidate
                        
                    except:
                        engine_logger.warning(f"Failed to parse move: {move}")
        
        # Convert to list sorted by multipv index
        for idx in sorted(multipv_moves.keys()):
            candidates.append(multipv_moves[idx])
        
        # If no candidates but we have a bestmove, create one
        if not candidates and bestmove:
            try:
                chess_move = chess.Move.from_uci(bestmove)
                from_square = chess.square_name(chess_move.from_square)
                to_square = chess.square_name(chess_move.to_square)
                
                candidate = MoveCandidate(
                    move=bestmove,
                    from_square=from_square,
                    to_square=to_square,
                    score_cp=0,
                    score_pawns=0.0,
                    depth=depth
                )
                candidates.append(candidate)
                
            except:
                engine_logger.warning(f"Failed to parse bestmove: {bestmove}")
        
        engine_logger.info(f"Found {len(candidates)} candidate moves")
        return candidates

    def get_best_move_with_intelligence(self, fen: str, game_state: GameState, 
                                       depth: int = 15, movetime: int = None) -> Optional[str]:
        """Get best move with NEW intelligence controls: disable + avoid low intelligence"""
        
        # Don't apply intelligence if using Maia
        if self.is_maia:
            engine_logger.info("Maia engine - using vanilla analysis")
            candidates = self.analyze_position(fen, depth, movetime)
            return candidates[0].move if candidates else None
        
        # NEW FEATURE 1: Check if intelligence is completely disabled
        if self.intelligence_settings.is_fully_disabled():
            engine_logger.info("Intelligence DISABLED - using pure engine analysis")
            candidates = self.analyze_position(fen, depth, movetime)
            self._log_intelligence_decision("disabled", "Intelligence completely disabled")
            return candidates[0].move if candidates else None
        
        # Get candidate moves from engine
        candidates = self.analyze_position(fen, depth, movetime)
        
        if not candidates:
            engine_logger.warning("No candidate moves found")
            return None
        
        engine_logger.info(f"Intelligence ENABLED - applying with threshold checking")
        
        # Store original engine move for comparison
        original_engine_move = candidates[0].move
        original_engine_eval = candidates[0].score_pawns
        
        # Create intelligent engine manager for move selection
        manager = EnhancedIntelligentEngineManager([self], self.intelligence_settings)
        
        # Update game state
        game_state.update_from_fen(fen)
        
        # Apply intelligence to get modified candidates
        intelligent_candidates = manager.apply_intelligence_modifications(candidates, game_state)
        
        if not intelligent_candidates:
            engine_logger.warning("Intelligence failed - falling back to engine move")
            self._log_intelligence_decision("failed", "Intelligence processing failed")
            return original_engine_move
        
        # Get the intelligence-selected move
        intelligent_move = intelligent_candidates[0].move
        intelligent_eval = intelligent_candidates[0].score_pawns
        
        # NEW FEATURE 2: Avoid low intelligence - compare evaluations using THRESHOLD
        threshold = self.intelligence_settings.get_threshold()
        
        engine_logger.info(f"THRESHOLD COMPARISON:")
        engine_logger.info(f"  Engine evaluation: {original_engine_eval:.2f}")
        engine_logger.info(f"  Intelligence evaluation: {intelligent_eval:.2f}")
        engine_logger.info(f"  Threshold: {threshold:.2f}")
        
        if intelligent_eval > threshold:
            engine_logger.info(f"  RESULT: USE intelligence ({intelligent_eval:.2f} > {threshold:.2f})")
            self._log_intelligence_decision("used", f"Intelligence move: {intelligent_move}, eval: {intelligent_eval:.2f}")
            return intelligent_move
        else:
            engine_logger.info(f"  RESULT: AVOID intelligence ({intelligent_eval:.2f} <= {threshold:.2f})")
            self._log_intelligence_decision("avoided", f"Intelligence eval {intelligent_eval:.2f} <= threshold {threshold:.2f}")
            return original_engine_move

    def _log_intelligence_decision(self, decision: str, reason: str):
        """Log intelligence decision for tracking and statistics"""
        self.total_decisions += 1
        
        if decision == "used":
            self.intelligence_used_count += 1
        elif decision == "avoided":
            self.intelligence_avoided_count += 1
        
        decision_log = {
            'timestamp': datetime.now(),
            'decision': decision,
            'reason': reason,
            'total_decisions': self.total_decisions,
            'usage_rate': (self.intelligence_used_count / self.total_decisions * 100) if self.total_decisions > 0 else 0
        }
        
        self.intelligence_decisions_log.append(decision_log)
        
        # Keep log size manageable
        if len(self.intelligence_decisions_log) > 100:
            self.intelligence_decisions_log = self.intelligence_decisions_log[-50:]
        
        engine_logger.info(f"FINAL MOVE DECISION: {decision}")
        engine_logger.info(f"Original engine move: {self.intelligence_decisions_log[-1].get('original_move', 'unknown')}")
        engine_logger.info(f"Final selected move: {self.intelligence_decisions_log[-1].get('final_move', 'unknown')}")
        engine_logger.info(f"Decision reason: {reason}")

    def get_intelligence_statistics(self) -> Dict[str, Any]:
        """Get detailed intelligence usage statistics"""
        if self.total_decisions == 0:
            return {
                'total_decisions': 0,
                'intelligence_used': 0,
                'intelligence_avoided': 0,
                'intelligence_disabled': 0,
                'usage_rate': 0.0,
                'avoidance_rate': 0.0,
                'recent_decisions': []
            }
        
        disabled_count = sum(1 for log in self.intelligence_decisions_log if log['decision'] == 'disabled')
        
        return {
            'total_decisions': self.total_decisions,
            'intelligence_used': self.intelligence_used_count,
            'intelligence_avoided': self.intelligence_avoided_count,
            'intelligence_disabled': disabled_count,
            'usage_rate': (self.intelligence_used_count / self.total_decisions) * 100,
            'avoidance_rate': (self.intelligence_avoided_count / self.total_decisions) * 100,
            'recent_decisions': self.intelligence_decisions_log[-10:]  # Last 10 decisions
        }

    def _read_line(self) -> str:
        """Read a line from the engine output"""
        if not self._engine.stdout:
            raise BrokenPipeError()
        if self._engine.poll() is not None:
            raise Exception("The engine process has crashed")

        try:
            line = self.queueOutput.get_nowait()
        except Empty:
            return ""

        return line.strip()

    def read_line(self) -> str:
        """Read a line from the engine, sending next command if needed"""
        self.send_next_command()
        line = self._read_line()
        
        if not line:
            return ""
        
        engine_logger.debug(f"Engine output: {line}")
        return line
    
    def read_available_lines(self) -> List[str]:
        """Read all currently available lines from the engine"""
        self.send_next_command()
        lines = []
        
        max_lines = 100  # Increased for MultiPV output
        for _ in range(max_lines):
            try:
                line = self.queueOutput.get_nowait()
                if line:
                    line = line.strip()
                    if line:
                        lines.append(line)
                        engine_logger.debug(f"Engine output: {line}")
            except Empty:
                break
        
        return lines
    
    def quit(self):
        """Properly quit the engine"""
        engine_logger.info("Shutting down engine")
        self.put("quit")
        time.sleep(0.5)
        if self._engine.poll() is None:
            self._engine.terminate()
            self._engine.wait(timeout=2)


class EnhancedIntelligentEngineManager:
    """Enhanced engine manager with complete intelligence implementation and NEW controls"""
    
    def __init__(self, engines: List[EngineChess], intelligence_settings: IntelligenceSettings):
        self.engines = engines
        self.intelligence_settings = intelligence_settings
        self.primary_engine = engines[0] if engines else None
        self.settings_manager = None
        
        # Analysis state
        self.current_candidates = []
        self.analysis_history = []
        self.opening_book_moves = {}
        self.position_evaluations = {}
        
        # Performance tracking
        self.total_positions_analyzed = 0
        self.total_moves_selected = 0
        
        engine_logger.info(f"Enhanced intelligent engine manager created with {len(engines)} engines")
        engine_logger.info(f"Intelligence enabled: {intelligence_settings.intelligence_enabled}")
        engine_logger.info(f"Avoid low intelligence: {intelligence_settings.avoid_low_intelligence}")
        engine_logger.info(f"Low intelligence threshold: {intelligence_settings.low_intelligence_threshold}")
    
    def set_settings_manager(self, settings_manager):
        """Set settings manager for configuration access"""
        self.settings_manager = settings_manager
        engine_logger.info("Settings manager linked to intelligent engine manager")
    
    def update_intelligence_settings(self, settings: IntelligenceSettings):
        """Update intelligence settings and propagate to engines"""
        self.intelligence_settings = settings
        for engine in self.engines:
            engine.intelligence_settings = settings
        engine_logger.info(f"Intelligence settings updated: enabled={settings.intelligence_enabled}")
    
    def apply_intelligence_modifications(self, candidates: List[MoveCandidate], 
                                       game_state: GameState) -> List[MoveCandidate]:
        """Apply intelligence modifications to candidates with CRITICAL CHECKMATE FIX"""
        
        engine_logger.info("=== APPLYING INTELLIGENCE MODIFICATIONS ===")
        
        # NEW CONTROL 1: Check if intelligence is completely disabled
        if self.intelligence_settings.is_fully_disabled():
            engine_logger.info("Intelligence completely disabled - returning original candidates")
            return candidates
        
        # Don't apply intelligence if using Maia
        if self.primary_engine and self.primary_engine.is_maia:
            engine_logger.info("Maia engine detected - skipping intelligence features")
            return candidates
        
        if not candidates:
            engine_logger.warning("No candidates to modify")
            return candidates
        
        engine_logger.info(f"Intelligence enabled - modifying {len(candidates)} candidates")
        
        # Get the current board
        board = game_state.current_board
        if not board:
            engine_logger.warning("No board state available")
            return candidates
        
        # CRITICAL FIX: Check for checkmate moves FIRST and set absolute values
        mate_moves_found = []
        for candidate in candidates:
            try:
                move = chess.Move.from_uci(candidate.move)
                board_copy = board.copy()
                board_copy.push(move)
                
                if board_copy.is_checkmate():
                    # CRITICAL FIX: Set absolute evaluation to 1000 for checkmate
                    candidate.score_pawns = 1000.0
                    candidate.score_cp = 100000
                    mate_moves_found.append(candidate.move)
                    engine_logger.info(f"!!! CHECKMATE FOUND - set to 1000: {candidate.move}")
            except:
                continue
        
        # Check if we're in a critical position
        is_critical = self.is_critical_position(board)
        if is_critical:
            engine_logger.info("Critical position detected - limiting intelligence modifications")
        
        modified_candidates = []
        
        for i, candidate in enumerate(candidates):
            try:
                # Create a copy with potentially modified evaluation
                modified_candidate = MoveCandidate(
                    move=candidate.move,
                    from_square=candidate.from_square,
                    to_square=candidate.to_square,
                    score_cp=candidate.score_cp,
                    score_pawns=candidate.score_pawns,
                    depth=candidate.depth,
                    mate_in=candidate.mate_in,
                    pv_line=candidate.pv_line
                )
                
                # SKIP INTELLIGENCE MODIFICATIONS FOR CHECKMATE MOVES - they're already set to 1000
                if candidate.move in mate_moves_found:
                    engine_logger.info(f"Skipping intelligence modifications for mate move: {candidate.move}")
                    modified_candidates.append(modified_candidate)
                    continue
                
                # Store original evaluation
                original_eval = candidate.score_pawns
                modified_eval = original_eval
                total_multiplier = 1.0
                
                # Apply intelligence modifications to non-mate moves
                try:
                    move_obj = chess.Move.from_uci(candidate.move)
                    
                    # Get moving piece type
                    moving_piece = board.piece_at(move_obj.from_square)
                    if moving_piece:
                        piece_type = moving_piece.piece_type
                        
                        # Apply piece preference multiplier
                        piece_multipliers = {
                            chess.PAWN: self.intelligence_settings.pawn_preference,
                            chess.KNIGHT: self.intelligence_settings.knight_preference,
                            chess.BISHOP: self.intelligence_settings.bishop_preference,
                            chess.ROOK: self.intelligence_settings.rook_preference,
                            chess.QUEEN: self.intelligence_settings.queen_preference,
                            chess.KING: self.intelligence_settings.king_preference
                        }
                        piece_mult = piece_multipliers.get(piece_type, 1.0)
                        if piece_mult != 1.0:
                            modified_eval = self.apply_chess_multiplier(modified_eval, piece_mult, is_critical)
                            total_multiplier *= piece_mult
                            engine_logger.debug(f"Move {candidate.move}: Piece mult={piece_mult:.2f}")
                        
                        # Check move characteristics
                        is_capture = board.is_capture(move_obj)
                        is_castling = board.is_castling(move_obj)
                        is_en_passant = board.is_en_passant(move_obj)
                        is_promotion = move_obj.promotion is not None
                        creates_pin = self.detect_pin_moves(board, move_obj)
                        
                        # Calculate aggressiveness/passiveness
                        aggression_score = self.calculate_aggressiveness_score(board, move_obj)
                        is_aggressive = aggression_score > 1
                        is_passive = aggression_score <= 1
                        
                        # Apply aggressiveness contempt
                        if is_aggressive and self.intelligence_settings.aggressiveness_contempt != 1.0:
                            modified_eval = self.apply_chess_multiplier(modified_eval, self.intelligence_settings.aggressiveness_contempt, is_critical)
                            total_multiplier *= self.intelligence_settings.aggressiveness_contempt
                            engine_logger.debug(f"Move {candidate.move}: Aggressive mult={self.intelligence_settings.aggressiveness_contempt:.2f}")
                        
                        # Apply passiveness contempt
                        if is_passive and self.intelligence_settings.passiveness_contempt != 1.0:
                            modified_eval = self.apply_chess_multiplier(modified_eval, self.intelligence_settings.passiveness_contempt, is_critical)
                            total_multiplier *= self.intelligence_settings.passiveness_contempt
                            engine_logger.debug(f"Move {candidate.move}: Passive mult={self.intelligence_settings.passiveness_contempt:.2f}")
                        
                        # Apply capture preference
                        if is_capture and self.intelligence_settings.capture_preference != 1.0:
                            modified_eval = self.apply_chess_multiplier(modified_eval, self.intelligence_settings.capture_preference, is_critical)
                            total_multiplier *= self.intelligence_settings.capture_preference
                            engine_logger.debug(f"Move {candidate.move}: Capture mult={self.intelligence_settings.capture_preference:.2f}")
                        
                        # Apply castle preference
                        if is_castling:
                            modified_eval = self.apply_chess_multiplier(modified_eval, self.intelligence_settings.castle_preference, is_critical)
                            total_multiplier *= self.intelligence_settings.castle_preference
                            engine_logger.debug(f"Move {candidate.move}: Castle mult={self.intelligence_settings.castle_preference:.2f}")
                            
                            # Apply early castling preference
                            if self.intelligence_settings.prefer_early_castling and game_state.move_number <= 15:
                                early_castle_mult = 1.2
                                modified_eval = self.apply_chess_multiplier(modified_eval, early_castle_mult, is_critical)
                                total_multiplier *= early_castle_mult
                                engine_logger.debug(f"Move {candidate.move}: Early castle bonus=1.2")
                            
                            # Apply castle side preference
                            if self.intelligence_settings.prefer_side_castle and self.intelligence_settings.castle_side:
                                if self.intelligence_settings.castle_side == "kingside" and move_obj.to_square > move_obj.from_square:
                                    side_mult = 1.2
                                    modified_eval = self.apply_chess_multiplier(modified_eval, side_mult, is_critical)
                                    total_multiplier *= side_mult
                                    engine_logger.debug(f"Move {candidate.move}: Kingside preference=1.2")
                                elif self.intelligence_settings.castle_side == "queenside" and move_obj.to_square < move_obj.from_square:
                                    side_mult = 1.2
                                    modified_eval = self.apply_chess_multiplier(modified_eval, side_mult, is_critical)
                                    total_multiplier *= side_mult
                                    engine_logger.debug(f"Move {candidate.move}: Queenside preference=1.2")
                        
                        # Apply en passant preference
                        if is_en_passant and self.intelligence_settings.en_passant_preference != 1.0:
                            modified_eval = self.apply_chess_multiplier(modified_eval, self.intelligence_settings.en_passant_preference, is_critical)
                            total_multiplier *= self.intelligence_settings.en_passant_preference
                            engine_logger.debug(f"Move {candidate.move}: En passant mult={self.intelligence_settings.en_passant_preference:.2f}")
                        
                        # Apply promotion preference
                        if is_promotion and self.intelligence_settings.promotion_preference != 1.0:
                            modified_eval = self.apply_chess_multiplier(modified_eval, self.intelligence_settings.promotion_preference, is_critical)
                            total_multiplier *= self.intelligence_settings.promotion_preference
                            engine_logger.debug(f"Move {candidate.move}: Promotion mult={self.intelligence_settings.promotion_preference:.2f}")
                        
                        # Apply pin preference
                        if creates_pin and self.intelligence_settings.prefer_pins:
                            pin_mult = 1.1
                            modified_eval = self.apply_chess_multiplier(modified_eval, pin_mult, is_critical)
                            total_multiplier *= pin_mult
                            engine_logger.debug(f"Move {candidate.move}: Pin bonus=1.1")
                        
                        # Apply trading preference
                        is_trade, trade_value = self.is_direct_trade(board, move_obj)
                        if is_trade and self.intelligence_settings.trading_preference != 0:
                            if trade_value >= self.intelligence_settings.trading_preference:
                                # This trade meets our threshold
                                trade_mult = 1.5
                                modified_eval = self.apply_chess_multiplier(modified_eval, trade_mult, is_critical)
                                total_multiplier *= trade_mult
                                engine_logger.debug(f"Move {candidate.move}: Trade boost (value={trade_value:.1f} >= threshold={self.intelligence_settings.trading_preference:.1f})")
                            else:
                                # This trade doesn't meet our threshold
                                trade_mult = 0.5
                                modified_eval = self.apply_chess_multiplier(modified_eval, trade_mult, is_critical)
                                total_multiplier *= trade_mult
                                engine_logger.debug(f"Move {candidate.move}: Trade penalty (value={trade_value:.1f} < threshold={self.intelligence_settings.trading_preference:.1f})")
                        
                        engine_logger.info(f"Move {candidate.move}: Original={original_eval:.2f}, Modified={modified_eval:.2f}, Multiplier={total_multiplier:.2f}")
                        
                        # Apply the modification to the candidate
                        if abs(total_multiplier - 1.0) > 0.01:  # Only if significant change
                            modified_candidate.score_pawns = modified_eval
                            modified_candidate.score_cp = int(modified_eval * 100)
                
                except Exception as e:
                    engine_logger.warning(f"Error analyzing move {candidate.move}: {e}")
                
                modified_candidates.append(modified_candidate)
                
            except Exception as e:
                engine_logger.warning(f"Error modifying candidate {candidate.move}: {e}")
                modified_candidates.append(candidate)  # Keep original
        
        # Apply special intelligence behaviors
        modified_candidates = self.apply_special_behaviors(modified_candidates, board, game_state)
        
        # Sort by modified evaluations (highest first)
        modified_candidates.sort(key=lambda x: x.score_pawns, reverse=True)
        
        engine_logger.info(f"Intelligence modifications complete - returning {len(modified_candidates)} candidates")
        return modified_candidates
    
    def apply_special_behaviors(self, candidates: List[MoveCandidate], board: chess.Board, 
                              game_state: GameState) -> List[MoveCandidate]:
        """Apply special intelligence behaviors (checkmate, stalemate, etc.)"""
        
        # CHECKMATE IMMEDIATELY - but don't multiply, set absolute values
        if self.intelligence_settings.checkmate_immediately:
            engine_logger.debug("Checking for additional checkmate moves...")
            mate_move = self.find_checkmate_in_n(board, 3)
            if mate_move:
                # Find and boost mate move to absolute 1000
                for candidate in candidates:
                    if candidate.move == mate_move.uci():
                        candidate.score_pawns = 1000.0
                        candidate.score_cp = 100000
                        engine_logger.info(f"!!! CHECKMATE FOUND - set to 1000: {candidate.move}")
                        break
        
        # STALEMATE PROBABILITY
        if self.intelligence_settings.stalemate_probability > 0:
            engine_logger.debug(f"Checking for stalemate (prob={self.intelligence_settings.stalemate_probability})...")
            for candidate in candidates:
                try:
                    move = chess.Move.from_uci(candidate.move)
                    board_copy = board.copy()
                    board_copy.push(move)
                    
                    if board_copy.is_stalemate():
                        if random.random() < self.intelligence_settings.stalemate_probability:
                            candidate.score_pawns = 50.0
                            candidate.score_cp = 5000
                            engine_logger.info(f"!!! STALEMATE BOOSTED: {candidate.move}")
                except:
                    continue
        
        # ALWAYS PROMOTE TO QUEEN
        if self.intelligence_settings.always_promote_queen:
            engine_logger.debug("Filtering non-queen promotions...")
            filtered_candidates = []
            for candidate in candidates:
                try:
                    move = chess.Move.from_uci(candidate.move)
                    # Check if it's a promotion
                    if move.promotion:
                        # Only allow queen promotions
                        if move.promotion == chess.QUEEN:
                            filtered_candidates.append(candidate)
                        # Skip non-queen promotions
                    else:
                        # Not a promotion, keep it
                        filtered_candidates.append(candidate)
                except:
                    filtered_candidates.append(candidate)
            
            if filtered_candidates:
                candidates = filtered_candidates
                engine_logger.info(f"Filtered to {len(candidates)} candidates (queen promotions only)")
        
        # STAY EQUAL MODE
        if self.intelligence_settings.stay_equal and game_state.current_evaluation > 1.5:
            engine_logger.info("Applying stay equal mode...")
            filtered_candidates = []
            for candidate in candidates:
                if 0.5 < candidate.score_pawns < game_state.current_evaluation - 0.3:
                    filtered_candidates.append(candidate)
            
            if filtered_candidates:
                candidates = filtered_candidates
                engine_logger.info(f"Stay equal: filtered to {len(candidates)} moves")
        
        return candidates
    
    def detect_pin_moves(self, board: chess.Board, move: chess.Move) -> bool:
        """Detect if a move creates a pin on opponent pieces"""
        try:
            # Make the move temporarily
            board_copy = board.copy()
            board_copy.push(move)
            
            # Check if this move created any new pins
            opponent_color = not board_copy.turn
            for square in chess.SQUARES:
                piece = board_copy.piece_at(square)
                if piece and piece.color == opponent_color:
                    if board_copy.is_pinned(opponent_color, square):
                        # Check if this pin didn't exist before the move
                        if not board.is_pinned(opponent_color, square):
                            return True
            return False
        except:
            return False
    
    def calculate_aggressiveness_score(self, board: chess.Board, move: chess.Move) -> int:
        """Calculate aggressiveness score for a move"""
        score = 0
        
        try:
            # Make the move temporarily
            board_copy = board.copy()
            board_copy.push(move)
            
            # Check immediate capture
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                                  chess.ROOK: 5, chess.QUEEN: 9}
                    score += piece_values.get(captured_piece.piece_type, 0)
            
            # Check if opponent can capture our piece after this move
            opponent_moves = list(board_copy.legal_moves)
            for opp_move in opponent_moves:
                if board_copy.is_capture(opp_move) and opp_move.to_square == move.to_square:
                    moving_piece = board.piece_at(move.from_square)
                    if moving_piece:
                        piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                                      chess.ROOK: 5, chess.QUEEN: 9}
                        score += piece_values.get(moving_piece.piece_type, 0)
                    break
        except:
            pass
        
        return score
    
    def is_direct_trade(self, board: chess.Board, move: chess.Move) -> Tuple[bool, float]:
        """Check if move is a direct trade and calculate its value"""
        if not board.is_capture(move):
            return False, 0.0
        
        try:
            # Get the captured piece value
            captured_piece = board.piece_at(move.to_square)
            if not captured_piece:
                return False, 0.0
            
            piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                          chess.ROOK: 5, chess.QUEEN: 9}
            captured_value = piece_values.get(captured_piece.piece_type, 0)
            
            # Check if opponent can recapture
            board_copy = board.copy()
            board_copy.push(move)
            
            moving_piece = board.piece_at(move.from_square)
            moving_value = piece_values.get(moving_piece.piece_type, 0) if moving_piece else 0
            
            # Check for immediate recapture
            for opp_move in board_copy.legal_moves:
                if board_copy.is_capture(opp_move) and opp_move.to_square == move.to_square:
                    # This is a trade - calculate the net value
                    trade_value = captured_value - moving_value
                    return True, trade_value
            
            return False, 0.0
        except:
            return False, 0.0
    
    def find_checkmate_in_n(self, board: chess.Board, n: int = 3) -> Optional[chess.Move]:
        """Find checkmate in n moves or less"""
        try:
            for move in board.legal_moves:
                board_copy = board.copy()
                board_copy.push(move)
                
                if board_copy.is_checkmate():
                    return move
                
                if n > 1:
                    # Check if opponent has any move that avoids mate
                    can_avoid_mate = False
                    for opp_move in board_copy.legal_moves:
                        board_copy2 = board_copy.copy()
                        board_copy2.push(opp_move)
                        
                        # Recursively check if we can still mate
                        mate_move = self.find_checkmate_in_n(board_copy2, n - 1)
                        if not mate_move:
                            can_avoid_mate = True
                            break
                    
                    if not can_avoid_mate:
                        return move
        except:
            pass
        
        return None
    
    def is_critical_position(self, board: chess.Board) -> bool:
        """Check if position requires protection from intelligence modifications"""
        if not board:
            return False
        
        # Critical situations where intelligence should be limited
        if board.is_check():
            return True
        
        # Check if only few legal moves (forced positions)
        legal_moves = list(board.legal_moves)
        if len(legal_moves) <= 2:
            return True
        
        # Check for immediate mate threats
        for move in legal_moves:
            board_copy = board.copy()
            board_copy.push(move)
            if board_copy.is_checkmate():
                return True
        
        return False
    
    def apply_chess_multiplier(self, evaluation: float, multiplier: float, is_critical: bool = False) -> float:
        """Apply multiplier to chess evaluation with proper sign handling and critical protection"""
        if multiplier == 1.0 or evaluation == 0.0:
            return evaluation
        
        # In critical positions, limit intelligence modifications
        if is_critical:
            # Reduce multiplier effect in critical positions
            if multiplier > 1.0:
                multiplier = 1.0 + (multiplier - 1.0) * 0.3  # Reduce boost by 70%
            else:
                multiplier = 1.0 - (1.0 - multiplier) * 0.3  # Reduce penalty by 70%
            
            engine_logger.debug(f"Critical position: reduced multiplier to {multiplier:.2f}")
        
        if evaluation > 0:
            # Positive evaluation: normal multiplication
            return evaluation * multiplier
        else:
            # Negative evaluation: inverse relationship (higher multiplier = closer to zero)
            return evaluation / multiplier
    
    def get_intelligence_statistics(self) -> Dict[str, Any]:
        """Get intelligence application statistics"""
        engine_stats = {}
        if self.primary_engine:
            engine_stats = self.primary_engine.get_intelligence_statistics()
        
        return {
            'total_positions_analyzed': self.total_positions_analyzed,
            'total_moves_selected': self.total_moves_selected,
            'current_settings': self.intelligence_settings.to_dict(),
            'intelligence_enabled': self.intelligence_settings.intelligence_enabled,
            'avoid_low_intelligence': self.intelligence_settings.avoid_low_intelligence,
            'threshold': self.intelligence_settings.get_threshold(),
            'is_maia': self.primary_engine.is_maia if self.primary_engine else False,
            'engine_statistics': engine_stats
        }
    
    def reset_statistics(self):
        """Reset intelligence statistics"""
        self.total_positions_analyzed = 0
        self.total_moves_selected = 0
        if self.primary_engine:
            self.primary_engine.intelligence_decisions_log = []
            self.primary_engine.total_decisions = 0
            self.primary_engine.intelligence_used_count = 0
            self.primary_engine.intelligence_avoided_count = 0
        engine_logger.info("Intelligence statistics reset")


# Alias for backward compatibility
IntelligentEngineManager = EnhancedIntelligentEngineManager