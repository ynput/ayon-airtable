"""Main entry point for AYON Airtable service tools.

This module provides command-line interfaces to run processor, leecher, and transmitter services,
as well as a utility to run all services concurrently.
"""

import argparse
import logging
import os
import subprocess
import sys
import time

from ayon_api.constants import (
    DEFAULT_VARIANT_ENV_KEY,
)

ADDON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_all():
    """Run all three services (leecher, processor, transmitter) concurrently."""
    all_idx = sys.argv.index("all")
    leecher_args = list(sys.argv)
    processor_args = list(sys.argv)
    transmitter_args = list(sys.argv)

    leecher_args[all_idx] = "leecher"
    processor_args[all_idx] = "processor"
    transmitter_args[all_idx] = "transmitter"

    leecher_args.insert(0, sys.executable)
    processor_args.insert(0, sys.executable)
    transmitter_args.insert(0, sys.executable)

    leecher = subprocess.Popen(leecher_args)
    processor = subprocess.Popen(processor_args)
    transmitter = subprocess.Popen(transmitter_args)
    try:
        while True:
            l_poll = leecher.poll()
            p_poll = processor.poll()
            t_poll = transmitter.poll()
            if (
                l_poll is not None
                and p_poll is not None
                and t_poll is not None
            ):
                break

            if (
                l_poll is not None
                or p_poll is not None
                or t_poll is not None
            ):
                if l_poll is not None:
                    leecher.kill()
                if p_poll is not None:
                    processor.kill()
                if t_poll is not None:
                    transmitter.kill()

            time.sleep(0.1)
    finally:
        if leecher.poll() is None:
            leecher.kill()

        if processor.poll() is None:
            processor.kill()

        if transmitter.poll() is None:
            transmitter.kill()


def main() -> None:
    """Parse arguments and run the specified AYON Airtable service.

    Parses command-line arguments to determine which service to run
    (processor, leecher, transmitter, or all), sets the appropriate
    environment variable for the settings variant, and executes the
    selected service.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--service",
        help="Run processor service",
        choices=["processor", "leecher", "transmitter", "all"],
    )
    parser.add_argument(
        "--variant",
        default="production",
        help="Settings variant",
    )
    opts = parser.parse_args()
    if opts.variant:
        os.environ[DEFAULT_VARIANT_ENV_KEY] = opts.variant

    service_name = opts.service
    if service_name == "all":
        return run_all()

    for path in (
        os.path.join(ADDON_DIR, "services", service_name),
    ):
        sys.path.insert(0, path)

    if service_name == "processor":
        from processor import service_main

        service_main()

    elif service_name == "leecher":
        from leecher import service_main

        service_main()

    else:
        from transmitter import service_main

        service_main()

    return None


if __name__ == "__main__":
    logging.basicConfig()
    main()
