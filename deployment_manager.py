import subprocess
import os
import threading
from config import MANAGED_SERVICES

class DeploymentManager:
    def __init__(self):
        self.deployment_logs = {}
    
    def _run_command_with_output(self, command, cwd=None):
        """Run a command and capture its output"""
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=cwd
            )
            
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                line = line.rstrip()
                output_lines.append(line)
            
            process.wait()
            
            return {
                'success': process.returncode == 0,
                'output': '\n'.join(output_lines),
                'returncode': process.returncode
            }
        
        except Exception as e:
            return {
                'success': False,
                'output': f'Error executing command: {str(e)}',
                'returncode': -1
            }
    
    def deploy_service(self, service_name):
        """Deploy a service by pulling from git and restarting"""
        if service_name not in MANAGED_SERVICES:
            return {'success': False, 'error': 'Service not configured'}
        
        service_config = MANAGED_SERVICES[service_name]
        service_path = service_config['path']
        
        deployment_log = []
        
        def log_step(message):
            deployment_log.append(message)
            print(f"[DEPLOY {service_name}] {message}")
        
        try:
            log_step(f"Starting deployment for {service_name}")
            log_step(f"Service path: {service_path}")
            
            # Check if directory exists
            if not os.path.exists(service_path):
                error_msg = f"Service directory does not exist: {service_path}"
                log_step(f"ERROR: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'log': deployment_log
                }
            
            # Step 1: Git pull
            log_step("Pulling latest code from repository...")
            git_result = self._run_command_with_output("git pull", cwd=service_path)
            log_step(f"Git output: {git_result['output']}")
            
            if not git_result['success']:
                log_step(f"ERROR: Git pull failed")
                return {
                    'success': False,
                    'error': 'Git pull failed',
                    'log': deployment_log
                }
            
            # Step 2: Install dependencies (if requirements.txt exists)
            requirements_path = os.path.join(service_path, 'requirements.txt')
            if os.path.exists(requirements_path):
                log_step("Installing dependencies...")
                
                # Try to find and use virtual environment
                venv_path = None
                possible_venv_paths = [
                    os.path.join(service_path, 'venv'),
                    os.path.join(service_path, '.venv'),
                    os.path.join(service_path, 'env')
                ]
                
                for path in possible_venv_paths:
                    if os.path.exists(os.path.join(path, 'bin', 'pip')):
                        venv_path = path
                        break
                
                if venv_path:
                    pip_command = f"{venv_path}/bin/pip install -r requirements.txt"
                    log_step(f"Using virtual environment: {venv_path}")
                else:
                    pip_command = "pip install -r requirements.txt"
                    log_step("Using system pip (no virtual environment found)")
                
                pip_result = self._run_command_with_output(pip_command, cwd=service_path)
                log_step(f"Pip output: {pip_result['output']}")
                
                if not pip_result['success']:
                    log_step("WARNING: Pip install had issues, continuing with restart...")
            else:
                log_step("No requirements.txt found, skipping dependency installation")
            
            # Step 3: Restart service
            log_step("Restarting service...")
            restart_result = self._run_command_with_output(f"sudo systemctl restart {service_name}")
            log_step(f"Restart output: {restart_result['output']}")
            
            if not restart_result['success']:
                log_step(f"ERROR: Service restart failed")
                return {
                    'success': False,
                    'error': 'Service restart failed',
                    'log': deployment_log
                }
            
            # Step 4: Check service status
            log_step("Checking service status...")
            status_result = self._run_command_with_output(f"sudo systemctl is-active {service_name}")
            log_step(f"Service status: {status_result['output']}")
            
            if status_result['output'].strip() == 'active':
                log_step("✅ Deployment completed successfully!")
                return {
                    'success': True,
                    'message': 'Deployment completed successfully',
                    'log': deployment_log
                }
            else:
                log_step("⚠️ Service may not be running properly")
                return {
                    'success': False,
                    'error': 'Service not active after restart',
                    'log': deployment_log
                }
        
        except Exception as e:
            error_msg = f"Deployment failed with exception: {str(e)}"
            log_step(f"ERROR: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'log': deployment_log
            }
    
    def get_deployment_log(self, service_name):
        """Get the deployment log for a service"""
        return self.deployment_logs.get(service_name, [])
