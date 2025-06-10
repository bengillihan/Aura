import os

# Authorized email for access control
ALLOWED_EMAIL = os.environ.get("ALLOWED_EMAIL", "Bdgillihan@gmail.com")

# Configuration for managed services
# Each service should have a name and path to its directory
MANAGED_SERVICES = {
    "podcastpal.service": {
        "name": "PodcastPal",
        "path": "/home/ubuntu/podcastpal",
        "description": "Podcast management service"
    },
    "webserver.service": {
        "name": "Web Server", 
        "path": "/home/ubuntu/webserver",
        "description": "Main web server application"
    },
    # Add more services as needed
    # "myapp.service": {
    #     "name": "My Application",
    #     "path": "/path/to/myapp",
    #     "description": "Description of my application"
    # }
}

# Terminal shortcuts - predefined commands for quick access
TERMINAL_SHORTCUTS = [
    {
        "name": "List Services",
        "command": "sudo systemctl list-units --type=service --state=active"
    },
    {
        "name": "System Resources",
        "command": "htop"
    },
    {
        "name": "Disk Usage",
        "command": "df -h"
    },
    {
        "name": "System Logs",
        "command": "sudo journalctl -f"
    },
    {
        "name": "Check PodcastPal Logs",
        "command": "sudo journalctl -u podcastpal.service -f"
    }
]
