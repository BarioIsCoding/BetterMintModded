"use strict";

// BetterMint Modded - Enhanced Chess Engine Integration
// Server-side settings management with improved performance and features

var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};

// Enhanced server communication with retry logic
var ServerRequest = (function () {
    var requestId = 0;
    var serverUrl = 'http://localhost:8000';
    var connectionAttempts = 0;
    var maxRetries = 3;
    
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
            console.warn(`BetterMint Modded: Server request failed for ${endpoint}:`, error);
            throw error;
        });
    }
    
    function getData(data = null) {
        var id = requestId++;
        return new Promise(function (resolve, reject) {
            // Try server first, fallback to default options
            makeRequest('/api/settings')
                .then(serverSettings => {
                    resolve(serverSettings);
                })
                .catch(error => {
                    console.log('BetterMint Modded: Using default settings, server unavailable');
                    // Fallback to legacy Chrome storage request for backwards compatibility
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
            console.warn('BetterMint Modded: Failed to save settings to server:', error);
        });
    }
    
    return { getData, updateSettings, makeRequest };
})();

// Enhanced gradient color calculation
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

// Enhanced notification system
function showNotification(message, type = 'info', duration = 3000) {
    // Remove existing notifications
    const existing = document.querySelectorAll('.betterMint-notification');
    existing.forEach(n => n.remove());
    
    const notification = document.createElement('div');
    notification.className = `betterMint-notification ${type}`;
    notification.textContent = message;
    
    // Add icon based on type
    const icon = document.createElement('span');
    icon.style.marginRight = '8px';
    switch (type) {
        case 'success':
            icon.textContent = '✓';
            break;
        case 'error':
            icon.textContent = '✗';
            break;
        case 'warning':
            icon.textContent = '⚠';
            break;
        default:
            icon.textContent = 'ℹ';
    }
    notification.insertBefore(icon, notification.firstChild);
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Performance monitoring
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            evaluationTime: [],
            movesAnalyzed: 0,
            serverLatency: [],
            engineDepth: 0
        };
        this.indicator = null;
        this.enabled = false;
    }
    
    enable() {
        this.enabled = true;
        this.createIndicator();
    }
    
    disable() {
        this.enabled = false;
        if (this.indicator) {
            this.indicator.remove();
            this.indicator = null;
        }
    }
    
    createIndicator() {
        if (this.indicator) return;
        
        this.indicator = document.createElement('div');
        this.indicator.className = 'performance-indicator';
        document.body.appendChild(this.indicator);
        this.updateDisplay();
    }
    
    recordEvaluation(timeMs, depth) {
        if (!this.enabled) return;
        
        this.metrics.evaluationTime.push(timeMs);
        this.metrics.engineDepth = depth;
        this.metrics.movesAnalyzed++;
        
        // Keep only last 50 measurements
        if (this.metrics.evaluationTime.length > 50) {
            this.metrics.evaluationTime.shift();
        }
        
        this.updateDisplay();
    }
    
    recordServerLatency(timeMs) {
        if (!this.enabled) return;
        
        this.metrics.serverLatency.push(timeMs);
        if (this.metrics.serverLatency.length > 20) {
            this.metrics.serverLatency.shift();
        }
    }
    
    updateDisplay() {
        if (!this.indicator) return;
        
        const avgEval = this.metrics.evaluationTime.length > 0 
            ? Math.round(this.metrics.evaluationTime.reduce((a, b) => a + b, 0) / this.metrics.evaluationTime.length)
            : 0;
        
        const avgLatency = this.metrics.serverLatency.length > 0
            ? Math.round(this.metrics.serverLatency.reduce((a, b) => a + b, 0) / this.metrics.serverLatency.length)
            : 0;
        
        this.indicator.innerHTML = `
            <div>Eval: ${avgEval}ms | Depth: ${this.metrics.engineDepth}</div>
            <div>Moves: ${this.metrics.movesAnalyzed} | Latency: ${avgLatency}ms</div>
        `;
    }
}

// Global performance monitor instance
const performanceMonitor = new PerformanceMonitor();

// Settings enumeration
var enumOptions = {
    UrlApiStockfish: "url-api-stockfish",
    ApiStockfish: "api-stockfish", 
    NumCores: "num-cores",
    HashtableRam: "hashtable-ram",
    Depth: "depth",
    MateFinderValue: "mate-finder-value",
    MultiPV: "multipv",
    HighMateChance: "highmatechance",
    AutoMoveTime: "auto-move-time",
    AutoMoveTimeRandom: "auto-move-time-random",
    AutoMoveTimeRandomDiv: "auto-move-time-random-div",
    AutoMoveTimeRandomMulti: "auto-move-time-random-multi",
    Premove: "premove-enabled",
    MaxPreMoves: "max-premoves",
    PreMoveTime: "premove-time",
    PreMoveTimeRandom: "premove-time-random",
    PreMoveTimeRandomDiv: "premove-time-random-div",
    PreMoveTimeRandomMulti: "premove-time-random-multi",
    LegitAutoMove: "legit-auto-move",
    BestMoveChance: "best-move-chance",
    RandomBestMove: "random-best-move",
    ShowHints: "show-hints",
    TextToSpeech: "text-to-speech",
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

// Enhanced TopMove class with additional properties
class TopMove {
    constructor(line, depth, cp, mate, multipv = 1) {
        this.line = line.split(" ");
        this.move = this.line[0];
        this.promotion = this.move.length > 4 ? this.move.substring(4, 5) : null;
        this.from = this.move.substring(0, 2);
        this.to = this.move.substring(2, 4);
        this.cp = cp;
        this.mate = mate;
        this.depth = depth;
        this.multipv = multipv;
        this.evaluationTime = Date.now();
        this.quality = this.calculateMoveQuality();
    }
    
    calculateMoveQuality() {
        if (this.mate !== null) {
            return this.mate > 0 ? 'brilliant' : 'blunder';
        }
        
        if (this.cp === null) return 'unknown';
        
        const absEval = Math.abs(this.cp);
        if (absEval >= 300) return 'excellent';
        if (absEval >= 100) return 'good';
        if (absEval >= 50) return 'average';
        return 'poor';
    }
}

// Enhanced GameController with additional features
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
            averageEvalTime: 0,
            bestMoveAccuracy: 0
        };
        
        let self = this;
        
        this.controller.on("Move", (event) => {
            console.log("Move detected:", event.data);
            this.gameStats.movesPlayed++;
            this.UpdateEngine(false);
        });
        
        // Enhanced game state management
        if (this.evalBar == null && getValueConfig(enumOptions.EvaluationBar)) {
            this.CreateAnalysisTools();
        }
        
        this.controller.on('ModeChanged', (event) => {
            if (event.data === "playing") {
                this.ResetGame();
                BetterMintmaster.game.RefreshEvalutionBar();
                BetterMintmaster.engine.moveCounter = 0;
                BetterMintmaster.engine.hasShownLimitMessage = false;
                BetterMintmaster.engine.isPreMoveSequence = true;
                showNotification("New game started - BetterMint Modded ready!", 'success');
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
    
    UpdateEngine(isNewGame) {
        const startTime = Date.now();
        let FENs = this.controller.getFEN();
        this.BetterMintmaster.engine.UpdatePosition(FENs, isNewGame);
        this.SetCurrentDepth(0);
        
        // Record evaluation time
        setTimeout(() => {
            performanceMonitor.recordEvaluation(Date.now() - startTime, this.BetterMintmaster.engine.depth);
        }, 100);
    }
    
    ResetGame() {
        this.UpdateEngine(true);
        this.gameStats = { movesPlayed: 0, averageEvalTime: 0, bestMoveAccuracy: 0 };
        BetterMintmaster.game.RefreshEvalutionBar();
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
    
    HintMoves(topMoves, lastTopMoves, isBestMove) {
        let bestMove = topMoves[0];
        if (getValueConfig(enumOptions.ShowHints)) {
            this.RemoveCurrentMarkings();
            topMoves.forEach((move, idx) => {
                if (isBestMove && move.depth != bestMove.depth) return;

                // Enhanced move quality visualization
                if (idx != 0 && move.cp != null && move.mate == null) {
                    let hlColor = getGradientColor("#ff0000", "#0000ff", Math.min(((move.cp + 250) / 500) ** 4), 1);
                    this.currentMarkings.push({
                        data: { opacity: 0.4, color: hlColor, square: move.to },
                        node: true, persistent: true, type: "highlight",
                    });
                }

                // Enhanced arrow colors based on move quality
                let color = this.options.arrowColors.alt;
                if (idx == 0) {
                    color = move.quality === 'brilliant' ? '#1baca6' : this.options.arrowColors.alt;
                } else if (idx >= 1 && idx <= 2) {
                    color = this.options.arrowColors.shift;
                } else if (idx >= 3 && idx <= 5) {
                    color = this.options.arrowColors.default;
                } else {
                    color = this.options.arrowColors.ctrl;
                }
                
                this.currentMarkings.push({
                    data: { from: move.from, color: color, opacity: 0.8, to: move.to },
                    node: true, persistent: true, type: "arrow",
                });
                
                if (move.mate != null) {
                    this.currentMarkings.push({
                        data: { square: move.to, type: move.mate < 0 ? "ResignWhite" : "WinnerWhite" },
                        node: true, persistent: true, type: "effect",
                    });
                }
            });
            
            this.currentMarkings.reverse();
            this.controller.markings.addMany(this.currentMarkings);
        }
        
        if (getValueConfig(enumOptions.DepthBar)) {
            let depthPercent = ((isBestMove ? bestMove.depth : bestMove.depth - 1) / getValueConfig(enumOptions.Depth)) * 100;
            this.SetCurrentDepth(depthPercent);
        }
        
        if (getValueConfig(enumOptions.EvaluationBar)) {
            let score = bestMove.mate != null ? bestMove.mate : bestMove.cp;
            if (this.controller.getTurn() == 2) score *= -1;
            this.SetEvaluation(score, bestMove.mate != null);
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
}

// Enhanced StockfishEngine class with improved connectivity and performance
class StockfishEngine {
    constructor(BetterMintmaster) {
        let stockfishJsURL;
        let stockfishPathConfig = Config?.threadedEnginePaths?.stockfish;
        this.BetterMintmaster = BetterMintmaster;
        this.loaded = false;
        this.stopInFlight = false;
        this.ready = false;
        this.isEvaluating = false;
        this.isRequestedStop = false;
        this.isGameStarted = false;
        this.readyCallbacks = [];
        this.goDoneCallbacks = [];
        this.topMoves = [];
        this.lastTopMoves = [];
        this.moveCounter = 0;
        this.maxAutoMoves = 5;
        this.isPreMoveSequence = false;
        this.hasShownLimitMessage = false;
        this.isInTheory = false;
        this.lastMoveScore = null;
        this.depth = getValueConfig(enumOptions.Depth);
        this.connectionRetries = 0;
        this.maxRetries = 5;
        this.options = {
            "Slow Mover": "10",
            "MultiPV": getValueConfig(enumOptions.MultiPV),
        };

        // Enhanced WebSocket connection with retry logic
        if (getValueConfig(enumOptions.ApiStockfish)) {
            this.initializeWebSocket(getValueConfig(enumOptions.UrlApiStockfish));
        } else {
            // Fallback to local engine if available
            try {
                new SharedArrayBuffer(getValueConfig(enumOptions.HashtableRam));
                stockfishJsURL = `${stockfishPathConfig.multiThreaded.loader}#${stockfishPathConfig.multiThreaded.engine}`;
            } catch (e) {
                stockfishJsURL = `${stockfishPathConfig.singleThreaded.loader}#${stockfishPathConfig.singleThreaded.engine}`;
            }
            this.initializeWorker(stockfishJsURL);
        }

        this.reconnectDelay = 500;
        this.maxReconnectDelay = 3000;
        this.reconnectAttempts = 5;
    }

    initializeWorker(stockfishJsURL) {
        try {
            this.stockfish = new Worker(stockfishJsURL);
            this.stockfish.onmessage = (e) => {
                this.ProcessMessage(e);
            };
            this.send("uci");
            this.onReady(() => {
                this.UpdateOptions();
                this.send("ucinewgame");
            });
        } catch (e) {
            showNotification("Failed to load Stockfish engine", 'error');
            throw e;
        }
    }

    initializeWebSocket(url) {
        const startTime = Date.now();
        try {
            this.stockfish = new WebSocket(url);
            
            this.stockfish.addEventListener("open", () => {
                const latency = Date.now() - startTime;
                performanceMonitor.recordServerLatency(latency);
                console.log("BetterMint WebSocket connected");
                this.connectionRetries = 0;
                showNotification("Connected to BetterMint Server", 'success');
                this.send("uci");
                this.onReady(() => {
                    this.UpdateOptions();
                    this.send("ucinewgame");
                });
            });

            this.stockfish.addEventListener("message", (event) => {
                this.ProcessMessage(event.data);
            });

            this.stockfish.addEventListener("close", () => {
                console.error("BetterMint WebSocket connection closed");
                this.handleDisconnect();
            });

            this.stockfish.addEventListener("error", (error) => {
                console.error("BetterMint WebSocket error:", error);
                this.handleDisconnect();
            });
        } catch (e) {
            console.error("Failed to initialize WebSocket:", e);
            showNotification("Failed to connect to BetterMint Server", 'error');
            throw e;
        }
    }

    send(cmd) {
        if (this.isWebSocketOpen()) {
            if (!getValueConfig(enumOptions.ApiStockfish)) {
                this.stockfish.postMessage(cmd);
            } else {
                this.stockfish.send(cmd);
            }
        } else {
            console.warn("Attempted to send command while WebSocket is not open:", cmd);
        }
    }

    isWebSocketOpen() {
        return this.stockfish && this.stockfish.readyState === WebSocket.OPEN;
    }

    go() {
        this.onReady(() => {
            this.stopEvaluation(() => {
                if (this.isEvaluating) return;
                console.assert(!this.isEvaluating, "Duplicated Stockfish go command");
                this.isEvaluating = true;
                this.send(`go depth ${this.depth}`);
            });
        });
    }

    handleDisconnect() {
        this.ready = false;
        this.loaded = false;
        this.isEvaluating = false;
        showNotification("Lost connection to BetterMint Server", 'warning');
        this.attemptReconnect();
    }

    attemptReconnect() {
        if (this.connectionRetries < this.maxRetries) {
            this.connectionRetries++;
            const delay = Math.min(this.reconnectDelay * this.connectionRetries, this.maxReconnectDelay);
            console.log(`Attempting to reconnect in ${delay / 1000} seconds... (${this.connectionRetries}/${this.maxRetries})`);
            setTimeout(() => {
                this.initializeWebSocket(getValueConfig(enumOptions.UrlApiStockfish));
            }, delay);
        } else {
            showNotification("Failed to reconnect to server. Please check connection.", 'error');
        }
    }

    onReady(callback) {
        if (this.ready) {
            callback();
        } else {
            this.readyCallbacks.push(callback);
            this.send("isready");
        }
    }

    stopEvaluation(callback) {
        if (this.isEvaluating) {
            if (!this.stopInFlight) {
                this.stopInFlight = true;
                this.goDoneCallbacks = [() => {
                    this.isEvaluating = false;
                    this.isRequestedStop = false;
                    callback();
                }];
                this.isRequestedStop = true;
                this.send("stop");
                this.send("ucinewgame");
                this.stopInFlight = false;
                this.goDoneCallbacks.forEach(cb => cb());
                this.goDoneCallbacks = [];
            } else {
                this.goDoneCallbacks.push(callback);
            }
        } else {
            callback();
        }
    }

    onStockfishResponse() {
        if (this.isRequestedStop) {
            this.isRequestedStop = false;
            this.stopInFlight = false;
            this.isEvaluating = false;
            this.executeCallbacks();
        }
    }

    executeCallbacks() {
        while (this.goDoneCallbacks.length) {
            const callback = this.goDoneCallbacks.shift();
            callback();
        }
    }

    UpdatePosition(FENs = null, isNewGame = true) {
        this.onReady(() => {
            this.stopEvaluation(() => {
                if (isNewGame) {
                    this.moveCounter = 0;
                    this.hasShownLimitMessage = false;
                    this.isPreMoveSequence = true;
                    console.log("NEW GAME - COUNTERS RESET");
                }
                this.MoveAndGo(FENs, isNewGame);
            });
        });
    }

    restartGame() {
        this.stopEvaluation(() => {
            this.isGameStarted = false;
            this.moveCounter = 0;
            this.isPreMoveSequence = false;
            this.send("ucinewgame");
            this.isGameStarted = true;
            this.go();
        });
    }

    UpdateExtensionOptions(options) {
        if (options == null) options = this.options;
        Object.keys(options).forEach((key) => {
            this.send(`setoption name ${key} value ${options[key]}`);
        });
        this.depth = getValueConfig(enumOptions.Depth);
        if (this.topMoves.length > 0) this.onTopMoves(null, !this.isEvaluating);
    }

    UpdateOptions(options = null) {
        if (options === null) options = this.options;
        Object.keys(options).forEach((key) => {
            this.send(`setoption name ${key} value ${options[key]}`);
        });
    }

    ProcessMessage(event) {
        this.ready = false;
        let line = event && typeof event === "object" ? event.data : event;

        if (line === "uciok") {
            this.loaded = true;
            this.BetterMintmaster.onEngineLoaded();
        } else if (line === "readyok") {
            this.ready = true;
            if (this.readyCallbacks.length > 0) {
                let copy = this.readyCallbacks;
                this.readyCallbacks = [];
                copy.forEach(function (callback) {
                    callback();
                });
            }
        } else if (this.isEvaluating && line === "Load eval file success: 1") {
            this.isEvaluating = false;
            this.isRequestedStop = false;
            if (this.goDoneCallbacks.length > 0) {
                let copy = this.goDoneCallbacks;
                this.goDoneCallbacks = [];
                copy.forEach(function (callback) {
                    callback();
                });
            }
        } else {
            // Enhanced message parsing with better error handling
            let depthMatch = line.match(/^info .*?depth (\d+)/);
            let seldepthMatch = line.match(/^info .*?seldepth (\d+)/);
            let timeMatch = line.match(/^info .*?time (\d+)/);
            let scoreMatch = line.match(/^info .*?score (\w+) (-?\d+)/);
            let pvMatch = line.match(/^info .*?pv ([a-h][1-8][a-h][1-8][qrbn]?(?: [a-h][1-8][a-h][1-8][qrbn]?)*)(?: .*)?/);
            let multipvMatch = line.match(/^info .*?multipv (\d+)/);
            let bestMoveMatch = line.match(/^bestmove ([a-h][1-8][a-h][1-8][qrbn]?)(?: ponder ([a-h][1-8][a-h][1-8][qrbn]?))?/);

            if (depthMatch && scoreMatch && pvMatch) {
                let depth = parseInt(depthMatch[1]);
                let seldepth = seldepthMatch ? parseInt(seldepthMatch[1]) : null;
                let time = timeMatch ? parseInt(timeMatch[1]) : null;
                let scoreType = scoreMatch[1];
                let score = parseInt(scoreMatch[2]);
                let multipv = multipvMatch ? parseInt(multipvMatch[1]) : 1;
                let pv = pvMatch[1];

                let cpScore = scoreType === "cp" ? score : null;
                let mateScore = scoreType === "mate" ? score : null;

                if (!this.isRequestedStop) {
                    let move = new TopMove(pv, depth, cpScore, mateScore, multipv);
                    this.onTopMoves(move, false);
                }
            } else if (bestMoveMatch) {
                this.isEvaluating = false;
                if (this.goDoneCallbacks.length > 0) {
                    let copy = this.goDoneCallbacks;
                    this.goDoneCallbacks = [];
                    copy.forEach(function (callback) {
                        callback();
                    });
                }
                if (!this.isRequestedStop && bestMoveMatch[1] !== undefined) {
                    const bestMove = bestMoveMatch[1];
                    const ponderMove = bestMoveMatch[2];
                    const index = this.topMoves.findIndex((object) => object.move === bestMove);

                    if (index < 0) {
                        console.warn(`Engine returned best move "${bestMove}" not in top move list`);
                        let bestMoveOnTop = new TopMove(bestMove, getValueConfig(enumOptions.Depth), 100, null);
                        this.onTopMoves(bestMoveOnTop, true);
                    } else {
                        this.onTopMoves(this.topMoves[index], true);
                    }
                }
                this.isRequestedStop = false;
            }
        }
    }

    executeReadyCallbacks() {
        while (this.readyCallbacks.length > 0) {
            const callback = this.readyCallbacks.shift();
            callback();
        }
    }

    MoveAndGo(FENs = null, isNewGame = true) {
        let go = () => {
            this.lastTopMoves = isNewGame ? [] : this.topMoves;
            this.lastMoveScore = null;
            this.topMoves = [];
            if (isNewGame) this.isInTheory = eTable != null;
            if (this.isInTheory) {
                let shortFen = this.BetterMintmaster.game.controller.getFEN().split(" ").slice(0, 3).join(" ");
                if (eTable.get(shortFen) !== true) this.isInTheory = false;
            }
            if (FENs != null) this.send(`position fen ${FENs}`);
            this.go();
        };
        this.onReady(() => {
            if (isNewGame) {
                this.send("ucinewgame");
                this.onReady(go);
            } else {
                go();
            }
        });
    }

    AnalyzeLastMove() {
        this.lastMoveScore = null;
        let lastMove = this.BetterMintmaster.game.controller.getLastMove();
        if (lastMove === undefined) return;
        
        if (this.isInTheory) {
            this.lastMoveScore = "Book";
        } else if (this.lastTopMoves.length > 0) {
            let lastBestMove = this.lastTopMoves[0];
            if (lastBestMove.from === lastMove.from && lastBestMove.to === lastMove.to) {
                this.lastMoveScore = "BestMove";
            } else {
                let bestMove = this.topMoves[0];
                if (lastBestMove.mate != null) {
                    if (bestMove.mate == null) {
                        this.lastMoveScore = lastBestMove.mate > 0 ? "MissedWin" : "Brilliant";
                    } else {
                        this.lastMoveScore = lastBestMove.mate > 0 ? "Excellent" : "ResignWhite";
                    }
                } else if (bestMove.mate != null) {
                    this.lastMoveScore = bestMove.mate < 0 ? "Brilliant" : "Blunder";
                } else if (bestMove.cp != null && lastBestMove.cp != null) {
                    let evalDiff = -(bestMove.cp + lastBestMove.cp);
                    if (evalDiff > 100) this.lastMoveScore = "Brilliant";
                    else if (evalDiff > 0) this.lastMoveScore = "GreatFind";
                    else if (evalDiff > -10) this.lastMoveScore = "BestMove";
                    else if (evalDiff > -25) this.lastMoveScore = "Excellent";
                    else if (evalDiff > -50) this.lastMoveScore = "Good";
                    else if (evalDiff > -100) this.lastMoveScore = "Inaccuracy";
                    else if (evalDiff > -250) this.lastMoveScore = "Mistake";
                    else this.lastMoveScore = "Blunder";
                } else {
                    console.assert(false, "Error while analyzing last move");
                }
            }
        }

        // Enhanced move highlighting with improved colors
        if (this.lastMoveScore != null) {
            const highlightColors = {
                Brilliant: "#1baca6",
                GreatFind: "#5c8bb0", 
                BestMove: "#9eba5a",
                Excellent: "#96bc4b",
                Good: "#96af8b",
                Book: "#a88865",
                Inaccuracy: "#f0c15c",
                Mistake: "#e6912c",
                Blunder: "#b33430",
                MissedWin: "#dbac16",
            };
            let hlColor = highlightColors[this.lastMoveScore];
            if (hlColor != null) {
                this.BetterMintmaster.game.controller.markings.addOne({
                    data: { opacity: 0.5, color: hlColor, square: lastMove.to },
                    node: true, persistent: true, type: "highlight",
                });
            }
            this.BetterMintmaster.game.controller.markings.addOne({
                data: { square: lastMove.to, type: this.lastMoveScore },
                node: true, persistent: true, type: "effect",
            });
        }
    }

    onTopMoves(move = null, isBestMove = false) {
        window.top_pv_moves = [];
        var bestMoveSelected = false;
        
        if (move != null) {
            const index = this.topMoves.findIndex((object) => object.move === move.move);
            if (isBestMove) {
                bestMoveSelected = true;
                if (index === -1) {
                    this.topMoves.push(move);
                    this.SortTopMoves();
                }
            } else {
                if (index === -1) {
                    this.topMoves.push(move);
                    this.SortTopMoves();
                } else {
                    if (move.depth >= this.topMoves[index].depth) {
                        this.topMoves[index] = move;
                        this.SortTopMoves();
                    }
                }
            }
        }

        // Enhanced pre-move logic with better timing and safety checks
        if (bestMoveSelected && this.topMoves.length > 0) {
            const bestMove = this.topMoves[0];
            const currentFEN = this.BetterMintmaster.game.controller.getFEN();
            const currentTurn = currentFEN.split(" ")[1];
            const playingAs = this.BetterMintmaster.game.controller.getPlayingAs();

            if (getValueConfig(enumOptions.Premove) && getValueConfig(enumOptions.LegitAutoMove)) {
                if (((playingAs === 1 && currentTurn === 'w') || (playingAs === 2 && currentTurn === 'b')) &&
                    this.moveCounter < getValueConfig(enumOptions.MaxPreMoves) && !this.hasShownLimitMessage) {
                    const legalMoves = this.BetterMintmaster.game.controller.getLegalMoves();
                    const moveData = legalMoves.find(move => move.from === bestMove.from && move.to === bestMove.to);

                    if (moveData) {
                        moveData.userGenerated = true;
                        if (bestMove.promotion !== null) {
                            moveData.promotion = bestMove.promotion;
                        }
                        this.moveCounter++;

                        let pre_move_time = getValueConfig(enumOptions.PreMoveTime) +
                            (Math.floor(Math.random() * getValueConfig(enumOptions.PreMoveTimeRandom)) %
                            getValueConfig(enumOptions.PreMoveTimeRandomDiv)) *
                            getValueConfig(enumOptions.PreMoveTimeRandomMulti);

                        setTimeout(() => {
                            this.BetterMintmaster.game.controller.move(moveData);
                            showNotification(`Pre-move ${this.moveCounter}/${getValueConfig(enumOptions.MaxPreMoves)} executed!`, 'success', 2000);

                            if (this.moveCounter >= getValueConfig(enumOptions.MaxPreMoves)) {
                                showNotification("Maximum pre-moves reached!", 'warning', 2000);
                                this.hasShownLimitMessage = true;
                            }
                        }, pre_move_time);
                    }
                }

                // Enhanced mate detection with notification
                if (bestMove.mate !== null && bestMove.mate > 0 && bestMove.mate <= getValueConfig(enumOptions.MateFinderValue)) {
                    const legalMoves = this.BetterMintmaster.game.controller.getLegalMoves();
                    const moveData = legalMoves.find(move => move.from === bestMove.from && move.to === bestMove.to);

                    if (moveData) {
                        moveData.userGenerated = true;
                        if (bestMove.promotion !== null) {
                            moveData.promotion = bestMove.promotion;
                        }
                        showNotification(`Mate in ${bestMove.mate} move(s) found! Executing...`, 'success', 2000);
                        this.BetterMintmaster.game.controller.move(moveData);
                    }
                }
            }
        }

        // Enhanced Text-to-Speech with better voice selection
        if (getValueConfig(enumOptions.TextToSpeech) && bestMoveSelected && this.topMoves.length > 0) {
            const topMove = this.topMoves[0];
            const msg = new SpeechSynthesisUtterance(topMove.move);
            const voices = window.speechSynthesis.getVoices();
            const preferredVoice = voices.find(voice => 
                voice.voiceURI.includes("Google UK English Female") || 
                voice.name.includes("Female") ||
                voice.name.includes("Samantha")
            );
            if (preferredVoice) {
                msg.voice = preferredVoice;
            }
            msg.volume = 0.75;
            msg.rate = 1;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(msg);
        }

        if (bestMoveSelected) {
            top_pv_moves = this.topMoves.slice(0, this.options["MultiPV"]);
            this.BetterMintmaster.game.HintMoves(top_pv_moves, this.lastTopMoves, isBestMove);

            if (getValueConfig(enumOptions.MoveAnalysis)) {
                this.AnalyzeLastMove();
            }
        } else {
            // Enhanced move selection logic for ongoing analysis
            if (getValueConfig(enumOptions.LegitAutoMove)) {
                const movesWithAccuracy = this.topMoves.filter(move => move.accuracy !== undefined);
                if (movesWithAccuracy.length > 0) {
                    movesWithAccuracy.sort((a, b) => b.accuracy - a.accuracy);
                    const totalAccuracy = movesWithAccuracy.reduce((sum, move) => sum + move.accuracy, 0);
                    const cumulativeProbabilities = movesWithAccuracy.reduce((arr, move) => {
                        const lastProbability = arr.length > 0 ? arr[arr.length - 1] : 0;
                        const probability = move.accuracy / totalAccuracy;
                        arr.push(lastProbability + probability);
                        return arr;
                    }, []);

                    const random = Math.random();
                    let selectedMove;
                    for (let i = 0; i < cumulativeProbabilities.length; i++) {
                        if (random <= cumulativeProbabilities[i]) {
                            selectedMove = movesWithAccuracy[i];
                            break;
                        }
                    }
                    top_pv_moves = [selectedMove, ...this.topMoves.filter(move => move !== selectedMove)];
                } else {
                    top_pv_moves = this.topMoves.slice(0, this.options["MultiPV"]);
                }
            } else {
                top_pv_moves = this.topMoves.slice(0, this.options["MultiPV"]);
            }
        }

        const bestMoveChance = getValueConfig(enumOptions.BestMoveChance);
        if (Math.random() * 100 < bestMoveChance && getValueConfig(enumOptions.LegitAutoMove)) {
            top_pv_moves = [top_pv_moves[0]];
        }

        // Enhanced auto-move logic with improved timing and notifications
        if (bestMoveSelected && getValueConfig(enumOptions.LegitAutoMove) &&
            this.BetterMintmaster.game.controller.getPlayingAs() === this.BetterMintmaster.game.controller.getTurn()) {
            
            let bestMove;
            if (getValueConfig(enumOptions.RandomBestMove)) {
                const random_best_move_index = Math.floor(Math.random() * top_pv_moves.length);
                bestMove = top_pv_moves[random_best_move_index];
            } else {
                bestMove = top_pv_moves[0];
            }
            
            const legalMoves = this.BetterMintmaster.game.controller.getLegalMoves();
            const index = legalMoves.findIndex(move => move.from === bestMove.from && move.to === bestMove.to);
            console.assert(index !== -1, "Illegal best move");
            const moveData = legalMoves[index];
            moveData.userGenerated = true;
            
            if (bestMove.promotion !== null) {
                moveData.promotion = bestMove.promotion;
            }

            if (getValueConfig(enumOptions.HighMateChance)) {
                const sortedMoves = this.topMoves.sort((a, b) => {
                    if (a.mateIn !== null && b.mateIn === null) {
                        return -1;
                    } else if (a.mateIn === null && b.mateIn !== null) {
                        return 1;
                    } else if (a.mateIn !== null && b.mateIn !== null) {
                        if (a.mateIn <= getValueConfig(enumOptions.MateFinderValue) &&
                            b.mateIn <= getValueConfig(enumOptions.MateFinderValue)) {
                            return a.mateIn - b.mateIn;
                        } else {
                            return 0;
                        }
                    } else {
                        return 0;
                    }
                });
                top_pv_moves = sortedMoves.slice(0, Math.min(this.options["MultiPV"], this.topMoves.length));
                const mateMoves = top_pv_moves.filter(move => move.mateIn !== null);
                if (mateMoves.length > 0) {
                    const fastestMateMove = mateMoves.reduce((a, b) => a.mateIn < b.mateIn ? a : b);
                    top_pv_moves = [fastestMateMove];
                }
            }

            let auto_move_time = getValueConfig(enumOptions.AutoMoveTime) +
                (Math.floor(Math.random() * getValueConfig(enumOptions.AutoMoveTimeRandom)) %
                getValueConfig(enumOptions.AutoMoveTimeRandomDiv)) *
                getValueConfig(enumOptions.AutoMoveTimeRandomMulti);

            if (isNaN(auto_move_time) || auto_move_time === null || auto_move_time === undefined) {
                auto_move_time = 100;
            }

            const secondsTillAutoMove = (auto_move_time / 1000).toFixed(1);
            showNotification(`Auto move in ${secondsTillAutoMove}s`, 'info', parseFloat(secondsTillAutoMove) * 1000);

            setTimeout(() => {
                this.BetterMintmaster.game.controller.move(moveData);
                showNotification("Auto move executed!", 'success');
            }, auto_move_time);
        }
    }

    SortTopMoves() {
        this.topMoves.sort(function (a, b) {
            if (a.mate !== null && b.mate === null) {
                return a.mate < 0 ? 1 : -1;
            }
            if (a.mate === null && b.mate !== null) {
                return b.mate > 0 ? 1 : -1;
            }
            if (a.mate === null && b.mate === null) {
                if (a.depth === b.depth) {
                    if (a.cp === b.cp) return 0;
                    return a.cp > b.cp ? -1 : 1;
                }
                return a.depth > b.depth ? -1 : 1;
            }
            if (a.mate < 0 && b.mate < 0) {
                if (a.line.length === b.line.length) return 0;
                return a.line.length < b.line.length ? 1 : -1;
            }
            if (a.mate > 0 && b.mate > 0) {
                if (a.line.length === b.line.length) return 0;
                return a.line.length > b.line.length ? 1 : -1;
            }
            return a.mate < b.mate ? 1 : -1;
        });
    }
}

// Enhanced BetterMint class with additional features
class BetterMint {
    constructor(chessboard, options) {
        this.options = options;
        this.game = new GameController(this, chessboard);
        this.engine = new StockfishEngine(this);
        this.sessionStats = {
            gamesPlayed: 0,
            movesAnalyzed: 0,
            startTime: Date.now()
        };
        
        // Enhanced settings synchronization with server
        window.addEventListener("BetterMintUpdateOptions", (event) => {
            this.options = event.detail;
            this.game.UpdateExtensionOptions();
            this.engine.UpdateExtensionOptions(this.options);
            
            // Save settings to server
            ServerRequest.updateSettings(this.options);
            
            showNotification("Settings updated!", 'success', 2000);
        }, false);
        
        // Enable performance monitoring if configured
        if (this.options['performance-monitoring']) {
            performanceMonitor.enable();
        }
    }
    
    onEngineLoaded() {
        showNotification("BetterMint Modded is ready!", 'success', 3000);
        console.log("BetterMint Modded v3.0.0 loaded successfully");
    }
    
    resetPreMoveCounter() {
        this.engine.moveCounter = 0;
        this.engine.hasShownLimitMessage = false;
        this.engine.isPreMoveSequence = true;
    }
    
    getSessionStats() {
        return {
            ...this.sessionStats,
            uptime: Date.now() - this.sessionStats.startTime
        };
    }
}

// Enhanced initialization function
function InitBetterMint(chessboard) {
    // Fetch ECO table with improved error handling
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

    // Get settings from server
    ServerRequest.getData().then(function (options) {
        try {
            BetterMintmaster = new BetterMint(chessboard, options);

            // Enhanced keyboard shortcuts
            document.addEventListener("keypress", function (e) {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
                
                switch(e.key) {
                    case "q": BetterMintmaster.game.controller.moveBackward(); break;
                    case "e": BetterMintmaster.game.controller.moveForward(); break;
                    case "r": BetterMintmaster.game.controller.resetGame(); break;
                    case "w": 
                        BetterMintmaster.game.ResetGame();
                        BetterMintmaster.game.RefreshEvalutionBar();
                        break;
                    case "p": // Toggle performance monitor
                        if (performanceMonitor.enabled) {
                            performanceMonitor.disable();
                            showNotification("Performance monitoring disabled", 'info');
                        } else {
                            performanceMonitor.enable();
                            showNotification("Performance monitoring enabled", 'info');
                        }
                        break;
                }
            });
            
            console.log("BetterMint Modded initialized successfully");
        } catch (e) {
            console.error("Failed to initialize BetterMint Modded:", e);
            showNotification("Failed to initialize BetterMint Modded", 'error');
        }
    });
}

// Enhanced observer with better detection
const observer = new MutationObserver(async function (mutations) {
    mutations.forEach(async function (mutation) {
        mutation.addedNodes.forEach(async function (node) {
            if (node.nodeType === Node.ELEMENT_NODE) {
                if (node.tagName == "WC-CHESS-BOARD" || node.tagName == "CHESS-BOARD") {
                    if (Object.hasOwn(node, "game")) {
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

// Enhanced WebRTC configuration for privacy
const config = {
    iceServers: [],
    iceTransportPolicy: "all",
    bundlePolicy: "balanced",
    rtcpMuxPolicy: "require",
    sdpSemantics: "unified-plan",
    peerIdentity: null,
    certificates: [],
};

const constraints = {
    optional: [
        { googIPv6: false },
        { googDscp: false },
        { googCpuOveruseDetection: false },
        { googCpuUnderuseThreshold: 55 },
        { googCpuOveruseThreshold: 85 },
        { googSuspendBelowMinBitrate: false },
        { googScreencastMinBitrate: 400 },
        { googCombinedAudioVideoBwe: false },
        { googScreencastUseTransportCc: false },
        { googNoiseReduction2: false },
        { googHighpassFilter: false },
        { googEchoCancellation3: false },
        { googExperimentalEchoCancellation: false },
        { googAutoGainControl2: false },
        { googTypingNoiseDetection: false },
        { googAutoGainControl: false },
        { googBeamforming: false },
        { googExperimentalNoiseSuppression: false },
        { googEchoCancellation: false },
        { googEchoCancellation2: false },
        { googNoiseReduction: false },
        { googExperimentalWebRtcEchoCancellation: false },
        { googRedundantRtcpFeedback: false },
        { googScreencastDesktopMirroring: false },
        { googSpatialAudio: false },
        { offerToReceiveAudio: false },
        { offerToReceiveVideo: false },
    ],
};

Object.assign(config, constraints);

const oldPeerConnection = window.RTCPeerConnection || window.webkitRTCPeerConnection || window.mozRTCPeerConnection;
if (oldPeerConnection) {
    window.RTCPeerConnection = function (config, constraints) {
        const pc = new oldPeerConnection(config, constraints);
        pc.getTransceivers = function () {
            const transceivers = oldPeerConnection.prototype.getTransceivers.call(this);
            for (const transceiver of transceivers) {
                transceiver.stop();
            }
            return [];
        };
        return pc;
    };
}

// Enhanced message handling
window.addEventListener("bm", function (event) {
    if (event.source === window && event.data) {
        console.log("BetterMint message received:", event.data);
    }
}, false);

console.log("BetterMint Modded v3.0.0 script loaded");