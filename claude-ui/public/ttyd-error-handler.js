// Global error handler for ttyd WebSocket and fetch errors
// These errors are normal when ttyd reconnects to TMUX sessions

(function() {
  // Store the original console.error to filter messages
  const originalConsoleError = console.error;
  console.error = function(...args) {
    // Filter out ttyd WebSocket errors
    const errorString = args.join(' ');
    if (errorString.includes('WebSocket connection to') &&
        errorString.includes('localhost:809') &&
        (errorString.includes('/ws') || errorString.includes('failed'))) {
      // Suppress ttyd WebSocket errors silently
      return;
    }
    return originalConsoleError.apply(console, args);
  };

  // Store original WebSocket constructor
  const OriginalWebSocket = window.WebSocket;

  // Override WebSocket to add error handling
  window.WebSocket = function(url, protocols) {
    // If it's a ttyd WebSocket, handle it specially
    if (url && url.includes('localhost:809')) {
      try {
        const ws = new OriginalWebSocket(url, protocols);

        // Suppress all ttyd WebSocket errors
        ws.addEventListener('error', function(event) {
          event.stopImmediatePropagation();
          event.preventDefault();
          return false;
        }, true);

        ws.addEventListener('close', function(event) {
          if (event.code >= 4000) {
            event.stopImmediatePropagation();
            event.preventDefault();
            return false;
          }
        }, true);

        // Override onerror to prevent propagation
        const originalOnerror = ws.onerror;
        ws.onerror = function(event) {
          // Silently ignore ttyd errors
          return false;
        };

        return ws;
      } catch (e) {
        // If WebSocket creation fails, return a mock object
        console.log('ttyd WebSocket creation intercepted for', url);
        return {
          send: () => {},
          close: () => {},
          addEventListener: () => {},
          removeEventListener: () => {},
          readyState: 3,
          CONNECTING: 0,
          OPEN: 1,
          CLOSING: 2,
          CLOSED: 3
        };
      }
    }

    // For non-ttyd WebSockets, use original
    return new OriginalWebSocket(url, protocols);
  };

  // Copy static properties
  Object.setPrototypeOf(window.WebSocket, OriginalWebSocket);
  Object.setPrototypeOf(window.WebSocket.prototype, OriginalWebSocket.prototype);
  for (let prop in OriginalWebSocket) {
    if (OriginalWebSocket.hasOwnProperty(prop)) {
      window.WebSocket[prop] = OriginalWebSocket[prop];
    }
  }

  // Also intercept fetch errors for ttyd token requests
  const originalFetch = window.fetch;
  window.fetch = function(...args) {
    const url = args[0];
    if (typeof url === 'string' && url.includes('localhost:809') && url.includes('/token')) {
      // This is a ttyd token request, handle errors gracefully
      return originalFetch.apply(this, args).catch(err => {
        // Silently return mock response
        return Promise.resolve(new Response('{}', {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        }));
      });
    }
    return originalFetch.apply(this, args);
  };

  // Global error handler for unhandled errors
  window.addEventListener('error', function(event) {
    if (event.message &&
        (event.message.includes('WebSocket') || event.message.includes('ws://localhost:809'))) {
      event.preventDefault();
      event.stopPropagation();
      return false;
    }
  }, true);

  // Suppress unhandled promise rejections from ttyd
  window.addEventListener('unhandledrejection', function(event) {
    if (event.reason && event.reason.toString().includes('localhost:809')) {
      event.preventDefault();
      return false;
    }
  }, true);
})();