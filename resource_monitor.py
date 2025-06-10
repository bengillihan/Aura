import psutil
import subprocess
import re

class ResourceMonitor:
    def __init__(self):
        pass
    
    def get_system_usage(self):
        """Get overall system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'cores': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'used': memory.used,
                    'percent': memory.percent,
                    'available': memory.available
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'percent': (disk.used / disk.total) * 100,
                    'free': disk.free
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_service_usage(self, service_name):
        """Get resource usage for a specific service"""
        try:
            # Get the main PID of the service
            result = subprocess.run(
                ['sudo', 'systemctl', 'show', service_name, '--property=MainPID'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {'error': f'Failed to get service info: {result.stderr}'}
            
            # Parse MainPID
            main_pid_match = re.search(r'MainPID=(\d+)', result.stdout)
            if not main_pid_match or main_pid_match.group(1) == '0':
                return {'status': 'not_running', 'cpu': 0, 'memory': 0}
            
            main_pid = int(main_pid_match.group(1))
            
            # Get process info
            try:
                process = psutil.Process(main_pid)
                
                # Get CPU and memory usage
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                
                # Get all child processes
                children = process.children(recursive=True)
                total_cpu = cpu_percent
                total_memory = memory_info.rss
                
                for child in children:
                    try:
                        total_cpu += child.cpu_percent()
                        total_memory += child.memory_info().rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                return {
                    'status': 'running',
                    'pid': main_pid,
                    'cpu': total_cpu,
                    'memory': total_memory,
                    'memory_percent': (total_memory / psutil.virtual_memory().total) * 100,
                    'children_count': len(children)
                }
            
            except psutil.NoSuchProcess:
                return {'status': 'not_running', 'cpu': 0, 'memory': 0}
            except psutil.AccessDenied:
                return {'error': 'Access denied to process information'}
        
        except Exception as e:
            return {'error': str(e)}
    
    def format_bytes(self, bytes_value):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
