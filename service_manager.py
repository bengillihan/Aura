import subprocess
import os
import re
from config import MANAGED_SERVICES

class ServiceManager:
    def __init__(self):
        pass
    
    def _run_systemctl_command(self, command, service_name):
        """Run a systemctl command and return the result"""
        try:
            cmd = f"sudo systemctl {command} {service_name}"
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'command': cmd
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'Command timed out',
                'command': cmd
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'command': cmd
            }
    
    def start_service(self, service_name):
        """Start a systemd service"""
        return self._run_systemctl_command('start', service_name)
    
    def stop_service(self, service_name):
        """Stop a systemd service"""
        return self._run_systemctl_command('stop', service_name)
    
    def restart_service(self, service_name):
        """Restart a systemd service"""
        return self._run_systemctl_command('restart', service_name)
    
    def get_service_status(self, service_name):
        """Get the status of a systemd service"""
        result = self._run_systemctl_command('status', service_name)
        
        if result['success'] or 'Active:' in result['output']:
            # Parse the status output to get state
            output = result['output']
            if 'Active: active (running)' in output:
                status = 'running'
            elif 'Active: inactive (dead)' in output:
                status = 'stopped'
            elif 'Active: failed' in output:
                status = 'failed'
            else:
                status = 'unknown'
            
            result['status'] = status
        else:
            result['status'] = 'unknown'
        
        return result
    
    def get_service_config(self, service_name):
        """Get the current configuration of a service"""
        service_path = f"/etc/systemd/system/{service_name}.service"
        
        try:
            with open(service_path, 'r') as f:
                content = f.read()
            
            # Parse CPU and Memory limits
            cpu_quota = None
            memory_max = None
            
            cpu_match = re.search(r'CPUQuota=(.+)', content)
            if cpu_match:
                cpu_quota = cpu_match.group(1)
            
            memory_match = re.search(r'MemoryMax=(.+)', content)
            if memory_match:
                memory_max = memory_match.group(1)
            
            return {
                'success': True,
                'cpu_quota': cpu_quota,
                'memory_max': memory_max,
                'service_path': service_path
            }
        
        except FileNotFoundError:
            return {
                'success': False,
                'error': f'Service file not found: {service_path}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_service_limits(self, service_name, cpu_quota=None, memory_max=None):
        """Update CPU and memory limits for a service"""
        service_path = f"/etc/systemd/system/{service_name}.service"
        
        try:
            # Read current service file
            with open(service_path, 'r') as f:
                lines = f.readlines()
            
            # Track if we're in the [Service] section
            in_service_section = False
            service_section_found = False
            cpu_updated = False
            memory_updated = False
            
            # Process each line
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                if stripped == '[Service]':
                    in_service_section = True
                    service_section_found = True
                elif stripped.startswith('[') and stripped.endswith(']'):
                    in_service_section = False
                elif in_service_section:
                    # Update existing directives
                    if stripped.startswith('CPUQuota=') and cpu_quota is not None:
                        lines[i] = f'CPUQuota={cpu_quota}\n'
                        cpu_updated = True
                    elif stripped.startswith('MemoryMax=') and memory_max is not None:
                        lines[i] = f'MemoryMax={memory_max}\n'
                        memory_updated = True
            
            # Add missing directives to [Service] section
            if service_section_found:
                service_end_idx = None
                for i, line in enumerate(lines):
                    if line.strip() == '[Service]':
                        # Find the end of the [Service] section
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip().startswith('[') and lines[j].strip().endswith(']'):
                                service_end_idx = j
                                break
                        if service_end_idx is None:
                            service_end_idx = len(lines)
                        break
                
                if service_end_idx is not None:
                    insert_idx = service_end_idx
                    
                    # Add CPU quota if not updated and provided
                    if not cpu_updated and cpu_quota is not None:
                        lines.insert(insert_idx, f'CPUQuota={cpu_quota}\n')
                        insert_idx += 1
                    
                    # Add memory max if not updated and provided
                    if not memory_updated and memory_max is not None:
                        lines.insert(insert_idx, f'MemoryMax={memory_max}\n')
            
            # Write the updated service file
            with open(service_path, 'w') as f:
                f.writelines(lines)
            
            # Reload systemd and restart the service
            reload_result = subprocess.run(
                ['sudo', 'systemctl', 'daemon-reload'],
                capture_output=True,
                text=True
            )
            
            if reload_result.returncode != 0:
                return {
                    'success': False,
                    'error': f'Failed to reload systemd: {reload_result.stderr}'
                }
            
            # Restart the service to apply changes
            restart_result = self.restart_service(service_name)
            
            return {
                'success': True,
                'message': 'Service limits updated successfully',
                'restart_result': restart_result
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
