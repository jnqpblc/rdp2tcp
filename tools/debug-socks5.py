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
import struct
import sys
import time

def debug_socks5(host='127.0.0.1', port=19050):
    """Debug SOCKS5 connection step by step"""
    
    print(f"🔍 Debugging SOCKS5 connection to {host}:{port}")
    print("=" * 50)
    
    try:
        # Step 1: Connect to SOCKS5 proxy
        print("1. Connecting to SOCKS5 proxy...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        print("   ✓ Connected successfully")
        
        # Step 2: SOCKS5 handshake
        print("\n2. Sending SOCKS5 handshake...")
        handshake = b'\x05\x01\x00'  # VER=5, NMETHODS=1, METHOD=0 (no auth)
        print(f"   Sending: {handshake.hex()}")
        sock.send(handshake)
        
        # Step 3: Receive handshake response
        print("\n3. Waiting for handshake response...")
        response = sock.recv(2)
        print(f"   Received: {response.hex()}")
        
        if len(response) == 0:
            print("   ✗ No response received - connection closed")
            return False
            
        if len(response) < 2:
            print(f"   ✗ Incomplete response: {response.hex()}")
            return False
            
        ver, method = struct.unpack('!BB', response)
        print(f"   Version: {ver}, Method: {method}")
        
        if ver != 5:
            print(f"   ✗ Wrong SOCKS version: {ver}")
            return False
            
        if method != 0:
            print(f"   ✗ Authentication required: {method}")
            return False
            
        print("   ✓ SOCKS5 handshake successful")
        
        # Step 4: Send connect request
        print("\n4. Sending connect request...")
        target_host = "ifconfig.io"
        target_port = 80
        
        # Build connect request: VER=5, CMD=1 (CONNECT), RSV=0, ATYPE=3 (domain), DST.ADDR, DST.PORT
        domain = target_host.encode()
        connect_req = struct.pack('!BBBB', 5, 1, 0, 3) + struct.pack('B', len(domain)) + domain + struct.pack('!H', target_port)
        print(f"   Target: {target_host}:{target_port}")
        print(f"   Sending: {connect_req.hex()}")
        sock.send(connect_req)
        
        # Step 5: Receive connect response
        print("\n5. Waiting for connect response...")
        response = sock.recv(10)
        print(f"   Received: {response.hex()}")
        
        if len(response) == 0:
            print("   ✗ No response received - connection closed")
            return False
            
        if len(response) < 4:
            print(f"   ✗ Incomplete response: {response.hex()}")
            return False
            
        ver, rep, rsv, atyp = struct.unpack('!BBBB', response[:4])
        print(f"   Version: {ver}, Reply: {rep}, RSV: {rsv}, ATYPE: {atyp}")
        
        if rep != 0:
            error_codes = {
                1: "General SOCKS server failure",
                2: "Connection not allowed by ruleset",
                3: "Network unreachable",
                4: "Host unreachable",
                5: "Connection refused",
                6: "TTL expired",
                7: "Command not supported",
                8: "Address type not supported"
            }
            error_msg = error_codes.get(rep, f"Unknown error {rep}")
            print(f"   ✗ SOCKS5 connect failed: {error_msg}")
            return False
            
        print("   ✓ SOCKS5 connect successful")
        
        # Step 6: Send HTTP request
        print("\n6. Sending HTTP request...")
        http_request = f"GET /ip HTTP/1.1\r\nHost: {target_host}\r\nConnection: close\r\n\r\n".encode()
        sock.send(http_request)
        
        # Step 7: Receive HTTP response
        print("\n7. Receiving HTTP response...")
        response = sock.recv(1024)
        print(f"   Received {len(response)} bytes")
        print(f"   Response: {response.decode()[:200]}...")
        
        sock.close()
        print("\n🎉 SOCKS5 proxy is working correctly!")
        return True
        
    except socket.timeout:
        print("   ✗ Connection timeout")
        return False
    except ConnectionResetError:
        print("   ✗ Connection reset by peer")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

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
    except:
        print(f"✗ Port {port} is closed")
        test_different_ports()
        return
    
    # Debug SOCKS5
    success = debug_socks5(port=port)
    
    if not success:
        print("\n❌ SOCKS5 debugging failed")
        print("\nPossible issues:")
        print("1. RDP2TCP server not running on remote machine")
        print("2. SOCKS5 implementation issue in RDP2TCP")
        print("3. Network connectivity problems")
        print("4. Firewall blocking the connection")

if __name__ == '__main__':
    main()
