#!/usr/bin/env python3
"""
Test script to verify the SOCKS5 fix
"""

import sys
import socket

from socks5_util import (socks5_handshake, build_connect_request,
                         read_socks5_reply, SOCKS5Error)
from testutil import require_integration

def test_socks5_handshake(host='127.0.0.1', port=19050):
    """Test SOCKS5 handshake with detailed debugging"""

    print(f"🔍 Testing SOCKS5 handshake to {host}:{port}")
    print("=" * 50)

    sock = None
    try:
        # Step 1: Connect to SOCKS5 proxy
        print("1. Connecting to SOCKS5 proxy...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        print("   ✓ Connected successfully")

        # Step 2+3: SOCKS5 handshake (reads exactly the 2-byte method reply)
        print("\n2. Performing SOCKS5 handshake...")
        socks5_handshake(sock)
        print("   ✓ SOCKS5 handshake successful!")

        # Step 4: Send connect request
        print("\n4. Sending connect request...")
        target_host = "ifconfig.io"
        target_port = 80
        sock.sendall(build_connect_request(target_host, target_port))
        print(f"   Target: {target_host}:{target_port}")

        # Step 5: Receive connect response (length determined by ATYP)
        print("\n5. Reading connect response...")
        reply = read_socks5_reply(sock)
        print(f"   ✓ SOCKS5 connect successful (bound {reply['addr']}:{reply['port']})")

        # Step 6: Send HTTP request
        print("\n6. Sending HTTP request...")
        http_request = f"GET /ip HTTP/1.1\r\nHost: {target_host}\r\nConnection: close\r\n\r\n".encode()
        sock.sendall(http_request)

        # Step 7: Receive HTTP response
        print("\n7. Receiving HTTP response...")
        response = sock.recv(1024)
        print(f"   Received {len(response)} bytes")

        if not response:
            print("   ✗ No HTTP response received")
            return False
        print(f"   ✓ HTTP response received: {response[:100].decode('utf-8', errors='ignore')}...")

        print("\n🎉 SOCKS5 test successful!")
        return True

    except SOCKS5Error as e:
        print(f"   ✗ SOCKS5 error: {e}")
        return False
    except Exception as e:
        print(f"   ✗ SOCKS5 test failed: {e}")
        return False
    finally:
        if sock is not None:
            sock.close()

def test_channel_status():
    """Test RDP2TCP channel status"""
    try:
        from rdp2tcp import rdp2tcp, R2TException
        
        print("\nTesting RDP2TCP channel status...")
        r2t = rdp2tcp('127.0.0.1', 8477)
        
        # Get info to check channel status
        info = r2t.info()
        print(f"Channel info: {info}")
        
        # Try to create a simple tunnel to test channel connectivity
        result = r2t.add_tunnel('t', ('127.0.0.1', 8888), ('127.0.0.1', 8889))
        print(f"Tunnel test result: {result}")
        
        # Clean up
        r2t.del_tunnel(('127.0.0.1', 8888))
        r2t.close()
        
        return True
        
    except Exception as e:
        print(f"Channel status test failed: {e}")
        return False

def main():
    require_integration('test-socks5.py')

    print("SOCKS5 Fix Test")
    print("="*30)

    # Test 1: Channel status
    if not test_channel_status():
        print("\n❌ Channel status test failed!")
        return False
    
    # Test 2: SOCKS5 handshake
    if not test_socks5_handshake():
        print("\n❌ SOCKS5 handshake test failed!")
        print("\nThe SOCKS5 fix may not be working properly.")
        print("Check if the RDP2TCP channel is connected.")
        return False
    
    print("\n🎉 All tests passed!")
    print("The SOCKS5 fix is working correctly.")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
