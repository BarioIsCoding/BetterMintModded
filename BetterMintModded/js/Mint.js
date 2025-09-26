"use strict";

// BetterMint Modded (MINT Beta 2c 26092025 Features) - PURE SERVER-CONTROLLED CLIENT
// Extension acts as presentation layer only - all decisions made server-side

var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};

// Server communication - reports game state and receives commands
var ServerRequest = (function () {
    var requestId = 0;
    var serverUrl = 'http://localhost:8000'; // Default

    // Load custom server URL from extension storage if available
    if (typeof chrome !== 'undefined' && chrome.storage) {
        chrome.storage.local.get(['serverUrl'], function (result) {
            if (result.serverUrl) {
                serverUrl = result.serverUrl.replace(/\/$/, ''); // Remove trailing slash
                console.log('BetterMint: Using stored server URL:', serverUrl);
            }
        });

        // Listen for URL changes
        chrome.storage.onChanged.addListener(function (changes, namespace) {
            if (namespace === 'local' && changes.serverUrl) {
                serverUrl = changes.serverUrl.newValue.replace(/\/$/, '');
                console.log('BetterMint: Server URL updated to:', serverUrl);
            }
        });
    }

    function makeRequest(endpoint, options = {}) {
        return fetch(`${serverUrl}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .catch(error => {
                console.warn(`BetterMint: Server request failed for ${endpoint}:`, error);
                throw error;
            });
    }

    function getData(data = null) {
        var id = requestId++;
        return new Promise(function (resolve, reject) {
            makeRequest('/api/settings')
                .then(serverSettings => {
                    resolve(serverSettings);
                })
                .catch(error => {
                    console.log('BetterMint: Using default settings, server unavailable');
                    var listener = function (evt) {
                        if (evt.detail.requestId == id) {
                            window.removeEventListener("BetterMintSendOptions", listener);
                            resolve(evt.detail.data);
                        }
                    };
                    window.addEventListener("BetterMintSendOptions", listener);
                    var payload = { data: data, id: id };
                    window.dispatchEvent(new CustomEvent("BetterMintGetOptions", { detail: payload }));
                });
        });
    }

    function updateSettings(settings) {
        return makeRequest('/api/settings', {
            method: 'POST',
            body: JSON.stringify(settings)
        }).catch(error => {
            console.warn('BetterMint: Failed to save settings to server:', error);
        });
    }

    function reportGameState(gameData) {
        return makeRequest('/api/game_state', {
            method: 'POST',
            body: JSON.stringify(gameData)
        }).catch(error => {
            console.warn('BetterMint: Failed to report game state:', error);
        });
    }

    function reportMove(moveData) {
        return makeRequest('/api/move_made', {
            method: 'POST',
            body: JSON.stringify(moveData)
        }).catch(error => {
            console.warn('BetterMint: Failed to report move:', error);
        });
    }

    return { getData, updateSettings, makeRequest, reportGameState, reportMove };
})();

// Enhanced gradient color calculation - preserved for visual feedback
function getGradientColor(start_color, end_color, percent) {
    start_color = start_color.replace(/^\s*#|\s*$/g, "");
    end_color = end_color.replace(/^\s*#|\s*$/g, "");

    if (start_color.length == 3) {
        start_color = start_color.replace(/(.)/g, "$1$1");
    }
    if (end_color.length == 3) {
        end_color = end_color.replace(/(.)/g, "$1$1");
    }

    var start_red = parseInt(start_color.substr(0, 2), 16),
        start_green = parseInt(start_color.substr(2, 2), 16),
        start_blue = parseInt(start_color.substr(4, 2), 16);

    var end_red = parseInt(end_color.substr(0, 2), 16),
        end_green = parseInt(end_color.substr(2, 2), 16),
        end_blue = parseInt(end_color.substr(4, 2), 16);

    var diff_red = end_red - start_red;
    var diff_green = end_green - start_green;
    var diff_blue = end_blue - start_blue;

    diff_red = (diff_red * percent + start_red).toString(16).split(".")[0];
    diff_green = (diff_green * percent + start_green).toString(16).split(".")[0];
    diff_blue = (diff_blue * percent + start_blue).toString(16).split(".")[0];

    if (diff_red.length == 1) diff_red = "0" + diff_red;
    if (diff_green.length == 1) diff_green = "0" + diff_green;
    if (diff_blue.length == 1) diff_blue = "0" + diff_blue;

    return "#" + diff_red + diff_green + diff_blue;
}

// Console logging for debugging
function logMessage(message, type = 'info') {
    console.log(`[BetterMint ${type.toUpperCase()}] ${message}`);
}

// Settings enumeration - preserved for visual features
var enumOptions = {
    UrlApiStockfish: "url-api-stockfish",
    ApiStockfish: "api-stockfish",
    ShowHints: "show-hints",
    MoveAnalysis: "move-analysis",
    DepthBar: "depth-bar",
    EvaluationBar: "evaluation-bar",
};

var BetterMintmaster;
var Config = undefined;
var context = undefined;
var eTable = null;

var tempOptions = {};
ServerRequest.getData().then(function (options) {
    tempOptions = options;
});

function getValueConfig(key) {
    if (BetterMintmaster == undefined) return tempOptions[key];
    return BetterMintmaster.options[key];
}

// Visual data structure - preserved for server-sent display commands
class VisualMove {
    constructor(from, to, promotion = null, evaluation = null, depth = null, quality = 'unknown') {
        this.from = from;
        this.to = to;
        this.promotion = promotion;
        this.move = from + to + (promotion || '');
        this.evaluation = evaluation;
        this.depth = depth;
        this.quality = quality;
    }
}

// GameController - handles visual feedback and server command execution
class GameController {
    constructor(BetterMintmaster, chessboard) {
        this.BetterMintmaster = BetterMintmaster;
        this.chessboard = chessboard;
        this.controller = chessboard.game;
        this.options = this.controller.getOptions();
        this.depthBar = null;
        this.evalBar = null;
        this.evalBarFill = null;
        this.evalScore = null;
        this.evalScoreAbbreviated = null;
        this.currentMarkings = [];
        this.gameStats = {
            movesPlayed: 0,
            gameStartTime: Date.now()
        };

        let self = this;

        this.controller.on("Move", (event) => {
            console.log("Move detected:", event.data);
            this.gameStats.movesPlayed++;
            this.reportPositionToServer();

            // Report the move to server
            ServerRequest.reportMove({
                move: event.data,
                fen: this.controller.getFEN(),
                moveNumber: this.gameStats.movesPlayed,
                playerTurn: this.controller.getTurn()
            });
        });

        // Create visual elements if enabled
        if (this.evalBar == null && getValueConfig(enumOptions.EvaluationBar)) {
            this.CreateAnalysisTools();
        }

        this.controller.on('ModeChanged', (event) => {
            if (event.data === "playing") {
                this.ResetGame();
                this.RefreshEvalutionBar();
                // Notify server of new game
                if (BetterMintmaster.serverController && BetterMintmaster.serverController.isWebSocketOpen()) {
                    BetterMintmaster.serverController.send("game_start");
                }
                logMessage("New game started - server notified", 'success');
            }
        });

        let checkEventOne = false;
        this.controller.on("RendererSet", (event) => {
            this.ResetGame();
            this.RefreshEvalutionBar();
            checkEventOne = true;
        });

        setTimeout(() => {
            if (!checkEventOne) {
                this.controller.on("ResetGame", (event) => {
                    this.ResetGame();
                    this.RefreshEvalutionBar();
                });
            }
        }, 1100);

        this.controller.on("UpdateOptions", (event) => {
            this.options = this.controller.getOptions();
            if (event.data.flipped != undefined && this.evalBar != null) {
                if (event.data.flipped)
                    this.evalBar.classList.add("evaluation-bar-flipped");
                else this.evalBar.classList.remove("evaluation-bar-flipped");
            }
        });
    }

    UpdateExtensionOptions() {
        if (getValueConfig(enumOptions.EvaluationBar) && this.evalBar == null)
            this.CreateAnalysisTools();
        else if (!getValueConfig(enumOptions.EvaluationBar) && this.evalBar != null) {
            this.evalBar.remove();
            this.evalBar = null;
        }

        if (getValueConfig(enumOptions.DepthBar) && this.depthBar == null)
            this.CreateAnalysisTools();
        else if (!getValueConfig(enumOptions.DepthBar) && this.depthBar != null) {
            this.depthBar.parentElement.remove();
            this.depthBar = null;
        }

        if (!getValueConfig(enumOptions.ShowHints)) {
            this.RemoveCurrentMarkings();
        }

        if (!getValueConfig(enumOptions.MoveAnalysis)) {
            let lastMove = this.controller.getLastMove();
            if (lastMove) {
                this.controller.markings.removeOne(`effect|${lastMove.to}`);
            }
        }
    }

    CreateAnalysisTools() {
        let interval1 = setInterval(() => {
            let layoutChessboard = this.chessboard.parentElement;
            if (layoutChessboard == null) return;
            let layoutMain = layoutChessboard.parentElement;
            if (layoutMain == null) return;

            clearInterval(interval1);

            if (getValueConfig(enumOptions.DepthBar) && this.depthBar == null) {
                let depthBar = document.createElement("div");
                depthBar.classList.add("depthBarLayoutt");
                depthBar.innerHTML = `<div class="depthBarr"><span class="depthBarProgress"></span></div>`;
                layoutMain.insertBefore(depthBar, layoutChessboard.nextSibling);
                this.depthBar = depthBar.querySelector(".depthBarProgress");
            }

            if (getValueConfig(enumOptions.EvaluationBar) && this.evalBar == null) {
                let evalBar = document.createElement("div");
                evalBar.style.flex = "1 1 auto;";
                evalBar.innerHTML = `
                    <div class="evaluation-bar-bar">
                        <span class="evaluation-bar-scoreAbbreviated evaluation-bar-dark">0.0</span>
                        <span class="evaluation-bar-score evaluation-bar-dark ">+0.00</span>
                        <div class="evaluation-bar-fill">
                        <div class="evaluation-bar-color evaluation-bar-black"></div>
                        <div class="evaluation-bar-color evaluation-bar-draw"></div>
                        <div class="evaluation-bar-color evaluation-bar-white" style="transform: translate3d(0px, 50%, 0px);"></div>
                        </div>
                    </div>`;
                let layoutEvaluation = layoutChessboard.querySelector("#board-layout-evaluation");
                if (layoutEvaluation == null) {
                    layoutEvaluation = document.createElement("div");
                    layoutEvaluation.classList.add("board-layout-evaluation");
                    layoutChessboard.insertBefore(layoutEvaluation, layoutChessboard.firstElementChild);
                }
                layoutEvaluation.innerHTML = "";
                layoutEvaluation.appendChild(evalBar);
                this.evalBar = layoutEvaluation.querySelector(".evaluation-bar-bar");
                this.evalBarFill = layoutEvaluation.querySelector(".evaluation-bar-white");
                this.evalScore = layoutEvaluation.querySelector(".evaluation-bar-score");
                this.evalScoreAbbreviated = layoutEvaluation.querySelector(".evaluation-bar-scoreAbbreviated");

                if (!this.options.isWhiteOnBottom && this.options.flipped)
                    this.evalBar.classList.add("evaluation-bar-flipped");
            }
        }, 10);
    }

    RefreshEvalutionBar() {
        if (getValueConfig(enumOptions.EvaluationBar)) {
            if (this.evalBar == null) {
                this.CreateAnalysisTools();
            } else if (this.evalBar != null) {
                this.evalBar.remove();
                this.evalBar = null;
                this.CreateAnalysisTools();
            }
        }
    }

    reportPositionToServer() {
        let FENs = this.controller.getFEN();

        ServerRequest.reportGameState({
            fen: FENs,
            turn: this.controller.getTurn(),
            moveCount: this.gameStats.movesPlayed,
            gameMode: this.controller.getOptions().gameMode,
            isPlayerWhite: !this.options.isPlayerBlack,
            timestamp: Date.now()
        });

        console.log("Position reported to server:", FENs);
    }

    ResetGame() {
        this.reportPositionToServer();
        this.gameStats = { movesPlayed: 0, gameStartTime: Date.now() };
        BetterMintmaster.game.RefreshEvalutionBar();
        this.RemoveCurrentMarkings();

        ServerRequest.reportGameState({
            fen: this.controller.getFEN(),
            turn: 1,
            moveCount: 0,
            gameMode: 'new_game',
            isPlayerWhite: !this.options.isPlayerBlack,
            timestamp: Date.now()
        });
    }

    RemoveCurrentMarkings() {
        this.currentMarkings.forEach((marking) => {
            let key = marking.type + "|";
            if (marking.data.square != null) key += marking.data.square;
            else key += `${marking.data.from}${marking.data.to}`;
            this.controller.markings.removeOne(key);
        });
        this.currentMarkings = [];
    }

    // Server-commanded visual feedback - displays arrows and highlights
    displayServerVisuals(visualData) {
        console.log("Displaying server visuals:", visualData);

        if (getValueConfig(enumOptions.ShowHints)) {
            this.RemoveCurrentMarkings();

            // Display arrows from server
            if (visualData.arrows) {
                visualData.arrows.forEach((arrow) => {
                    console.log(`Adding server arrow: ${arrow.from} -> ${arrow.to} (${arrow.color})`);
                    this.currentMarkings.push({
                        data: {
                            from: arrow.from,
                            to: arrow.to,
                            color: arrow.color || this.options.arrowColors.alt,
                            opacity: arrow.opacity || 0.8
                        },
                        node: true,
                        persistent: true,
                        type: "arrow",
                    });
                });
            }

            // Display highlights from server
            if (visualData.highlights) {
                visualData.highlights.forEach((highlight) => {
                    console.log(`Adding server highlight: ${highlight.square} (${highlight.color})`);
                    this.currentMarkings.push({
                        data: {
                            square: highlight.square,
                            color: highlight.color,
                            opacity: highlight.opacity || 0.4
                        },
                        node: true,
                        persistent: true,
                        type: "highlight",
                    });
                });
            }

            // Display effects from server
            if (visualData.effects) {
                visualData.effects.forEach((effect) => {
                    console.log(`Adding server effect: ${effect.square} (${effect.type})`);
                    this.currentMarkings.push({
                        data: {
                            square: effect.square,
                            type: effect.type
                        },
                        node: true,
                        persistent: true,
                        type: "effect",
                    });
                });
            }

            this.currentMarkings.reverse();
            console.log("Adding server markings:", this.currentMarkings);
            this.controller.markings.addMany(this.currentMarkings);
        }
    }

    SetCurrentDepth(percentage) {
        if (this.depthBar == null) return;
        let style = this.depthBar.style;
        if (percentage <= 0) {
            this.depthBar.classList.add("disable-transition");
            style.width = `0%`;
            this.depthBar.classList.remove("disable-transition");
        } else {
            if (percentage > 100) percentage = 100;
            style.width = `${percentage}%`;
        }
    }

    SetEvaluation(score, isMate) {
        if (this.evalBar == null) return;
        var percentage, textNumber, textScoreAbb;

        if (!isMate) {
            let eval_max = 500;
            let eval_min = -500;
            let smallScore = score / 100;
            percentage = 90 - ((score - eval_min) / (eval_max - eval_min)) * (95 - 5) + 5;
            if (percentage < 5) percentage = 5;
            else if (percentage > 95) percentage = 95;
            textNumber = (score >= 0 ? "+" : "") + smallScore.toFixed(2);
            textScoreAbb = Math.abs(smallScore).toFixed(1);
        } else {
            percentage = score < 0 ? 100 : 0;
            textNumber = "M" + Math.abs(score).toString();
            textScoreAbb = textNumber;
        }

        this.evalBarFill.style.transform = `translate3d(0px, ${percentage}%, 0px)`;
        this.evalScore.innerText = textNumber;
        this.evalScoreAbbreviated.innerText = textScoreAbb;

        let classSideAdd = score >= 0 ? "evaluation-bar-dark" : "evaluation-bar-light";
        let classSideRemove = score >= 0 ? "evaluation-bar-light" : "evaluation-bar-dark";
        this.evalScore.classList.remove(classSideRemove);
        this.evalScoreAbbreviated.classList.remove(classSideRemove);
        this.evalScore.classList.add(classSideAdd);
        this.evalScoreAbbreviated.classList.add(classSideAdd);
    }

    getPlayingAs() {
        return this.options.isPlayerBlack ? 2 : 1;
    }

    // Execute server-commanded move with validation
    executeCommandedMove(moveData) {
        console.log("Executing server-commanded move:", moveData);

        // Validate move data
        if (!moveData.from || !moveData.to) {
            console.error("Invalid move data from server:", moveData);
            return false;
        }

        // Find legal move
        const legalMoves = this.controller.getLegalMoves();
        const move = legalMoves.find(m =>
            m.from === moveData.from && m.to === moveData.to
        );

        if (move) {
            move.userGenerated = true;
            if (moveData.promotion) {
                move.promotion = moveData.promotion;
            }

            // Execute the move
            this.controller.move(move);
            console.log("Move executed successfully:", moveData.from + moveData.to);
            logMessage(`Server move executed: ${moveData.from}${moveData.to}`, 'success');
            return true;
        } else {
            console.error("Invalid move command from server:", moveData);
            logMessage(`Invalid server move: ${moveData.from}${moveData.to}`, 'error');
            return false;
        }
    }
}

// ServerController - pure WebSocket communication with command processing
class ServerController {
    constructor(BetterMintmaster) {
        this.BetterMintmaster = BetterMintmaster;
        this.connectionRetries = 0;
        this.maxRetries = 5;
        this.reconnectDelay = 500;
        this.maxReconnectDelay = 3000;

        // Load WebSocket URL from storage, fallback to config
        if (typeof chrome !== 'undefined' && chrome.storage) {
            chrome.storage.local.get(['wsUrl'], (result) => {
                const wsUrl = result.wsUrl || getValueConfig(enumOptions.UrlApiStockfish);
                console.log('BetterMint: Using WebSocket URL:', wsUrl);

                if (getValueConfig(enumOptions.ApiStockfish)) {
                    this.initializeWebSocket(wsUrl);
                } else {
                    logMessage("Server mode required - no local engine support", 'error');
                }
            });

            // Listen for WebSocket URL changes
            chrome.storage.onChanged.addListener((changes, namespace) => {
                if (namespace === 'local' && changes.wsUrl) {
                    console.log('BetterMint: WebSocket URL changed, reconnecting...');
                    if (this.websocket) {
                        this.websocket.close();
                    }
                    this.connectionRetries = 0;
                    this.initializeWebSocket(changes.wsUrl.newValue);
                }
            });
        } else {
            // Fallback if chrome.storage not available
            if (getValueConfig(enumOptions.ApiStockfish)) {
                this.initializeWebSocket(getValueConfig(enumOptions.UrlApiStockfish));
            } else {
                logMessage("Server mode required - no local engine support", 'error');
            }
        }
    }

    initializeWebSocket(url) {
        try {
            this.websocket = new WebSocket(url);

            this.websocket.addEventListener("open", () => {
                console.log("BetterMint WebSocket connected");
                this.connectionRetries = 0;
                logMessage("Connected to BetterMint Server", 'success');
                this.send("client_ready");
            });

            this.websocket.addEventListener("message", (event) => {
                this.processServerMessage(event.data);
            });

            this.websocket.addEventListener("close", () => {
                console.error("BetterMint WebSocket connection closed");
                this.handleDisconnect();
            });

            this.websocket.addEventListener("error", (error) => {
                console.error("BetterMint WebSocket error:", error);
                this.handleDisconnect();
            });
        } catch (e) {
            console.error("Failed to initialize WebSocket:", e);
            logMessage("Failed to connect to BetterMint Server", 'error');
            throw e;
        }
    }

    send(cmd) {
        if (this.isWebSocketOpen()) {
            this.websocket.send(cmd);
            console.log("Sent to server:", cmd);
        } else {
            console.warn("Attempted to send command while WebSocket is not open:", cmd);
        }
    }

    isWebSocketOpen() {
        return this.websocket && this.websocket.readyState === WebSocket.OPEN;
    }

    handleDisconnect() {
        logMessage("Lost connection to BetterMint Server", 'warning');
        this.attemptReconnect();
    }

    attemptReconnect() {
        if (this.connectionRetries < this.maxRetries) {
            this.connectionRetries++;
            const delay = Math.min(this.reconnectDelay * this.connectionRetries, this.maxReconnectDelay);
            console.log(`Attempting to reconnect in ${delay / 1000} seconds... (${this.connectionRetries}/${this.maxRetries})`);
            setTimeout(() => {
                // Get current WebSocket URL from storage
                if (typeof chrome !== 'undefined' && chrome.storage) {
                    chrome.storage.local.get(['wsUrl'], (result) => {
                        const wsUrl = result.wsUrl || getValueConfig(enumOptions.UrlApiStockfish);
                        this.initializeWebSocket(wsUrl);
                    });
                } else {
                    this.initializeWebSocket(getValueConfig(enumOptions.UrlApiStockfish));
                }
            }, delay);
        } else {
            logMessage("Failed to reconnect to server. Please check connection.", 'error');
        }
    }

    // Process all server messages and execute commands
    processServerMessage(message) {
        let line = String(message).trim();
        console.log("Processing server message:", line);

        // Handle server move commands
        if (line.startsWith("move_command")) {
            this.handleMoveCommand(line);
            return;
        }

        // Handle server visual updates
        if (line.startsWith("visual_update")) {
            this.handleVisualUpdate(line);
            return;
        }

        // Handle evaluation updates
        if (line.startsWith("evaluation_update")) {
            this.handleEvaluationUpdate(line);
            return;
        }

        // Handle depth updates
        if (line.startsWith("depth_update")) {
            this.handleDepthUpdate(line);
            return;
        }

        // Handle server status messages
        if (line.startsWith("status")) {
            console.log("Server status:", line);
            return;
        }

        // Handle errors
        if (line.startsWith("error")) {
            console.warn("Server error:", line);
            logMessage(line, 'error');
            return;
        }

        console.log("Unhandled server message:", line);
    }

    // Handle explicit move commands from server
    handleMoveCommand(line) {
        console.log("Handling server move command:", line);

        // Parse: "move_command e2e4 delay_ms 2500"
        const parts = line.split(' ');
        if (parts.length < 2) {
            console.error("Invalid move command format:", line);
            return;
        }

        const move = parts[1];
        const delayMs = parts.length >= 4 ? parseInt(parts[3]) || 0 : 0;

        const moveData = {
            from: move.substring(0, 2),
            to: move.substring(2, 4),
            promotion: move.length > 4 ? move.substring(4, 5) : null
        };

        console.log(`Server commanding move: ${move} in ${delayMs}ms`);
        logMessage(`Server move command: ${move} (${delayMs}ms delay)`, 'info');

        // Execute after server-specified delay
        if (delayMs > 0) {
            setTimeout(() => {
                this.BetterMintmaster.game.executeCommandedMove(moveData);
            }, delayMs);
        } else {
            this.BetterMintmaster.game.executeCommandedMove(moveData);
        }
    }

    // Handle visual updates from server
    handleVisualUpdate(line) {
        try {
            const jsonData = line.substring("visual_update ".length);
            const data = JSON.parse(jsonData);

            console.log("Received visual update from server:", data);
            this.BetterMintmaster.game.displayServerVisuals(data);

        } catch (e) {
            console.error("Failed to parse visual update:", e);
        }
    }

    // Handle evaluation updates from server
    handleEvaluationUpdate(line) {
        try {
            const parts = line.split(' ');
            if (parts.length < 3) return;

            const score = parseFloat(parts[1]);
            const isMate = parts[2] === 'true';

            console.log("Server evaluation update:", score, isMate);
            this.BetterMintmaster.game.SetEvaluation(
                isMate ? (score > 0 ? 1 : -1) : Math.round(score * 100),
                isMate
            );
        } catch (e) {
            console.error("Failed to parse evaluation update:", e);
        }
    }

    // Handle depth updates from server
    handleDepthUpdate(line) {
        try {
            const parts = line.split(' ');
            if (parts.length < 2) return;

            const depthPercent = parseFloat(parts[1]);

            console.log("Server depth update:", depthPercent);
            this.BetterMintmaster.game.SetCurrentDepth(depthPercent);
        } catch (e) {
            console.error("Failed to parse depth update:", e);
        }
    }

    quit() {
        console.log("Shutting down server connection");
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.send("client_disconnect");
            setTimeout(() => {
                this.websocket.close();
            }, 500);
        }
    }
}

// BetterMint main class - pure client controller
class BetterMint {
    constructor(chessboard, options) {
        this.options = options;
        this.game = new GameController(this, chessboard);
        this.serverController = new ServerController(this);
        this.sessionStats = {
            gamesPlayed: 0,
            movesReported: 0,
            startTime: Date.now()
        };

        // Settings synchronization with server
        window.addEventListener("BetterMintUpdateOptions", (event) => {
            this.options = event.detail;
            this.game.UpdateExtensionOptions();

            // Save settings to server
            ServerRequest.updateSettings(this.options);

            logMessage("Settings updated!", 'success');
        }, false);
    }

    onEngineLoaded() {
        logMessage("BetterMint Server Client is ready!", 'success');
        console.log("BetterMint Modded (MINT Beta 2c 26092025 Features) - Pure Server Client - Ready");
    }

    getSessionStats() {
        return {
            ...this.sessionStats,
            uptime: Date.now() - this.sessionStats.startTime
        };
    }
}

// Initialize BetterMint as pure server client
function InitBetterMint(chessboard) {
    console.log("Initializing BetterMint Server Client with chessboard:", chessboard);

    // ECO table loading for analysis context
    if (Config?.pathToEcoJson) {
        fetch(Config.pathToEcoJson)
            .then(response => response.json())
            .then(table => {
                eTable = new Map(table.map(data => [data.f, true]));
                console.log("ECO table loaded");
            })
            .catch(error => {
                console.warn("Failed to load ECO table:", error);
            });
    }

    // Initialize with server settings
    ServerRequest.getData().then(function (options) {
        try {
            console.log("Creating BetterMint Server Client with options:", options);
            BetterMintmaster = new BetterMint(chessboard, options);

            // Basic keyboard shortcuts for game control
            document.addEventListener("keypress", function (e) {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

                switch (e.key) {
                    case "q": BetterMintmaster.game.controller.moveBackward(); break;
                    case "e": BetterMintmaster.game.controller.moveForward(); break;
                    case "r": BetterMintmaster.game.controller.resetGame(); break;
                    case "w":
                        BetterMintmaster.game.ResetGame();
                        BetterMintmaster.game.RefreshEvalutionBar();
                        break;
                }
            });

            console.log("BetterMint Server Client initialized successfully");
        } catch (e) {
            console.error("Failed to initialize BetterMint Server Client:", e);
            logMessage("Failed to initialize BetterMint Server Client", 'error');
        }
    });
}

// Enhanced observer for chessboard detection
const observer = new MutationObserver(async function (mutations) {
    mutations.forEach(async function (mutation) {
        mutation.addedNodes.forEach(async function (node) {
            if (node.nodeType === Node.ELEMENT_NODE) {
                if (node.tagName == "WC-CHESS-BOARD" || node.tagName == "CHESS-BOARD") {
                    if (Object.hasOwn(node, "game")) {
                        console.log("Found chessboard, initializing BetterMint Server Client");
                        InitBetterMint(node);
                        observer.disconnect();
                    }
                }
            }
        });
    });
});

observer.observe(document, {
    childList: true,
    subtree: true
});

console.log("BetterMint Modded - Pure Server Client - Script loaded");