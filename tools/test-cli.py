#!/usr/bin/env python3
"""
/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
Smoke test for the RDP2TCP Enhanced CLI.

This exercises the parts that do NOT require a running controller: importing
the CLI module, constructing it, and loading config. Operations that need a
live controller (tunnel list / config load) are allowed to fail with a
connection error -- but any OTHER failure, or an import/construction error,
makes this script exit non-zero.
"""

import importlib.util
import os
import sys

from rdp2tcp import R2TException

# Add the current directory to the path so we can import the CLI
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_cli_class():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = os.getcwd()

    cli_paths = [
        os.path.join(script_dir, "rdp2tcp-cli.py"),
        os.path.join(current_dir, "rdp2tcp-cli.py"),
        os.path.join(current_dir, "tools", "rdp2tcp-cli.py"),
    ]

    for path in cli_paths:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("rdp2tcp_cli", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"Found CLI file at: {path}")
            return module.RDP2TCPEnhancedCLI

    print("Could not find rdp2tcp-cli.py; checked:")
    for path in cli_paths:
        print(f"  - {path} (exists: {os.path.exists(path)})")
    raise ImportError("rdp2tcp-cli.py not found")


def find_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = os.getcwd()
    for path in [
        os.path.join(script_dir, "config.yaml"),
        os.path.join(current_dir, "config.yaml"),
        os.path.join(current_dir, "tools", "config.yaml"),
    ]:
        if os.path.exists(path):
            return path
    return None


def main():
    try:
        cli_class = load_cli_class()
    except Exception as e:
        print(f"✗ Failed to import CLI: {e}")
        return 1

    print("Testing RDP2TCP Enhanced CLI...")

    config_file = find_config()
    try:
        if config_file:
            print(f"Loading config from {config_file}")
            cli = cli_class(config_file)
        else:
            print("No config.yaml found; testing without config")
            cli = cli_class()
        cli.setup_logging()
        print("CLI initialized successfully!")
    except Exception as e:
        print(f"✗ CLI initialization failed: {e}")
        return 1

    # These require a controller. A connection error is acceptable here (we
    # may not have a live endpoint); anything else is a real failure.
    for label, fn in (("tunnel list", cli.tunnel_list),
                      ("config load", cli.config_load_tunnels)):
        print(f"\nTesting {label}...")
        try:
            fn()
        except R2TException as e:
            print(f"  (controller not reachable, expected without a server: {e})")
        except Exception as e:
            print(f"✗ {label} raised an unexpected error: {e}")
            return 1

    print("\nCLI smoke test completed!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
