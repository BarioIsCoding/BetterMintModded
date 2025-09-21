"""
Complete BetterMint Modded Server Rewrite with Enhanced Intelligence Integration
NEW FEATURES: Disable Intelligence + Avoid Low Intelligence with threshold comparison + Threat Arrows
"""

import asyncio
import json
import math
import os
import random
import re
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

import chess
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocketState

from constants import *
from models import Settings, ConnectionInfo, IntelligenceSettings, GameState
from settings import SettingsManager
from engine import EngineChess, EnhancedIntelligentEngineManager

# Configure logging
import logging
server_logger = logging.getLogger('bettermint.server')


class ThreatDetector:
    """Enhanced threat detection system - uses EnhancedThreatDetector for better analysis"""
    
    @staticmethod
    def detect_all_threats(board: chess.Board, max_player_threats: int = 5, max_opponent_threats: int = 3) -> Dict[str, List[Dict[str, str]]]:
        """Detect all threats using the enhanced detection system with custom limits"""
        try:
            # Import the enhanced detector
            from enhanced_threat_detection import EnhancedThreatDetector
            
            # Use enhanced detection with custom maximums and minimum threat value of 1.0 (pawns and above)
            return EnhancedThreatDetector.detect_all_threats(
                board, 
                min_threat_value=1.0,
                max_player_threats=max_player_threats,
                max_opponent_threats=max_opponent_threats
            )
            
        except ImportError:
            # Fallback to basic detection if enhanced version not available
            server_logger.warning("Enhanced threat detector not available, using basic detection")
            return ThreatDetector._basic_threat_detection(board, max_player_threats, max_opponent_threats)
        except Exception as e:
            server_logger.error(f"Error in enhanced threat detection: {e}")
            return ThreatDetector._basic_threat_detection(board, max_player_threats, max_opponent_threats)
    
    @staticmethod
    def _basic_threat_detection(board: chess.Board, max_player_threats: int = 5, max_opponent_threats: int = 3) -> Dict[str, List[Dict[str, str]]]:
        """Basic fallback threat detection with custom limits"""
        player_threats = []
        opponent_threats = []
        
        try:
            current_turn = board.turn
            
            # Basic player threats - just captures and checks
            if board.turn == current_turn:
                for move in list(board.legal_moves)[:10]:  # Limit to first 10 moves
                    from_sq = chess.square_name(move.from_square)
                    to_sq = chess.square_name(move.to_square)
                    
                    if board.is_capture(move):
                        captured = board.piece_at(move.to_square)
                        if captured and captured.piece_type != chess.PAWN:  # Skip pawn captures for basic version
                            player_threats.append({
                                'from': from_sq,
                                'to': to_sq,
                                'target': to_sq,
                                'threat_type': 'capture',
                                'value': 3.0
                            })
                    
                    # Check for checks
                    board_copy = board.copy()
                    board_copy.push(move)
                    if board_copy.is_check():
                        enemy_king = board_copy.king(not current_turn)
                        if enemy_king:
                            player_threats.append({
                                'from': from_sq,
                                'to': to_sq,
                                'target': chess.square_name(enemy_king),
                                'threat_type': 'check',
                                'value': 10.0
                            })
            
            # Basic opponent threats - pieces attacking our pieces
            for square in chess.SQUARES:
                piece = board.piece_at(square)
                if piece and piece.color != current_turn:
                    attacks = board.attacks(square)
                    for target in attacks:
                        target_piece = board.piece_at(target)
                        if target_piece and target_piece.color == current_turn:
                            if target_piece.piece_type != chess.PAWN:  # Skip pawn attacks for basic version
                                opponent_threats.append({
                                    'from': chess.square_name(square),
                                    'to': chess.square_name(target),
                                    'target': chess.square_name(target),
                                    'threat_type': 'attack',
                                    'value': ThreatDetector._get_basic_piece_value(target_piece.piece_type)
                                })
            
        except Exception as e:
            server_logger.error(f"Error in basic threat detection: {e}")
        
        return {
            'player_threats': player_threats[:max_player_threats],  # Respect custom limit
            'opponent_threats': opponent_threats[:max_opponent_threats]  # Respect custom limit
        }
    
    @staticmethod
    def _get_basic_piece_value(piece_type: int) -> float:
        """Get basic piece values"""
        values = {
            chess.PAWN: 1.0,
            chess.KNIGHT: 3.0,
            chess.BISHOP: 3.0,
            chess.ROOK: 5.0,
            chess.QUEEN: 9.0,
            chess.KING: 100.0
        }
        return values.get(piece_type, 0.0)


class GameStateManager:
    """Single source of truth for game state and move validation"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset to initial game state"""
        self.current_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.current_board = chess.Board()
        self.move_number = 1
        self.turn = 'w'
        self.game_phase = "opening"
        self.piece_count = 32
        self.position_history = []
        self.last_update_time = time.time()
        
        # Post-move analysis tracking
        self.last_move_played = None
        self.pre_move_recommendations = []
        self.move_analysis_pending = False
        self.move_analysis_timestamp = 0
        
        # INTELLIGENCE: Create game state object for intelligence system
        self.intelligence_game_state = GameState()
        
        server_logger.info("Game state reset to initial position")
    
    def update_position(self, fen: str) -> bool:
        """Update position with validation and move detection"""
        try:
            # Validate FEN
            board = chess.Board(fen)
            
            # Check for new game
            starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            if fen == starting_fen and self.current_fen != starting_fen:
                server_logger.info("New game detected - resetting state")
                self.reset()
                return True
            
            # Detect if a move was played
            move_played = None
            if self.current_board and self.current_fen != fen:
                try:
                    # Try to find the move that was played
                    for move in self.current_board.legal_moves:
                        test_board = self.current_board.copy()
                        test_board.push(move)
                        if test_board.fen() == fen:
                            move_played = move.uci()
                            break
                except:
                    pass
            
            # Store previous state for move analysis
            if move_played and self.pre_move_recommendations:
                self.last_move_played = move_played
                self.move_analysis_pending = True
                self.move_analysis_timestamp = time.time()
                server_logger.info(f"Move detected: {move_played}")
            
            # Update state
            self.current_fen = fen
            self.current_board = board
            self.move_number = board.fullmove_number
            self.turn = 'w' if board.turn else 'b'
            self.piece_count = len(board.piece_map())
            self.last_update_time = time.time()
            
            # INTELLIGENCE: Update intelligence game state
            self.intelligence_game_state.update_from_fen(fen)
            
            # Update game phase
            if board.fullmove_number <= 12:
                self.game_phase = "opening"
            elif self.piece_count <= 12:
                self.game_phase = "endgame"
            else:
                self.game_phase = "middlegame"
            
            # Track position history (for repetition detection)
            if len(self.position_history) == 0 or self.position_history[-1] != fen:
                self.position_history.append(fen)
                if len(self.position_history) > 50:
                    self.position_history = self.position_history[-25:]
            
            server_logger.debug(f"Position updated: {fen[:20]}... Move {self.move_number}, Phase {self.game_phase}")
            return True
            
        except Exception as e:
            server_logger.error(f"Invalid position update: {e}")
            return False
    
    def store_pre_move_analysis(self, candidates: List['MoveCandidate']):
        """Store analysis results before a move is played"""
        self.pre_move_recommendations = candidates.copy()
        self.move_analysis_pending = False
        server_logger.debug(f"Stored {len(candidates)} recommendations for post-move analysis")
    
    def get_move_analysis_quality(self) -> Optional[Tuple[str, str]]:
        """Get quality analysis for the last played move"""
        if not self.last_move_played or not self.pre_move_recommendations:
            return None
        
        # Find the played move in recommendations
        for i, candidate in enumerate(self.pre_move_recommendations):
            if candidate.move == self.last_move_played:
                rank = i + 1
                if rank == 1:
                    return ("BestMove", "#0080ff")
                elif rank == 2:
                    return ("Excellent", "#00ff00")
                elif rank == 3:
                    return ("Good", "#81c678")
                elif rank <= 5:
                    return ("Decent", "#ffff00")
                else:
                    return ("Inaccuracy", "#ff6600")
        
        # Move not in top recommendations
        if self.pre_move_recommendations:
            return ("Mistake", "#ff0000")
        
        return None
    
    def should_show_move_analysis(self) -> bool:
        """Check if post-move analysis badge should still be displayed"""
        if not self.move_analysis_pending or not self.last_move_played:
            return False
        
        # Show badge for 4 seconds after move is played
        badge_display_time = 4.0
        elapsed_time = time.time() - self.move_analysis_timestamp
        
        if elapsed_time > badge_display_time:
            server_logger.debug(f"Badge expired after {elapsed_time:.1f}s, clearing move analysis")
            self.clear_move_analysis()
            return False
        
        return True
    
    def clear_move_analysis(self):
        """Clear post-move analysis state"""
        self.last_move_played = None
        self.move_analysis_pending = False
        self.move_analysis_timestamp = 0
    
    def is_move_legal(self, move_uci: str) -> bool:
        """Validate if a move is legal in current position"""
        try:
            move = chess.Move.from_uci(move_uci)
            return move in self.current_board.legal_moves
        except:
            return False
    
    def get_legal_moves(self) -> List[str]:
        """Get all legal moves in current position"""
        return [move.uci() for move in self.current_board.legal_moves]
    
    def is_critical_position(self) -> bool:
        """Determine if position requires careful analysis"""
        if not self.current_board:
            return False
        
        # Check for tactical indicators
        if self.current_board.is_check():
            return True
        
        # Check for low material (endgame)
        if self.piece_count <= 10:
            return True
        
        return False


class MoveCandidate:
    """Represents an analyzed chess move with evaluation"""
    
    def __init__(self, move: str, score_cp: int = 0, depth: int = 0, mate_in: Optional[int] = None, pv_line: List[str] = None):
        self.move = move
        self.from_square = move[:2]
        self.to_square = move[2:4]
        self.promotion = move[4:] if len(move) > 4 else None
        
        self.score_cp = score_cp
        self.score_pawns = score_cp / 100.0 if score_cp is not None else 0.0
        self.mate_in = mate_in
        self.depth = depth
        self.pv_line = pv_line or []
        
        # Intelligence tracking
        self.original_score_pawns = self.score_pawns  # Store original engine evaluation
        self.intelligence_modified = False            # Track if intelligence modified this move
        self.intelligence_multiplier = 1.0           # Track the total multiplier applied
        
        # Move characteristics (for intelligence)
        self.is_capture = False
        self.is_check = False
        self.is_tactical = False
        self.is_positional = False
        self.is_critical = False  # For critical position detection
    
    def apply_intelligence_modification(self, new_score_pawns: float, multiplier: float):
        """Apply intelligence modification to this candidate"""
        self.original_score_pawns = self.score_pawns  # Store original if not already stored
        self.score_pawns = new_score_pawns
        self.score_cp = int(new_score_pawns * 100) if new_score_pawns is not None else self.score_cp
        self.intelligence_modified = True
        self.intelligence_multiplier = multiplier
    
    def analyze_characteristics(self, board: chess.Board):
        """Analyze move characteristics for intelligence"""
        try:
            move_obj = chess.Move.from_uci(self.move)
            
            self.is_capture = board.is_capture(move_obj)
            
            # Check if move gives check
            board_copy = board.copy()
            board_copy.push(move_obj)
            self.is_check = board_copy.is_check()
            
            # Check if this is a critical move (escaping check, preventing mate)
            if board.is_check():
                self.is_critical = True
            elif board_copy.is_checkmate():
                self.is_critical = True  # Delivers mate
            elif self.is_capture:
                # Check if this capture prevents immediate mate threat
                piece = board.piece_at(move_obj.from_square)
                if piece and piece.piece_type == chess.KING:
                    self.is_critical = True
            
            # Determine move type
            if self.is_capture or self.is_check:
                self.is_tactical = True
            else:
                self.is_positional = True
                
        except Exception as e:
            server_logger.warning(f"Failed to analyze move characteristics: {e}")


class AnalysisProcessor:
    """Processes UCI engine responses and creates move candidates"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset analysis state"""
        self.candidates = []
        self.depth_reached = 0
        self.nodes_searched = 0
        self.analysis_time = 0
        self.best_move = None
        self.evaluation = 0.0
        self.mate_score = None
        
    def process_info_line(self, line: str, game_state: GameStateManager) -> bool:
        """Process UCI info line and extract data"""
        try:
            # Extract depth
            depth_match = re.search(r'depth (\d+)', line)
            if depth_match:
                self.depth_reached = max(self.depth_reached, int(depth_match.group(1)))
            
            # Extract nodes
            nodes_match = re.search(r'nodes (\d+)', line)
            if nodes_match:
                self.nodes_searched = int(nodes_match.group(1))
            
            # Extract time
            time_match = re.search(r'time (\d+)', line)
            if time_match:
                self.analysis_time = int(time_match.group(1))
            
            # Extract score and PV
            pv_match = re.search(r'pv\s+([a-h][1-8][a-h][1-8][qrnb]?.*)', line)
            if not pv_match:
                return False
            
            pv_string = pv_match.group(1)
            pv_moves = pv_string.split()
            
            if not pv_moves:
                return False
            
            # Validate first move is properly formatted UCI move
            first_move = pv_moves[0]
            uci_move_pattern = re.compile(r'^[a-h][1-8][a-h][1-8][qrnb]?$')
            
            if not uci_move_pattern.match(first_move):
                server_logger.warning(f"Invalid UCI move format in PV: {first_move}")
                return False
            
            if not game_state.is_move_legal(first_move):
                server_logger.warning(f"Illegal move in PV: {first_move}")
                return False
            
            # Extract score
            score_cp = None
            mate_in = None
            
            if 'score cp' in line:
                cp_match = re.search(r'score cp (-?\d+)', line)
                if cp_match:
                    score_cp = int(cp_match.group(1))
                    self.evaluation = score_cp / 100.0
            elif 'score mate' in line:
                mate_match = re.search(r'score mate (-?\d+)', line)
                if mate_match:
                    mate_in = int(mate_match.group(1))
                    self.mate_score = mate_in
                    self.evaluation = 100.0 if mate_in > 0 else -100.0
            
            # Create candidate
            candidate = MoveCandidate(
                move=first_move,
                score_cp=score_cp,
                depth=self.depth_reached,
                mate_in=mate_in,
                pv_line=pv_moves[:5]
            )
            
            # Analyze move characteristics
            candidate.analyze_characteristics(game_state.current_board)
            
            # Update candidates list (keep unique moves only)
            existing_moves = [c.move for c in self.candidates]
            if first_move not in existing_moves:
                self.candidates.append(candidate)
                server_logger.debug(f"Added candidate: {first_move} (score: {score_cp})")
            else:
                # Update existing candidate with better analysis
                for i, c in enumerate(self.candidates):
                    if c.move == first_move:
                        if candidate.depth >= c.depth:
                            self.candidates[i] = candidate
                        break
            
            return True
            
        except Exception as e:
            server_logger.warning(f"Failed to process info line: {e}")
            return False
    
    def process_bestmove(self, line: str, game_state: GameStateManager) -> Optional[str]:
        """Process bestmove line and return the move"""
        try:
            match = re.search(r'bestmove\s+([a-h][1-8][a-h][1-8][qrnb]?)', line)
            if not match:
                return None
            
            move = match.group(1)
            if not game_state.is_move_legal(move):
                server_logger.warning(f"Illegal bestmove: {move}")
                return None
            
            self.best_move = move
            
            # Store analysis for post-move comparison
            sorted_candidates = self.get_sorted_candidates()
            if sorted_candidates:
                game_state.store_pre_move_analysis(sorted_candidates)
            
            server_logger.info(f"Best move: {move}")
            return move
            
        except Exception as e:
            server_logger.error(f"Failed to process bestmove: {e}")
            return None
    
    def get_sorted_candidates(self) -> List[MoveCandidate]:
        """Get candidates sorted by evaluation"""
        return sorted(self.candidates, 
                     key=lambda x: x.score_cp if x.score_cp is not None else -99999, 
                     reverse=True)
    
    def has_analysis(self) -> bool:
        """Check if we have any analysis data"""
        return len(self.candidates) > 0 or self.best_move is not None


class MoveExecutor:
    """Handles move timing and premove limiting"""
    
    def __init__(self, settings_manager: SettingsManager):
        self.settings_manager = settings_manager
        self.reset()
    
    def reset(self):
        """Reset execution state"""
        self.premove_count = 0
        self.total_moves = 0
        self.last_move_time = 0
        server_logger.info("Move executor reset - premove counter cleared")
    
    def should_auto_execute(self) -> bool:
        """Check if auto-execution is enabled"""
        return self.settings_manager.get_setting("legit-auto-move", False)
    
    def calculate_delay(self, game_state: GameStateManager) -> Tuple[int, str]:
        """Calculate move delay with proper premove limiting"""
        if not self.should_auto_execute():
            return 0, "manual"
        
        # Get settings
        premove_enabled = self.settings_manager.get_setting("premove-enabled", False)
        max_premoves = self.settings_manager.get_setting("max-premoves", 3)
        
        # Check premove limit BEFORE calculating timing
        if premove_enabled and self.premove_count < max_premoves:
            self.premove_count += 1
            delay = self._calculate_premove_timing()
            server_logger.info(f"Premove #{self.premove_count}/{max_premoves}: {delay}ms")
            return delay, "premove"
        else:
            delay = self._calculate_automove_timing(game_state)
            server_logger.info(f"Auto-move timing: {delay}ms")
            return delay, "automove"
    
    def _calculate_premove_timing(self) -> int:
        """Calculate premove timing with randomization"""
        base = self.settings_manager.get_setting("premove-time", 1000)
        random_range = self.settings_manager.get_setting("premove-time-random", 500)
        random_div = self.settings_manager.get_setting("premove-time-random-div", 100)
        random_multi = self.settings_manager.get_setting("premove-time-random-multi", 1)
        
        random_component = (random.randint(0, random_range - 1) % random_div) * random_multi
        total = base + random_component
        
        return max(50, min(total, 5000))  # 50ms to 5s
    
    def _calculate_automove_timing(self, game_state: GameStateManager) -> int:
        """Calculate auto-move timing with intelligence"""
        base = self.settings_manager.get_setting("auto-move-time", 5000)
        random_range = self.settings_manager.get_setting("auto-move-time-random", 2000)
        random_div = self.settings_manager.get_setting("auto-move-time-random-div", 10)
        random_multi = self.settings_manager.get_setting("auto-move-time-random-multi", 1000)
        
        # Base randomization
        random_component = (random.randint(0, random_range - 1) % random_div) * random_multi
        total = base + random_component
        
        return max(100, min(total, 30000))  # 100ms to 30s


class IntelligenceEngine:
    """Enhanced intelligence system with NEW controls: disable + avoid low intelligence"""
    
    def __init__(self, settings_manager: SettingsManager):
        self.settings_manager = settings_manager
    
    def is_intelligence_completely_disabled(self) -> bool:
        """NEW FEATURE 1: Check if intelligence is completely disabled"""
        return self.settings_manager.is_intelligence_fully_disabled()
    
    def should_avoid_low_intelligence(self) -> bool:
        """NEW FEATURE 2: Check if low intelligence avoidance is enabled"""
        return self.settings_manager.should_avoid_low_intelligence()
    
    def get_low_intelligence_threshold(self) -> float:
        """NEW FEATURE 2: Get the threshold for avoiding low intelligence"""
        return self.settings_manager.get_low_intelligence_threshold()
    
    def compare_intelligence_with_threshold(self, engine_eval: float, intelligence_eval: float) -> bool:
        """NEW FEATURE 2: Compare intelligence evaluation with threshold
        
        Returns True if intelligence should be used, False if it should be avoided
        """
        if not self.should_avoid_low_intelligence():
            return True  # No threshold checking, always use intelligence
        
        threshold = self.get_low_intelligence_threshold()
        
        server_logger.info(f"THRESHOLD COMPARISON:")
        server_logger.info(f"  Engine evaluation: {engine_eval:.2f}")
        server_logger.info(f"  Intelligence evaluation: {intelligence_eval:.2f}")
        server_logger.info(f"  Threshold: {threshold:.2f}")
        
        # If intelligence evaluation is at or below threshold, avoid it
        if intelligence_eval <= threshold:
            server_logger.info(f"  RESULT: AVOID intelligence ({intelligence_eval:.2f} <= {threshold:.2f})")
            return False
        else:
            server_logger.info(f"  RESULT: USE intelligence ({intelligence_eval:.2f} > {threshold:.2f})")
            return True
    
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
    
    def select_move_with_probability(self, candidates: List[MoveCandidate], 
                                   settings_manager: SettingsManager) -> Optional[str]:
        """Select move using best move chance probability distribution"""
        if not candidates:
            return None
        
        best_move_chance = settings_manager.get_setting("best-move-chance", 100)
        
        # If 100%, always return best move
        if best_move_chance >= 100:
            return candidates[0].move
        
        # Create probability distribution
        probabilities = self._calculate_probabilities(len(candidates), best_move_chance)
        
        # Select move based on probabilities
        rand_val = random.random() * 100
        cumulative_prob = 0
        
        for i, prob in enumerate(probabilities):
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                selected_move = candidates[i].move
                server_logger.info(f"Probabilistic selection: {selected_move} (rank {i+1}, prob {prob:.1f}%)")
                return selected_move
        
        # Fallback to best move
        return candidates[0].move
    
    def _calculate_probabilities(self, num_candidates: int, best_move_chance: float) -> List[float]:
        """Calculate probability distribution for move selection"""
        if num_candidates == 1:
            return [100.0]
        
        # Create decreasing probability distribution
        probabilities = []
        remaining_prob = 100.0
        
        # First move gets the specified chance
        probabilities.append(best_move_chance)
        remaining_prob -= best_move_chance
        
        # Distribute remaining probability with decreasing weights
        for i in range(1, num_candidates):
            # Exponentially decreasing probabilities
            weight = 1.0 / (2 ** i)  # 1, 0.5, 0.25, 0.125, ...
            
            # Last move gets whatever is left
            if i == num_candidates - 1:
                probabilities.append(remaining_prob)
            else:
                # Calculate proportional share
                total_remaining_weights = sum(1.0 / (2 ** j) for j in range(i, num_candidates))
                prob = (weight / total_remaining_weights) * remaining_prob
                probabilities.append(prob)
                remaining_prob -= prob
        
        return probabilities


class CommandGenerator:
    """Generates all extension commands atomically with NEW intelligence controls and threat arrows"""
    
    def __init__(self, settings_manager: SettingsManager, intelligence_manager: EnhancedIntelligentEngineManager = None):
        self.settings_manager = settings_manager
        self.intelligence_manager = intelligence_manager
        self.intelligence_engine = IntelligenceEngine(settings_manager)
    
    def set_intelligence_manager(self, intelligence_manager: EnhancedIntelligentEngineManager):
        """Set the intelligence manager for move selection"""
        self.intelligence_manager = intelligence_manager
        server_logger.info("Intelligence manager connected to command generator")
    
    def generate_all_commands(self, analysis: AnalysisProcessor, game_state: GameStateManager, 
                            move_executor: MoveExecutor, bestmove: Optional[str] = None) -> List[str]:
        """Generate all extension commands with NEW intelligence controls and threat arrows"""
        commands = []
        
        try:
            # Store original engine move for comparison
            original_engine_move = bestmove
            original_engine_eval = analysis.evaluation if analysis.has_analysis() else 0.0
            
            # NEW INTELLIGENCE CONTROL LOGIC
            final_move = bestmove
            intelligence_decision = "disabled"
            decision_reason = ""
            
            if bestmove and self.intelligence_manager:
                try:
                    # NEW FEATURE 1: Check if intelligence is completely disabled
                    if self.intelligence_engine.is_intelligence_completely_disabled():
                        server_logger.info("Intelligence COMPLETELY DISABLED - using engine move")
                        final_move = bestmove
                        intelligence_decision = "disabled"
                        decision_reason = "Intelligence completely disabled in settings"
                    
                    # NEW FEATURE 2: Apply intelligence with threshold checking
                    else:
                        server_logger.info("Intelligence ENABLED - applying with threshold checking")
                        
                        # Convert analysis candidates to intelligence format
                        candidates = analysis.get_sorted_candidates()
                        if candidates:
                            # Apply intelligence to get modified candidates
                            intelligent_candidates = self._apply_intelligence_to_candidates(
                                candidates, game_state
                            )
                            
                            if intelligent_candidates:
                                # Get intelligence evaluation
                                intelligent_move = intelligent_candidates[0].move
                                intelligent_eval = intelligent_candidates[0].score_pawns
                                
                                # NEW FEATURE 2: Compare with threshold
                                should_use_intelligence = self.intelligence_engine.compare_intelligence_with_threshold(
                                    original_engine_eval, intelligent_eval
                                )
                                
                                if should_use_intelligence:
                                    # Apply probabilistic selection
                                    probabilistic_move = self.intelligence_engine.select_move_with_probability(
                                        intelligent_candidates, self.settings_manager
                                    )
                                    
                                    if probabilistic_move:
                                        final_move = probabilistic_move
                                        intelligence_decision = "used"
                                        decision_reason = f"Intelligence move: {final_move}, eval: {intelligent_eval:.2f}"
                                        server_logger.info(f"Intelligence USED: {original_engine_move} -> {final_move}")
                                    else:
                                        final_move = bestmove
                                        intelligence_decision = "failed"
                                        decision_reason = "Probabilistic selection failed"
                                else:
                                    # Threshold check failed - use engine move
                                    final_move = bestmove
                                    intelligence_decision = "avoided"
                                    decision_reason = f"Intelligence eval {intelligent_eval:.2f} <= threshold {self.intelligence_engine.get_low_intelligence_threshold():.2f}"
                                    server_logger.info(f"Intelligence AVOIDED: threshold check failed")
                            else:
                                final_move = bestmove
                                intelligence_decision = "failed"
                                decision_reason = "Intelligence processing failed"
                        else:
                            final_move = bestmove
                            intelligence_decision = "failed"
                            decision_reason = "No candidates available for intelligence"
                
                except Exception as e:
                    server_logger.error(f"Intelligence processing failed: {e}")
                    final_move = bestmove
                    intelligence_decision = "failed"
                    decision_reason = f"Exception: {str(e)}"
            
            # Track the intelligence decision in game state
            if hasattr(game_state, 'intelligence_game_state'):
                game_state.intelligence_game_state.track_intelligence_decision(intelligence_decision)
            
            # Log the final decision
            server_logger.info(f"FINAL MOVE DECISION: {intelligence_decision}")
            server_logger.info(f"Original engine move: {original_engine_move}")
            server_logger.info(f"Final selected move: {final_move}")
            server_logger.info(f"Decision reason: {decision_reason}")
            
            # Visual update (with intelligence-aware move highlighting + NEW threat arrows)
            if analysis.has_analysis() or game_state.move_analysis_pending:
                visual_cmd = self._generate_combined_visual_update(analysis, game_state, final_move, intelligence_decision)
                if visual_cmd:
                    commands.append(visual_cmd)
                    server_logger.info("Generated combined visual update command with threat arrows")
                
                # Clear post-move analysis after including it
                if game_state.move_analysis_pending:
                    game_state.clear_move_analysis()
                
                # Evaluation bar update
                if analysis.has_analysis():
                    eval_cmd = self._generate_evaluation_update(analysis)
                    if eval_cmd:
                        commands.append(eval_cmd)
            
            # Depth progress update
            depth_cmd = self._generate_depth_update(analysis)
            if depth_cmd:
                commands.append(depth_cmd)
            
            # Move command (using final selected move)
            if final_move:
                move_cmd = self._generate_move_command(final_move, game_state, move_executor)
                if move_cmd:
                    commands.append(move_cmd)
                    server_logger.info(f"Generated move command: {final_move}")
                
                # Complete analysis (depth 100%)
                commands.append("depth_update 100")
            
            server_logger.info(f"Generated {len(commands)} total extension commands")
            return commands
            
        except Exception as e:
            server_logger.error(f"Command generation failed: {e}")
            return []
    
    def _apply_intelligence_to_candidates(self, candidates: List[MoveCandidate], 
                                        game_state: GameStateManager) -> List[MoveCandidate]:
        """Apply intelligence modifications to candidates and re-sort"""
        if not self.intelligence_manager:
            return candidates
        
        # Use the enhanced intelligence manager to apply modifications
        try:
            modified_candidates = self.intelligence_manager.apply_intelligence_modifications(
                candidates, game_state.intelligence_game_state
            )
            return modified_candidates
        except Exception as e:
            server_logger.error(f"Intelligence modification failed: {e}")
            return candidates
    
    def _generate_combined_visual_update(self, analysis: AnalysisProcessor, game_state: GameStateManager, 
                                       selected_move: Optional[str] = None, intelligence_decision: str = "disabled") -> Optional[str]:
        """Generate combined visual update highlighting selected move with intelligence indicators and NEW threat arrows"""
        try:
            visual_data = {
                "arrows": [],
                "highlights": [],
                "effects": []
            }
            
            # Include post-move analysis badge if still valid
            if game_state.should_show_move_analysis():
                analysis_result = game_state.get_move_analysis_quality()
                if analysis_result:
                    quality_label, color = analysis_result
                    move = game_state.last_move_played
                    
                    if move and len(move) >= 4:
                        to_square = move[2:4]
                        visual_data["effects"].append({
                            "square": to_square,
                            "type": quality_label,
                            "color": color
                        })
            
            # NEW: Add threat arrows if enabled
            if self.settings_manager.get_setting("show-threat-arrows", False):
                try:
                    # Get threat limit settings
                    max_player_threats = self.settings_manager.get_setting("max-player-threats", 5)
                    max_opponent_threats = self.settings_manager.get_setting("max-opponent-threats", 3)
                    
                    # Detect threats with custom limits
                    threat_data = ThreatDetector.detect_all_threats(
                        game_state.current_board, 
                        max_player_threats=max_player_threats,
                        max_opponent_threats=max_opponent_threats
                    )
                    
                    # Add player threats (green arrows)
                    for threat in threat_data['player_threats']:
                        # Skip very bad moves (evaluation less than -200 centipawns)
                        if selected_move and threat['from'] + threat['to'] == selected_move:
                            candidate_eval = self._get_move_evaluation(analysis, selected_move)
                            if candidate_eval is not None and candidate_eval < -2.0:  # Very bad move
                                continue
                        
                        visual_data["arrows"].append({
                            "from": threat['from'],
                            "to": threat['to'],
                            "color": "#00ff00",  # Green for player threats
                            "opacity": 0.2
                        })
                    
                    # Add opponent threats (red arrows)
                    for threat in threat_data['opponent_threats']:
                        visual_data["arrows"].append({
                            "from": threat['from'],
                            "to": threat['to'],
                            "color": "#ff0000",  # Red for opponent threats
                            "opacity": 0.2
                        })
                    
                    server_logger.debug(f"Added {len(threat_data['player_threats'])} player threats and {len(threat_data['opponent_threats'])} opponent threats")
                    
                except Exception as e:
                    server_logger.warning(f"Failed to generate threat arrows: {e}")
            
            # Include analysis arrows with intelligence highlighting
            if analysis.has_analysis():
                candidates = analysis.get_sorted_candidates()
                if candidates and self.settings_manager.get_setting("show-hints", True):
                    
                    colors = [
                        {"color": "#0080ff", "opacity": 0.8},  # Blue - Best
                        {"color": "#00ff00", "opacity": 0.7},  # Green - Good
                        {"color": "#81c678", "opacity": 0.6},  # Orange - Alternative
                        {"color": "#ffff00", "opacity": 0.5},  # Yellow - Fourth
                        {"color": "#ff6600", "opacity": 0.4}   # Red - Fifth
                    ]
                    
                    multipv = self.settings_manager.get_setting("multipv", 3)
                    num_arrows = min(len(candidates), multipv, len(colors))
                    
                    for i in range(num_arrows):
                        candidate = candidates[i]
                        color_info = colors[i]
                        
                        # NEW: Highlight moves differently based on intelligence decision
                        if selected_move and candidate.move == selected_move:
                            if intelligence_decision == "used":
                                # Intelligence was used - magenta highlighting
                                color_info = {"color": "#ff00ff", "opacity": 1.0}
                                server_logger.debug(f"Highlighting intelligence-used move: {candidate.move}")
                            elif intelligence_decision == "avoided":
                                # Intelligence was avoided - orange highlighting
                                color_info = {"color": "#3f00ff", "opacity": 1.0}
                                server_logger.debug(f"Highlighting intelligence-avoided move: {candidate.move}")
                            elif intelligence_decision == "disabled":
                                # Intelligence disabled - standard blue highlighting
                                color_info = {"color": "#0080ff", "opacity": 1.0}
                                server_logger.debug(f"Highlighting engine move (intelligence disabled): {candidate.move}")
                        
                        visual_data["arrows"].append({
                            "from": candidate.from_square,
                            "to": candidate.to_square,
                            "color": color_info["color"],
                            "opacity": color_info["opacity"]
                        })
            
            # Generate command if we have visual elements
            if visual_data["arrows"] or visual_data["effects"] or visual_data["highlights"]:
                command = f"visual_update {json.dumps(visual_data, separators=(',', ':'))}"
                return command
            
            return None
            
        except Exception as e:
            server_logger.error(f"Combined visual update generation failed: {e}")
            return None
    
    def _get_move_evaluation(self, analysis: AnalysisProcessor, move: str) -> Optional[float]:
        """Get evaluation for a specific move from analysis"""
        try:
            for candidate in analysis.candidates:
                if candidate.move == move:
                    return candidate.score_pawns
        except:
            pass
        return None
    
    def _generate_evaluation_update(self, analysis: AnalysisProcessor) -> Optional[str]:
        """Generate evaluation bar update"""
        try:
            if not self.settings_manager.get_setting("evaluation-bar", True):
                return None
            
            if analysis.mate_score is not None:
                return f"evaluation_update {analysis.mate_score} true"
            else:
                return f"evaluation_update {analysis.evaluation:.2f} false"
                
        except Exception as e:
            server_logger.error(f"Evaluation update generation failed: {e}")
            return None
    
    def _generate_depth_update(self, analysis: AnalysisProcessor) -> Optional[str]:
        """Generate depth progress update"""
        try:
            if not self.settings_manager.get_setting("depth-bar", True):
                return None
            
            target_depth = self.settings_manager.get_setting("depth", 15)
            progress = min((analysis.depth_reached / target_depth) * 100, 100) if target_depth > 0 else 0
            
            return f"depth_update {progress:.1f}"
            
        except Exception as e:
            server_logger.error(f"Depth update generation failed: {e}")
            return None
    
    def _generate_move_command(self, move: str, game_state: GameStateManager, 
                              move_executor: MoveExecutor) -> Optional[str]:
        """Generate move command with timing"""
        try:
            # Check if auto-move is enabled
            if not move_executor.should_auto_execute():
                server_logger.debug(f"Auto-move disabled, skipping move command for: {move}")
                return None
            
            # Validate move is legal
            if not game_state.is_move_legal(move):
                server_logger.warning(f"Cannot generate command for illegal move: {move}")
                return None
            
            # Calculate timing
            delay_ms, timing_type = move_executor.calculate_delay(game_state)
            
            # Generate command
            if delay_ms > 0:
                return f"move_command {move} delay_ms {delay_ms}"
            else:
                return f"move_command {move}"
                
        except Exception as e:
            server_logger.error(f"Move command generation failed: {e}")
            return None


class BetterMintServer:
    """Main BetterMint server with NEW intelligence controls and threat arrows"""
    
    def __init__(self, engines: List[EngineChess], engine_configs: List[Dict], 
                 settings_manager: SettingsManager, connection_update_callback=None, 
                 log_callback=None):
        
        self.engines = engines
        self.engine_configs = engine_configs
        self.settings_manager = settings_manager
        self.connection_update_callback = connection_update_callback
        self.log_callback = log_callback
        
        # Core components
        self.game_state = GameStateManager()
        self.analysis = AnalysisProcessor()
        self.move_executor = MoveExecutor(settings_manager)
        
        # INTELLIGENCE: Create and configure intelligence manager with NEW controls
        self.intelligence_manager = EnhancedIntelligentEngineManager(
            engines, settings_manager.get_intelligence_settings()
        )
        self.intelligence_manager.set_settings_manager(settings_manager)
        
        # Command generator with NEW intelligence integration
        self.command_generator = CommandGenerator(settings_manager, self.intelligence_manager)
        
        # Connection management
        self.active_connections: Set[WebSocket] = set()
        self.connections: Dict[str, ConnectionInfo] = {}
        self.connection_counter = 0
        
        # Analysis state
        self.analysis_lock = asyncio.Lock()
        self.current_analysis_id = 0
        
        # Create FastAPI app
        self.app = self._create_app()
        
        # Setup templates
        template_dir = Path(__file__).parent / "templates"
        if template_dir.exists():
            self.templates = Jinja2Templates(directory=str(template_dir))
        else:
            self.templates = None
        
        # Initialize engines with mate finder
        self._initialize_engines()
        
        server_logger.info(f"BetterMint server initialized with {len(engines)} engines, NEW intelligence controls, and threat arrows")
        server_logger.info(f"Intelligence enabled: {settings_manager.get_intelligence_settings().intelligence_enabled}")
        server_logger.info(f"Avoid low intelligence: {settings_manager.get_intelligence_settings().avoid_low_intelligence}")
        server_logger.info(f"Show threat arrows: {settings_manager.get_setting('show-threat-arrows', False)}")
    
    def _initialize_engines(self):
        """Initialize all chess engines with mate finder support"""
        for engine in self.engines:
            try:
                if hasattr(engine, 'initialize_engine'):
                    engine.initialize_engine()
                else:
                    # Fallback initialization
                    engine.put("uci")
                    engine.put("isready")
                
                # MATE FINDER: Connect mate-finder-value setting
                mate_finder_value = self.settings_manager.get_setting("mate-finder-value", 5)
                if mate_finder_value > 0:
                    # Try common mate finder option names
                    mate_options = ["MateSearch", "MateFinder", "MateDepth", "SearchForMate"]
                    for option in mate_options:
                        engine.put(f"setoption name {option} value {mate_finder_value}")
                    server_logger.info(f"Set mate finder value: {mate_finder_value}")
                
                # INTELLIGENCE: Update engine intelligence settings with NEW controls
                engine.intelligence_settings = self.settings_manager.get_intelligence_settings()
                
                server_logger.info(f"Engine initialized: Maia={engine.is_maia}, Intelligence={engine.intelligence_settings.intelligence_enabled}")
            except Exception as e:
                server_logger.error(f"Engine initialization failed: {e}")
    
    def update_intelligence_settings(self):
        """Update intelligence settings across all components with NEW controls"""
        try:
            intel_settings = self.settings_manager.get_intelligence_settings()
            
            # Update intelligence manager
            self.intelligence_manager.update_intelligence_settings(intel_settings)
            
            # Update all engines
            for engine in self.engines:
                engine.intelligence_settings = intel_settings
            
            server_logger.info(f"Intelligence settings updated:")
            server_logger.info(f"  Intelligence enabled: {intel_settings.intelligence_enabled}")
            server_logger.info(f"  Avoid low intelligence: {intel_settings.avoid_low_intelligence}")
            server_logger.info(f"  Low intelligence threshold: {intel_settings.low_intelligence_threshold}")
            
        except Exception as e:
            server_logger.error(f"Failed to update intelligence settings: {e}")
    
    def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application"""
        app = FastAPI(
            title="BetterMint Modded Server",
            version=APP_VERSION,
            description="Chess analysis server with NEW intelligence control features and threat arrows"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes(app)
        
        return app
    
    def _register_routes(self, app: FastAPI):
        """Register all API routes"""
        
        @app.get("/", response_class=HTMLResponse)
        async def get_home(request: Request):
            """Serve main interface"""
            intel_settings = self.settings_manager.get_intelligence_settings()
            if self.templates:
                return self.templates.TemplateResponse("index.html", {
                    "request": request,
                    "version": APP_VERSION,
                    "engines": len(self.engines),
                    "connections": len(self.active_connections),
                    "intelligence_enabled": intel_settings.intelligence_enabled,
                    "avoid_low_intelligence": intel_settings.avoid_low_intelligence,
                    "threshold": intel_settings.low_intelligence_threshold,
                    "threat_arrows": self.settings_manager.get_setting("show-threat-arrows", False)
                })
            else:
                return HTMLResponse(f"""
                    <html><body>
                        <h1>BetterMint Server v{APP_VERSION}</h1>
                        <p>Engines: {len(self.engines)}</p>
                        <p>Connections: {len(self.active_connections)}</p>
                        <p>Intelligence Enabled: {intel_settings.intelligence_enabled}</p>
                        <p>Avoid Low Intelligence: {intel_settings.avoid_low_intelligence}</p>
                        <p>Threshold: {intel_settings.low_intelligence_threshold}</p>
                        <p>Threat Arrows: {self.settings_manager.get_setting("show-threat-arrows", False)}</p>
                        <p>WebSocket: ws://localhost:{DEFAULT_PORT}/ws</p>
                    </body></html>
                """)
        
        @app.post("/api/game_state")
        async def report_game_state(request: Request):
            """Handle game state reports from extension"""
            try:
                data = await request.json()
                fen = data.get('fen')
                move_count = data.get('moveCount', 0)
                
                if not fen:
                    raise HTTPException(status_code=400, detail="Missing FEN")
                
                # Update game state
                if self.game_state.update_position(fen):
                    # Check if we should reset execution state for new game
                    if move_count <= 1:
                        self.move_executor.reset()
                        self.analysis.reset()
                    
                    # Trigger analysis for non-starting positions
                    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
                    if fen != starting_fen and move_count > 0:
                        asyncio.create_task(self._trigger_analysis(fen))
                    
                    return {"status": "success"}
                else:
                    raise HTTPException(status_code=400, detail="Invalid FEN")
                
            except HTTPException:
                raise
            except Exception as e:
                server_logger.error(f"Game state error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/settings")
        async def update_settings(settings: Settings):
            """Update settings with NEW intelligence controls"""
            try:
                self.settings_manager.update_settings(settings.settings)
                # Update intelligence settings across components with NEW controls
                self.update_intelligence_settings()
                return {"status": "success"}
            except Exception as e:
                server_logger.error(f"Settings update error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/settings")
        async def get_settings():
            """Get current settings"""
            return self.settings_manager.get_all_settings()
        
        @app.get("/api/intelligence_stats")
        async def get_intelligence_statistics():
            """Get NEW intelligence usage statistics"""
            try:
                stats = self.intelligence_manager.get_intelligence_statistics()
                return stats
            except Exception as e:
                server_logger.error(f"Intelligence stats error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint with NEW intelligence status and threat arrows"""
            intel_settings = self.settings_manager.get_intelligence_settings()
            return {
                "status": "healthy",
                "version": APP_VERSION,
                "engines": len(self.engines),
                "connections": len(self.active_connections),
                "intelligence_enabled": intel_settings.intelligence_enabled,
                "avoid_low_intelligence": intel_settings.avoid_low_intelligence,
                "low_intelligence_threshold": intel_settings.low_intelligence_threshold,
                "threat_arrows_enabled": self.settings_manager.get_setting("show-threat-arrows", False),
                "game_state": {
                    "fen": self.game_state.current_fen,
                    "move_number": self.game_state.move_number,
                    "phase": self.game_state.game_phase,
                    "pieces": self.game_state.piece_count
                }
            }
        
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication"""
            await self._handle_websocket(websocket)
    
    async def _handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connections"""
        # Create connection info
        self.connection_counter += 1
        client_id = f"client_{self.connection_counter}"
        conn_info = ConnectionInfo(client_id, websocket)
        self.connections[client_id] = conn_info
        self.active_connections.add(websocket)
        
        await websocket.accept()
        server_logger.info(f"WebSocket connected: {client_id}")
        self._notify_connection_update()
        
        try:
            # Start message handling tasks
            client_task = asyncio.create_task(self._handle_client_messages(websocket, conn_info))
            engine_task = asyncio.create_task(self._handle_engine_responses(websocket))
            
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [client_task, engine_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
        except WebSocketDisconnect:
            server_logger.info(f"WebSocket disconnected: {client_id}")
        except Exception as e:
            server_logger.error(f"WebSocket error: {e}")
        finally:
            # Cleanup
            self.active_connections.discard(websocket)
            if client_id in self.connections:
                del self.connections[client_id]
            self._notify_connection_update()
            
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.close()
            except:
                pass
    
    async def _handle_client_messages(self, websocket: WebSocket, conn_info: ConnectionInfo):
        """Handle messages from client"""
        while websocket.client_state == WebSocketState.CONNECTED:
            try:
                data = await websocket.receive_text()
                conn_info.update_activity()
                
                # Forward UCI commands to engines
                if data.strip():
                    server_logger.debug(f"Client command: {data}")
                    for engine in self.engines:
                        engine.put(data.strip())
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                server_logger.error(f"Client message error: {e}")
                break
    
    async def _handle_engine_responses(self, websocket: WebSocket):
        """Handle engine responses and generate commands with NEW intelligence controls and threat arrows"""
        while websocket.client_state == WebSocketState.CONNECTED:
            try:
                # Collect engine responses
                all_responses = []
                for engine in self.engines:
                    try:
                        lines = await asyncio.to_thread(engine.read_available_lines)
                        all_responses.extend(lines)
                    except Exception as e:
                        server_logger.warning(f"Engine read error: {e}")
                        continue
                
                if all_responses:
                    # Process responses and generate commands with NEW intelligence controls and threat arrows
                    commands = await self._process_engine_responses(all_responses)
                    
                    # Send commands to client
                    for command in commands:
                        if websocket.client_state == WebSocketState.CONNECTED:
                            await websocket.send_text(command)
                            server_logger.debug(f"Sent command: {command}")
                else:
                    # No responses, wait briefly
                    await asyncio.sleep(0.05)
                
            except Exception as e:
                server_logger.error(f"Engine response error: {e}")
                break
    
    async def _process_engine_responses(self, responses: List[str]) -> List[str]:
        """Process engine responses and generate extension commands with NEW intelligence controls and threat arrows"""
        if not responses:
            return []
        
        async with self.analysis_lock:
            # Process all responses
            bestmove = None
            analysis_updated = False
            
            for response in responses:
                response = response.strip()
                if not response:
                    continue
                
                server_logger.debug(f"Processing: {response}")
                
                if response.startswith("info"):
                    if self.analysis.process_info_line(response, self.game_state):
                        analysis_updated = True
                elif response.startswith("bestmove"):
                    bestmove = self.analysis.process_bestmove(response, self.game_state)
            
            # Generate commands with NEW intelligence controls and threat arrows
            if analysis_updated or bestmove:
                commands = self.command_generator.generate_all_commands(
                    self.analysis, self.game_state, self.move_executor, bestmove
                )
                
                # Reset analysis if bestmove received (analysis complete)
                if bestmove:
                    self.analysis.reset()
                
                return commands
            
            return []
    
    async def _trigger_analysis(self, fen: str):
        """Trigger engine analysis for position"""
        try:
            async with self.analysis_lock:
                self.current_analysis_id += 1
                analysis_id = self.current_analysis_id
                
                server_logger.info(f"Starting analysis #{analysis_id} for: {fen[:20]}...")
                
                # Reset analysis state
                self.analysis.reset()
                
                # Send position to engines
                position_cmd = f"position fen {fen}"
                for engine in self.engines:
                    engine.put(position_cmd)
                
                # Configure and start analysis
                depth = self.settings_manager.get_setting("depth", 15)
                multipv = self.settings_manager.get_setting("multipv", 3)
                
                # Set MultiPV for engines that support it
                for engine in self.engines:
                    if not engine.is_maia:  # Skip for Maia
                        engine.put(f"setoption name MultiPV value {multipv}")
                
                # Start analysis
                go_cmd = f"go depth {depth}"
                for engine in self.engines:
                    if engine.is_maia:
                        # Maia-specific go command
                        engine.put("go nodes 100")
                    else:
                        engine.put(go_cmd)
                
                server_logger.info(f"Analysis #{analysis_id} started: depth={depth}, multipv={multipv}")
                
        except Exception as e:
            server_logger.error(f"Analysis trigger failed: {e}")
    
    def _notify_connection_update(self):
        """Notify GUI about connection changes"""
        if self.connection_update_callback:
            conn_list = [conn.to_dict() for conn in self.connections.values()]
            self.connection_update_callback(conn_list)
    
    def get_app(self) -> FastAPI:
        """Get FastAPI application"""
        return self.app


def create_server(engines: List[EngineChess], engine_configs: List[Dict],
                 settings_manager: SettingsManager, connection_update_callback=None,
                 log_callback=None) -> BetterMintServer:
    """Create BetterMint server instance with NEW intelligence controls and threat arrows"""
    server_logger.info("Creating BetterMint server with NEW features:")
    server_logger.info("  - Disable Intelligence: Completely bypasses intelligence when disabled")
    server_logger.info("  - Avoid Low Intelligence: Compares evaluations with threshold")
    server_logger.info("  - Threat Arrows: Shows green arrows for player threats, red for opponent threats")
    
    return BetterMintServer(
        engines=engines,
        engine_configs=engine_configs,
        settings_manager=settings_manager,
        connection_update_callback=connection_update_callback,
        log_callback=log_callback
    )