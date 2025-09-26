"use strict";

// BetterMint Modded - Content Script Loader with Storage Support
// Fetches server URL from chrome.storage and manages settings

// Default configuration - will be overridden by server and storage
let DefaultExtensionOptions = {
  "url-api-stockfish": "ws://localhost:8000/ws",
  "server-url": "http://localhost:8000",
  "api-stockfish": true,
  "num-cores": 1,
  "hashtable-ram": 1024,
  "depth": 15,
  "mate-finder-value": 5,
  "multipv": 3,
  "auto-move-time": 5000,
  "auto-move-time-random": 2000,
  "auto-move-time-random-div": 10,
  "auto-move-time-random-multi": 1000,
  "legit-auto-move": false,
  "max-premoves": 3,
  "premove-enabled": false,
  "premove-time": 1000,
  "premove-time-random": 500,
  "premove-time-random-div": 100,
  "premove-time-random-multi": 1,
  "best-move-chance": 30,
  "random-best-move": false,
  "show-hints": true,
  "text-to-speech": false,
  "move-analysis": true,
  "depth-bar": true,
  "evaluation-bar": true,
  "highmatechance": false
};

// Load custom URLs from storage
function loadStoredUrls(callback) {
  chrome.storage.local.get(['serverUrl', 'wsUrl'], function(result) {
    if (result.serverUrl) {
      DefaultExtensionOptions["server-url"] = result.serverUrl;
    }
    if (result.wsUrl) {
      DefaultExtensionOptions["url-api-stockfish"] = result.wsUrl;
    }
    if (callback) callback();
  });
}

// Inject the main chess analysis script
function injectScript(file) {
  let script = document.createElement("script");
  script.src = chrome.runtime.getURL(file);
  let doc = document.head || document.documentElement;
  doc.insertBefore(script, doc.firstElementChild);
  script.onload = function () {
    script.remove();
  };
}

// Enhanced message handling for server communication
chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
  if (request.data !== "popout") {
    window.dispatchEvent(
      new CustomEvent("BetterMintUpdateOptions", {
        detail: request.data,
      })
    );
  } else if (request.data == "popout") {
    window.postMessage("popout");
  }
});

// Enhanced options handler that communicates with server
window.addEventListener("BetterMintGetOptions", function (evt) {
  let request = evt.detail;
  const serverUrl = DefaultExtensionOptions["server-url"];
  
  // Try to get options from server first, fallback to defaults
  fetch(`${serverUrl}/api/settings`)
    .then(response => response.json())
    .then(serverOptions => {
      let response = {
        requestId: request.id,
        data: { ...DefaultExtensionOptions, ...serverOptions },
        source: 'server'
      };
      window.dispatchEvent(
        new CustomEvent("BetterMintSendOptions", {
          detail: response,
        })
      );
    })
    .catch(error => {
      console.log('BetterMint Modded: Server not available, using defaults');
      // Fallback to defaults if server is not available
      let response = {
        requestId: request.id,
        data: DefaultExtensionOptions,
        source: 'default'
      };
      window.dispatchEvent(
        new CustomEvent("BetterMintSendOptions", {
          detail: response,
        })
      );
    });
});

// Server status monitoring
let serverStatusIndicator = null;

function createServerStatusIndicator() {
  if (serverStatusIndicator) return;
  
  serverStatusIndicator = document.createElement('div');
  serverStatusIndicator.className = 'bettermint-server-status bettermint-connecting';
  serverStatusIndicator.textContent = 'Connecting to BetterMint Server...';
  
  // Add styles
  const style = document.createElement('style');
  style.textContent = `
    .bettermint-server-status {
      position: fixed;
      top: 10px;
      right: 10px;
      padding: 8px 16px;
      border-radius: 4px;
      font-family: 'Montserrat', Arial, sans-serif;
      font-size: 12px;
      font-weight: 500;
      z-index: 10000;
      transition: opacity 0.3s;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .bettermint-connecting {
      background: #f39c12;
      color: #ffffff;
    }
    .bettermint-connected {
      background: #27ae60;
      color: #ffffff;
    }
    .bettermint-disconnected {
      background: #e74c3c;
      color: #ffffff;
    }
  `;
  
  if (!document.querySelector('style[data-bettermint-status]')) {
    style.setAttribute('data-bettermint-status', 'true');
    document.head.appendChild(style);
  }
  
  document.body.appendChild(serverStatusIndicator);
}

function updateServerStatus(status) {
  if (!serverStatusIndicator) createServerStatusIndicator();
  
  switch (status) {
    case 'connected':
      serverStatusIndicator.className = 'bettermint-server-status bettermint-connected';
      serverStatusIndicator.textContent = 'BetterMint Server Connected';
      break;
    case 'connecting':
      serverStatusIndicator.className = 'bettermint-server-status bettermint-connecting';
      serverStatusIndicator.textContent = 'Connecting to BetterMint Server...';
      break;
    case 'disconnected':
      serverStatusIndicator.className = 'bettermint-server-status bettermint-disconnected';
      serverStatusIndicator.textContent = 'BetterMint Server Disconnected';
      break;
  }
  
  // Auto-hide after 3 seconds if connected
  if (status === 'connected') {
    setTimeout(() => {
      if (serverStatusIndicator && serverStatusIndicator.className.includes('bettermint-connected')) {
        serverStatusIndicator.style.opacity = '0';
        setTimeout(() => {
          if (serverStatusIndicator) {
            serverStatusIndicator.remove();
            serverStatusIndicator = null;
          }
        }, 300);
      }
    }, 3000);
  }
}

// Monitor server connection
function monitorServerConnection() {
  const serverUrl = DefaultExtensionOptions["server-url"];
  
  fetch(`${serverUrl}/health`)
    .then(response => response.json())
    .then(data => {
      if (data.status === 'healthy') {
        updateServerStatus('connected');
      } else {
        updateServerStatus('connecting');
      }
    })
    .catch(error => {
      updateServerStatus('disconnected');
    });
}

// Listen for URL changes from popup
chrome.storage.onChanged.addListener(function(changes, namespace) {
  if (namespace === 'local') {
    if (changes.serverUrl) {
      DefaultExtensionOptions["server-url"] = changes.serverUrl.newValue;
      console.log('Server URL updated to:', changes.serverUrl.newValue);
    }
    if (changes.wsUrl) {
      DefaultExtensionOptions["url-api-stockfish"] = changes.wsUrl.newValue;
      console.log('WebSocket URL updated to:', changes.wsUrl.newValue);
    }
    // Re-check connection with new URLs
    monitorServerConnection();
  }
});

// Initialize with stored URLs, then inject script
loadStoredUrls(function() {
  console.log('BetterMint Modded: Loaded URLs', {
    serverUrl: DefaultExtensionOptions["server-url"],
    wsUrl: DefaultExtensionOptions["url-api-stockfish"]
  });
  
  // Inject the main Mint.js script
  injectScript("js/Mint.js");
  
  // Initialize monitoring when page loads
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setTimeout(monitorServerConnection, 1000);
      setInterval(monitorServerConnection, 15000);
    });
  } else {
    setTimeout(monitorServerConnection, 1000);
    setInterval(monitorServerConnection, 15000);
  }
});
