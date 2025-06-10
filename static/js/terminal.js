// Terminal JavaScript functionality using Xterm.js and Socket.IO

let terminal;
let socket;
let fitAddon;

function initializeTerminal() {
    // Initialize Socket.IO connection
    socket = io();
    window.socket = socket;
    
    // Initialize xterm.js terminal
    terminal = new Terminal({
        theme: {
            background: '#000000',
            foreground: '#ffffff',
            cursor: '#ffffff',
            selection: '#ffffff40',
            black: '#000000',
            red: '#ff0000',
            green: '#00ff00',
            yellow: '#ffff00',
            blue: '#0000ff',
            magenta: '#ff00ff',
            cyan: '#00ffff',
            white: '#ffffff',
            brightBlack: '#808080',
            brightRed: '#ff8080',
            brightGreen: '#80ff80',
            brightYellow: '#ffff80',
            brightBlue: '#8080ff',
            brightMagenta: '#ff80ff',
            brightCyan: '#80ffff',
            brightWhite: '#ffffff'
        },
        fontFamily: 'Consolas, "Courier New", monospace',
        fontSize: 14,
        lineHeight: 1.2,
        letterSpacing: 0,
        cursorBlink: true,
        cursorStyle: 'block',
        scrollback: 1000,
        rightClickSelectsWord: true
    });
    
    // Initialize fit addon
    fitAddon = new FitAddon.FitAddon();
    terminal.loadAddon(fitAddon);
    
    // Open terminal in the container
    terminal.open(document.getElementById('terminal'));
    
    // Fit terminal to container
    fitAddon.fit();
    
    // Store reference globally
    window.terminal = terminal;
    
    // Set up socket event listeners
    setupSocketListeners();
    
    // Set up terminal event listeners
    setupTerminalListeners();
    
    // Handle window resize
    window.addEventListener('resize', function() {
        setTimeout(() => {
            fitAddon.fit();
            sendTerminalResize();
        }, 100);
    });
    
    // Focus terminal
    terminal.focus();
}

function setupSocketListeners() {
    // Connection established
    socket.on('connect', function() {
        updateConnectionStatus('connected');
        console.log('Terminal WebSocket connected');
    });
    
    // Connection lost
    socket.on('disconnect', function() {
        updateConnectionStatus('disconnected');
        console.log('Terminal WebSocket disconnected');
        terminal.write('\r\n\x1b[31mConnection lost. Please refresh the page.\x1b[0m\r\n');
    });
    
    // Terminal output from server
    socket.on('terminal_output', function(data) {
        if (data.data) {
            terminal.write(data.data);
        }
    });
    
    // Error handling
    socket.on('error', function(error) {
        console.error('Terminal WebSocket error:', error);
        updateConnectionStatus('error');
        terminal.write('\r\n\x1b[31mTerminal error: ' + error + '\x1b[0m\r\n');
    });
}

function setupTerminalListeners() {
    // Handle user input
    terminal.onData(function(data) {
        if (socket && socket.connected) {
            socket.emit('terminal_input', { data: data });
        }
    });
    
    // Handle special key combinations
    terminal.onKey(function(e) {
        const ev = e.domEvent;
        
        // Ctrl+C
        if (ev.ctrlKey && ev.key === 'c') {
            // Let the terminal handle Ctrl+C normally
            return;
        }
        
        // Ctrl+L (clear screen)
        if (ev.ctrlKey && ev.key === 'l') {
            terminal.clear();
            ev.preventDefault();
            return;
        }
        
        // Ctrl+D (EOF)
        if (ev.ctrlKey && ev.key === 'd') {
            // Let the terminal handle Ctrl+D normally
            return;
        }
    });
    
    // Handle terminal resize
    terminal.onResize(function() {
        sendTerminalResize();
    });
}

function updateConnectionStatus(status) {
    const statusElement = document.getElementById('connection-status');
    if (!statusElement) return;
    
    statusElement.className = 'badge';
    
    switch (status) {
        case 'connected':
            statusElement.className += ' bg-success';
            statusElement.innerHTML = '<i class="fas fa-check-circle me-1"></i>Connected';
            break;
        case 'disconnected':
            statusElement.className += ' bg-danger';
            statusElement.innerHTML = '<i class="fas fa-times-circle me-1"></i>Disconnected';
            break;
        case 'error':
            statusElement.className += ' bg-warning';
            statusElement.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Error';
            break;
        default:
            statusElement.className += ' bg-secondary';
            statusElement.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Connecting...';
    }
}

function sendTerminalResize() {
    if (socket && socket.connected && terminal) {
        socket.emit('terminal_resize', {
            rows: terminal.rows,
            cols: terminal.cols
        });
    }
}

// Terminal control functions
function clearTerminal() {
    if (terminal) {
        terminal.clear();
    }
}

function sendCommand(command) {
    if (socket && socket.connected) {
        socket.emit('terminal_input', { data: command + '\n' });
    }
}

function focusTerminal() {
    if (terminal) {
        terminal.focus();
    }
}

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && terminal) {
        // Page became visible, focus terminal
        setTimeout(() => {
            terminal.focus();
        }, 100);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (socket) {
        socket.disconnect();
    }
});

// Export functions for global access
window.clearTerminal = clearTerminal;
window.sendCommand = sendCommand;
window.focusTerminal = focusTerminal;
window.initializeTerminal = initializeTerminal;
