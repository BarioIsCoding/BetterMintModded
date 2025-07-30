"use strict";

// BetterMint Modded - Simplified Content Script Loader
// All settings management is now handled server-side

// Default configuration - will be overridden by server
let DefaultExtensionOptions = {
  "url-api-stockfish": "ws://localhost:8000/ws",
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
  // Try to get options from server first, fallback to defaults
  fetch('http://localhost:8000/api/settings')
    .then(response => response.json())
    .then(serverOptions => {
      let request = evt.detail;
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
      let request = evt.detail;
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
  serverStatusIndicator.className = 'server-status connecting';
  serverStatusIndicator.textContent = 'Connecting to BetterMint Server...';
  document.body.appendChild(serverStatusIndicator);
}

function updateServerStatus(status) {
  if (!serverStatusIndicator) createServerStatusIndicator();
  
  switch (status) {
    case 'connected':
      serverStatusIndicator.className = 'server-status connected';
      serverStatusIndicator.textContent = 'BetterMint Server Connected';
      break;
    case 'connecting':
      serverStatusIndicator.className = 'server-status connecting';
      serverStatusIndicator.textContent = 'Connecting to BetterMint Server...';
      break;
    case 'disconnected':
      serverStatusIndicator.className = 'server-status disconnected';
      serverStatusIndicator.textContent = 'BetterMint Server Disconnected';
      break;
  }
  
  // Auto-hide after 3 seconds if connected
  if (status === 'connected') {
    setTimeout(() => {
      if (serverStatusIndicator && serverStatusIndicator.className.includes('connected')) {
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
  fetch('http://localhost:8000/health')
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

// Initialize monitoring when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    setTimeout(monitorServerConnection, 1000);
    setInterval(monitorServerConnection, 10000);
  });
} else {
  setTimeout(monitorServerConnection, 1000);
  setInterval(monitorServerConnection, 10000);
}

// Inject the main Mint.js script
injectScript("js/Mint.js");