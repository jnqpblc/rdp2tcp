#!/usr/bin/env python3
"""
/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
Detailed SOCKS5 debugging script
"""

import socket
import sys

from socks5_util import (socks5_handshake, build_connect_request,
                         read_socks5_reply, SOCKS5Error)

def debug_socks5(host='127.0.0.1', port=19050):
    """Debug SOCKS5 connection step by step"""

    print(f"🔍 Debugging SOCKS5 connection to {host}:{port}")
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
        print("   ✓ SOCKS5 handshake successful")

        # Step 4: Send connect request
        print("\n4. Sending connect request...")
        target_host = "ifconfig.io"
        target_port = 80
        sock.sendall(build_connect_request(target_host, target_port))
        print(f"   Target: {target_host}:{target_port}")

        # Step 5: Receive connect response (length determined by ATYP)
        print("\n5. Reading connect response...")
        reply = read_socks5_reply(sock)
        print(f"   Reply OK: bound to {reply['addr']}:{reply['port']}")

        # Step 6: Send HTTP request
        print("\n6. Sending HTTP request...")
        http_request = f"GET /ip HTTP/1.1\r\nHost: {target_host}\r\nConnection: close\r\n\r\n".encode()
        sock.sendall(http_request)

        # Step 7: Receive HTTP response
        print("\n7. Receiving HTTP response...")
        response = sock.recv(1024)
        print(f"   Received {len(response)} bytes")
        print(f"   Response: {response.decode('utf-8', errors='ignore')[:200]}...")

        print("\n🎉 SOCKS5 proxy is working correctly!")
        return True

    except SOCKS5Error as e:
        print(f"   ✗ SOCKS5 error: {e}")
        return False
    except socket.timeout:
        print("   ✗ Connection timeout")
        return False
    except ConnectionResetError:
        print("   ✗ Connection reset by peer")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    finally:
        if sock is not None:
            sock.close()

def test_different_ports():
    """Test different common SOCKS5 ports"""
    ports = [1080, 19050, 9050, 1081, 1082]
    
    print("🔍 Testing common SOCKS5 ports...")
    print("=" * 50)
    
    for port in ports:
        print(f"\nTesting port {port}:")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect(('127.0.0.1', port))
            print(f"  ✓ Port {port} is open")
            sock.close()
        except:
            print(f"  ✗ Port {port} is closed")

def main():
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 19050
        
    print("SOCKS5 Debug Tool")
    print("=" * 50)
    
    # Test if port is open
    print(f"Checking if port {port} is open...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect(('127.0.0.1', port))
        sock.close()
        print(f"✓ Port {port} is open")
    except OSError:
        print(f"✗ Port {port} is closed")
        test_different_ports()
        return False

    # Debug SOCKS5
    success = debug_socks5(port=port)

    if not success:
        print("\n❌ SOCKS5 debugging failed")
        print("\nPossible issues:")
        print("1. RDP2TCP server not running on remote machine")
        print("2. SOCKS5 implementation issue in RDP2TCP")
        print("3. Network connectivity problems")
        print("4. Firewall blocking the connection")

    return success

if __name__ == '__main__':
    sys.exit(0 if main() else 1)
