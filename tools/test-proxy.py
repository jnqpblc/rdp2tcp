#!/usr/bin/env python3
"""
/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */

Simple SOCKS5 test script
"""

import socket
import sys

from socks5_util import (socks5_handshake, build_connect_request,
                         read_socks5_reply, SOCKS5Error)
from testutil import require_integration

def test_socks5_connection(host='127.0.0.1', port=19050, target_host='ifconfig.io', target_port=80):
    """Test SOCKS5 connection"""

    print(f"Testing SOCKS5 connection to {host}:{port}")
    print(f"Target: {target_host}:{target_port}")

    sock = None
    try:
        # Connect to SOCKS5 proxy
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        print("✓ Connected to SOCKS5 proxy")

        # SOCKS5 handshake (reads exactly the method-selection reply)
        socks5_handshake(sock)
        print("✓ SOCKS5 handshake successful")

        # SOCKS5 connect request + framed reply (sized by ATYP)
        sock.sendall(build_connect_request(target_host, target_port))
        reply = read_socks5_reply(sock)
        print(f"✓ SOCKS5 connect successful (bound {reply['addr']}:{reply['port']})")

        # Send HTTP request
        http_request = f"GET /ip HTTP/1.1\r\nHost: {target_host}\r\nConnection: close\r\n\r\n".encode()
        sock.sendall(http_request)

        # Receive response
        response = sock.recv(1024)
        print(f"✓ Received response: {response.decode('utf-8', errors='ignore')[:200]}...")
        return True

    except SOCKS5Error as e:
        print(f"✗ SOCKS5 error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        if sock is not None:
            sock.close()

def main():
    require_integration('test-proxy.py')

    # First positional arg (that is not --run) overrides the port.
    port = 19050
    for arg in sys.argv[1:]:
        if arg != '--run':
            port = int(arg)
            break

    success = test_socks5_connection(port=port)
    if success:
        print("\n🎉 SOCKS5 proxy is working correctly!")
    else:
        print("\n❌ SOCKS5 proxy test failed")
        print("\nTroubleshooting tips:")
        print("1. Make sure RDP2TCP server is running")
        print("2. Check if SOCKS tunnel is created: python3 tools/rdp2tcp-cli.py tunnel list")
        print("3. Verify the tunnel port matches your config")
        print("4. Check if the RDP connection is active")
    return success

if __name__ == '__main__':
    sys.exit(0 if main() else 1)
