#!/usr/bin/env python3
"""
Test script for the shell (process) tunnel functionality.

Integration test: requires a live rdp2tcp controller and RDP session. Opt in
with RDP2TCP_RUN_INTEGRATION=1 (or --run).
"""

import importlib.util
import os
import socket
import sys
import time

from testutil import require_integration

CLI_FILENAME = "rdp2tcp-cli.py"


def load_cli_class():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = os.getcwd()
    cli_paths = [
        os.path.join(script_dir, CLI_FILENAME),
        os.path.join(current_dir, CLI_FILENAME),
        os.path.join(current_dir, "tools", CLI_FILENAME),
    ]
    for path in cli_paths:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("rdp2tcp_cli", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"Found CLI file at: {path}")
            return module.RDP2TCPEnhancedCLI
    raise ImportError(f"Could not find {CLI_FILENAME}")


def test_shell_connection():
    """Create a shell tunnel and verify we can reach the local listener."""
    try:
        cli_class = load_cli_class()
    except Exception as e:
        print(f"✗ Failed to import CLI: {e}")
        return False

    print("Testing Shell Tunnel")
    print("=" * 30)

    cli = cli_class()
    cli.setup_logging()

    print("\n1. Creating shell tunnel...")
    if not cli.shell_tunnel(local_port=4447, command='cmd.exe',
                            args=None, auto_connect=False):
        print("✗ Failed to create shell tunnel")
        return False
    print("✓ Shell tunnel created successfully")

    time.sleep(1)

    print("\n2. Testing local listener reachability...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        sock.connect(('127.0.0.1', 4447))
        # The far side is a Windows shell; it may or may not emit a banner.
        # Reaching the listener and not being refused is the signal we check.
        print("✓ Connected to shell tunnel listener on 127.0.0.1:4447")
        return True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"✗ Could not reach shell tunnel listener: {e}")
        return False
    finally:
        sock.close()


def main():
    require_integration('test-shell.py')

    print("Shell Tunnel Test")
    print("=" * 25)

    if not test_shell_connection():
        print("\n❌ Shell connection test failed!")
        return 1

    print("\n🎉 Shell tunnel test completed successfully!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
