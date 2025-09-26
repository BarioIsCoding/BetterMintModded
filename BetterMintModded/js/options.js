"use strict";

// BetterMint Modded - Complete Options Handler
// All logic for options.html popup

let isConnected = false;
let everConnected = false;
let retryCount = 0;
let checkTimeout = null;
const maxRetries = 3;
const DEFAULT_SERVER_URL = 'http://localhost:8000';
const DEFAULT_WS_URL = 'ws://localhost:8000/ws';

let serverUrl = DEFAULT_SERVER_URL;
let wsUrl = DEFAULT_WS_URL;

// DOM elements - will be initialized after DOM loads
let elements = {};

// Load settings from chrome.storage
function loadSettings() {
    chrome.storage.local.get(['serverUrl', 'wsUrl', 'everConnected'], function (result) {
        if (result.serverUrl) {
            serverUrl = result.serverUrl;
            if (elements.serverUrlInput) {
                elements.serverUrlInput.value = serverUrl;
            }
        }
        if (result.wsUrl) {
            wsUrl = result.wsUrl;
            if (elements.wsUrlInput) {
                elements.wsUrlInput.value = wsUrl;
            }
        }
        if (result.everConnected) {
            everConnected = true;
            hideInstallSection();
        }

        console.log('BetterMint: Settings loaded', { serverUrl, wsUrl, everConnected });

        // Start checking after settings loaded
        checkServerStatus();
    });
}

// Save settings to chrome.storage
function saveSettings() {
    const newServerUrl = elements.serverUrlInput.value.trim() || DEFAULT_SERVER_URL;
    const newWsUrl = elements.wsUrlInput.value.trim() || DEFAULT_WS_URL;

    // Remove trailing slashes
    serverUrl = newServerUrl.replace(/\/$/, '');
    wsUrl = newWsUrl;

    chrome.storage.local.set({
        serverUrl: serverUrl,
        wsUrl: wsUrl
    }, function () {
        console.log('BetterMint: Settings saved', { serverUrl, wsUrl });
        showSuccessBadge();
        retryCount = 0; // Reset retry count on manual save
        checkServerStatus();
    });
}

// Reset settings to defaults
function resetSettings() {
    serverUrl = DEFAULT_SERVER_URL;
    wsUrl = DEFAULT_WS_URL;

    elements.serverUrlInput.value = serverUrl;
    elements.wsUrlInput.value = wsUrl;

    chrome.storage.local.set({
        serverUrl: serverUrl,
        wsUrl: wsUrl
    }, function () {
        console.log('BetterMint: Settings reset to defaults');
        showSuccessBadge();
        retryCount = 0;
        checkServerStatus();
    });
}

// Toggle settings panel
function toggleSettings() {
    const panel = elements.settingsPanel;
    const chevron = elements.settingsChevron;

    if (panel && chevron) {
        panel.classList.toggle('visible');
        chevron.classList.toggle('rotated');
    }
}

// Show success badge temporarily
function showSuccessBadge() {
    if (elements.successBadge) {
        elements.successBadge.classList.add('visible');
        setTimeout(() => {
            elements.successBadge.classList.remove('visible');
        }, 3000);
    }
}

// Hide install section permanently after first connection
function hideInstallSection() {
    if (elements.installSection) {
        elements.installSection.style.display = 'none';
    }
}

// Format uptime in human-readable format
function formatUptime(seconds) {
    if (!seconds || seconds < 0) return 'N/A';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

async function checkServerStatus() {
    console.log('BetterMint: Checking server status at', serverUrl);

    // Clear any existing timeout
    if (checkTimeout) {
        clearTimeout(checkTimeout);
        checkTimeout = null;
    }

    // Reset UI to checking state
    elements.statusCard.className = 'status-card checking';
    elements.statusDot.className = 'status-dot checking';
    elements.statusText.textContent = 'Checking server...';
    elements.statusDetails.textContent = `Connecting to ${serverUrl}`;
    elements.serverInfo.className = 'server-info';
    elements.errorMessage.className = 'error-message hidden';

    try {
        // Use AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        // Try multiple endpoints to be robust
        const endpoints = ['/health', '/api/status', '/'];
        let response = null;
        let data = null;

        for (const endpoint of endpoints) {
            try {
                response = await fetch(`${serverUrl}${endpoint}`, {
                    method: 'GET',
                    signal: controller.signal,
                    headers: {
                        'Accept': 'application/json'
                    }
                });

                if (response.ok) {
                    clearTimeout(timeoutId);

                    // Try to parse as JSON, fallback to assuming healthy
                    try {
                        data = await response.json();
                        console.log('BetterMint: Server response from', endpoint, data);
                        break;
                    } catch (e) {
                        // Not JSON, but server responded - consider it healthy
                        console.log('BetterMint: Server responded (non-JSON) from', endpoint);
                        data = { status: 'healthy', version: 'MINT Beta 2c 26092025 Bugfixes' };
                        break;
                    }
                }
            } catch (e) {
                console.log('BetterMint: Endpoint failed', endpoint, e.message);
                continue;
            }
        }

        clearTimeout(timeoutId);

        if (data) {
            handleSuccessfulConnection(data);
        } else {
            throw new Error('No endpoints responded');
        }

    } catch (error) {
        console.log('BetterMint: Connection check failed', error.message);
        handleConnectionFailure(error.message);
    }
}

function handleSuccessfulConnection(data) {
    console.log('BetterMint: Connection successful', data);

    // Update UI for successful connection
    elements.statusCard.className = 'status-card connected';
    elements.statusDot.className = 'status-dot connected';
    elements.statusText.textContent = 'Connected to BetterMint Modded';
    elements.statusDetails.textContent = 'Server is running and ready';

    // Show server information - handle various response formats
    elements.serverVersion.textContent = data.version || data.app_version || 'MINT Beta 2c 26092025 Bugfixes';
    elements.engineCount.textContent = data.engines || data.engine_count || data.available_engines || 'N/A';

    // Handle uptime - could be in seconds, milliseconds, or as a formatted string
    if (data.uptime) {
        if (typeof data.uptime === 'number') {
            // If it's a large number, assume milliseconds
            const uptimeSeconds = data.uptime > 10000 ? data.uptime / 1000 : data.uptime;
            elements.uptime.textContent = formatUptime(uptimeSeconds);
        } else {
            elements.uptime.textContent = data.uptime;
        }
    } else {
        elements.uptime.textContent = 'N/A';
    }

    elements.serverInfo.className = 'server-info visible';
    elements.errorMessage.className = 'error-message hidden';

    isConnected = true;
    retryCount = 0;

    // Mark that we've connected at least once
    if (!everConnected) {
        everConnected = true;
        chrome.storage.local.set({ everConnected: true });
        hideInstallSection();
        console.log('BetterMint: First successful connection - hiding install section');
    }

    // Schedule next check in 15 seconds
    checkTimeout = setTimeout(checkServerStatus, 15000);
}

function handleConnectionFailure(reason) {
    console.log('BetterMint: Connection failed', reason);

    // Update UI for connection failure
    elements.statusCard.className = 'status-card';
    elements.statusDot.className = 'status-dot';
    elements.statusText.textContent = 'Server not found';
    elements.statusDetails.textContent = 'BetterMint Modded is not running';

    elements.serverInfo.className = 'server-info';
    elements.errorMessage.className = 'error-message';

    // Only show install section if never connected before
    if (!everConnected && elements.installSection) {
        elements.installSection.style.display = 'block';
    }

    isConnected = false;
    retryCount++;

    // Auto-retry with exponential backoff
    if (retryCount <= maxRetries) {
        const delay = Math.min(3000 * retryCount, 10000);
        console.log(`BetterMint: Retry ${retryCount}/${maxRetries} in ${delay}ms`);
        checkTimeout = setTimeout(checkServerStatus, delay);
    } else {
        // After max retries, check every 20 seconds
        console.log('BetterMint: Max retries reached, checking every 20s');
        checkTimeout = setTimeout(checkServerStatus, 20000);
    }
}

// Initialize DOM elements and event listeners
function initializeDOMElements() {
    elements = {
        statusCard: document.getElementById('statusCard'),
        statusDot: document.getElementById('statusDot'),
        statusText: document.getElementById('statusText'),
        statusDetails: document.getElementById('statusDetails'),
        serverInfo: document.getElementById('serverInfo'),
        errorMessage: document.getElementById('errorMessage'),
        installSection: document.getElementById('installSection'),

        serverVersion: document.getElementById('serverVersion'),
        engineCount: document.getElementById('engineCount'),
        uptime: document.getElementById('uptime'),

        settingsSection: document.getElementById('settingsSection'),
        settingsToggle: document.getElementById('settingsToggle'),
        settingsPanel: document.getElementById('settingsPanel'),
        settingsChevron: document.getElementById('settingsChevron'),

        serverUrlInput: document.getElementById('serverUrlInput'),
        wsUrlInput: document.getElementById('wsUrlInput'),
        saveButton: document.getElementById('saveButton'),
        resetButton: document.getElementById('resetButton'),
        retryButton: document.getElementById('retryButton'),
        successBadge: document.getElementById('successBadge')
    };

    // Set up event listeners
    if (elements.settingsToggle) {
        elements.settingsToggle.addEventListener('click', toggleSettings);
    }

    if (elements.saveButton) {
        elements.saveButton.addEventListener('click', saveSettings);
    }

    if (elements.resetButton) {
        elements.resetButton.addEventListener('click', resetSettings);
    }

    if (elements.retryButton) {
        elements.retryButton.addEventListener('click', function () {
            retryCount = 0; // Reset retry count on manual retry
            checkServerStatus();
        });
    }

    // Handle Enter key in input fields
    if (elements.serverUrlInput) {
        elements.serverUrlInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                saveSettings();
            }
        });
    }

    if (elements.wsUrlInput) {
        elements.wsUrlInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                saveSettings();
            }
        });
    }

    console.log('BetterMint: DOM elements initialized');
}

// Handle page visibility changes
document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') {
        console.log('BetterMint: Popup became visible, checking status');
        // Clear old timeout and check immediately when popup becomes visible
        if (checkTimeout) {
            clearTimeout(checkTimeout);
            checkTimeout = null;
        }
        retryCount = 0; // Reset retry count when user opens popup
        setTimeout(checkServerStatus, 100);
    } else {
        console.log('BetterMint: Popup hidden, stopping checks');
        // Stop checking when popup is hidden
        if (checkTimeout) {
            clearTimeout(checkTimeout);
            checkTimeout = null;
        }
    }
});

// Initial load
document.addEventListener('DOMContentLoaded', function () {
    console.log('BetterMint: Options page loaded');
    initializeDOMElements();
    loadSettings();
});

// Handle page unload
window.addEventListener('beforeunload', function () {
    if (checkTimeout) {
        clearTimeout(checkTimeout);
        checkTimeout = null;
    }
    console.log('BetterMint: Options page unloading');
});