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
import struct
import sys

def test_socks5_connection(host='127.0.0.1', port=19050, target_host='ifconfig.io', target_port=80):
    """Test SOCKS5 connection"""
    
    print(f"Testing SOCKS5 connection to {host}:{port}")
    print(f"Target: {target_host}:{target_port}")
    
    try:
        # Connect to SOCKS5 proxy
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        print("✓ Connected to SOCKS5 proxy")
        
        # SOCKS5 handshake
        # Send: VER=5, NMETHODS=1, METHOD=0 (no auth)
        sock.send(b'\x05\x01\x00')
        
        # Receive: VER=5, METHOD=0
        response = sock.recv(2)
        if response != b'\x05\x00':
            print(f"✗ SOCKS5 handshake failed: {response.hex()}")
            return False
        print("✓ SOCKS5 handshake successful")
        
        # SOCKS5 connect request
        # Send: VER=5, CMD=1 (CONNECT), RSV=0, ATYPE=3 (domain), DST.ADDR, DST.PORT
        domain = target_host.encode()
        request = struct.pack('!BBBB', 5, 1, 0, 3) + struct.pack('B', len(domain)) + domain + struct.pack('!H', target_port)
        sock.send(request)
        
        # Receive response
        response = sock.recv(10)
        if len(response) < 4:
            print(f"✗ SOCKS5 connect response too short: {response.hex()}")
            return False
            
        ver, rep, rsv, atyp = struct.unpack('!BBBB', response[:4])
        if rep != 0:
            print(f"✗ SOCKS5 connect failed with code: {rep}")
            return False
        print("✓ SOCKS5 connect successful")
        
        # Send HTTP request
        http_request = f"GET /ip HTTP/1.1\r\nHost: {target_host}\r\nConnection: close\r\n\r\n".encode()
        sock.send(http_request)
        
        # Receive response
        response = sock.recv(1024)
        print(f"✓ Received response: {response.decode()[:200]}...")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 19050
        
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

if __name__ == '__main__':
    main()
