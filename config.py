import os

# Authorized email for access control
ALLOWED_EMAIL = os.environ.get("ALLOWED_EMAIL", "Bdgillihan@gmail.com")

# Configuration for managed services
# Each service should have a name, path, and subdomain information
MANAGED_SERVICES = {
    "podcastpal.service": {
        "name": "PodcastPal",
        "path": "/home/ubuntu/podcastpal",
        "description": "Podcast management service",
        "subdomain": "podcastpal.bengillihan.com",
        "port": 3000
    },
    "timeblocker.service": {
        "name": "TimeBlocker", 
        "path": "/home/ubuntu/timeblocker",
        "description": "Time management application",
        "subdomain": "timeblocker.bengillihan.com",
        "port": 3001
    },
    "aura.service": {
        "name": "Aura Dashboard",
        "path": "/home/ubuntu/aura",
        "description": "Server administration dashboard",
        "subdomain": "aura.bengillihan.com",
        "port": 5000
    },
    # Add more services as needed
    # "myapp.service": {
    #     "name": "My Application",
    #     "path": "/path/to/myapp",
    #     "description": "Description of my application",
    #     "subdomain": "myapp.bengillihan.com",
    #     "port": 3002
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
