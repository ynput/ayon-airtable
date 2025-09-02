"""Main entry point for the leecher service.

This module imports and runs the service_main function from listener.
"""

from .listener import service_main

if __name__ == "__main__":
    service_main()
