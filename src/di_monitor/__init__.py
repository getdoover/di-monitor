from pydoover.docker import run_app

from .application import DiMonitorApplication


def main():
    """Run the application."""
    run_app(DiMonitorApplication())
