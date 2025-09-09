from pydoover.docker import run_app

from .application import DiMonitorApplication
from .app_config import DiMonitorConfig

def main():
    """
    Run the application.
    """
    run_app(DiMonitorApplication(config=DiMonitorConfig()))
