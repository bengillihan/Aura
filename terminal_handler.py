import pty
import os
import select
import subprocess
import threading
import termios
import struct
import fcntl
from flask_socketio import emit

class TerminalHandler:
    def __init__(self, socketio):
        self.socketio = socketio
        self.terminals = {}  # user_id -> terminal_info
    
    def handle_connect(self, user_id):
        """Handle a new WebSocket connection for terminal"""
        try:
            # Create a new pty
            master_fd, slave_fd = pty.openpty()
            
            # Start shell process
            shell_process = subprocess.Popen(
                ['/bin/bash'],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                preexec_fn=os.setsid
            )
            
            # Store terminal info
            self.terminals[user_id] = {
                'master_fd': master_fd,
                'slave_fd': slave_fd,
                'process': shell_process,
                'thread': None
            }
            
            # Start output reading thread
            thread = threading.Thread(
                target=self._read_output,
                args=(user_id, master_fd),
                daemon=True
            )
            thread.start()
            self.terminals[user_id]['thread'] = thread
            
            # Send initial prompt
            emit('terminal_output', {'data': 'Aura Terminal Ready\r\n$ '})
            
        except Exception as e:
            emit('terminal_output', {'data': f'Error starting terminal: {str(e)}\r\n'})
    
    def handle_disconnect(self, user_id):
        """Handle WebSocket disconnection"""
        if user_id in self.terminals:
            terminal_info = self.terminals[user_id]
            
            # Terminate the shell process
            try:
                terminal_info['process'].terminate()
                terminal_info['process'].wait(timeout=5)
            except:
                try:
                    terminal_info['process'].kill()
                except:
                    pass
            
            # Close file descriptors
            try:
                os.close(terminal_info['master_fd'])
                os.close(terminal_info['slave_fd'])
            except:
                pass
            
            # Remove from terminals dict
            del self.terminals[user_id]
    
    def handle_input(self, user_id, data):
        """Handle input from the web terminal"""
        if user_id not in self.terminals:
            return
        
        try:
            input_data = data.get('data', '')
            master_fd = self.terminals[user_id]['master_fd']
            
            # Write input to the pty
            os.write(master_fd, input_data.encode('utf-8'))
            
        except Exception as e:
            emit('terminal_output', {'data': f'Error writing to terminal: {str(e)}\r\n'})
    
    def handle_resize(self, user_id, data):
        """Handle terminal resize"""
        if user_id not in self.terminals:
            return
        
        try:
            rows = data.get('rows', 24)
            cols = data.get('cols', 80)
            master_fd = self.terminals[user_id]['master_fd']
            
            # Set terminal size
            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))
            
        except Exception as e:
            print(f"Error resizing terminal: {str(e)}")
    
    def _read_output(self, user_id, master_fd):
        """Read output from the pty and send to client"""
        try:
            while user_id in self.terminals:
                # Check if data is available to read
                ready, _, _ = select.select([master_fd], [], [], 0.1)
                
                if ready:
                    try:
                        data = os.read(master_fd, 1024)
                        if data:
                            output = data.decode('utf-8', errors='ignore')
                            self.socketio.emit('terminal_output', {'data': output})
                        else:
                            break
                    except OSError:
                        break
                
        except Exception as e:
            self.socketio.emit('terminal_output', {'data': f'Terminal error: {str(e)}\r\n'})
        
        # Clean up if we exit the loop
        if user_id in self.terminals:
            self.handle_disconnect(user_id)
    
    def send_shortcut_command(self, user_id, command):
        """Send a predefined command to the terminal"""
        if user_id not in self.terminals:
            return
        
        try:
            master_fd = self.terminals[user_id]['master_fd']
            
            # Clear current line and send command
            clear_line = '\x15'  # Ctrl+U to clear line
            command_with_enter = f"{clear_line}{command}\n"
            
            os.write(master_fd, command_with_enter.encode('utf-8'))
            
        except Exception as e:
            emit('terminal_output', {'data': f'Error sending command: {str(e)}\r\n'})
