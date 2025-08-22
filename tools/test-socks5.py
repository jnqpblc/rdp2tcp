#!/usr/bin/env python3
"""
Test script to verify the SOCKS5 fix
"""

import sys
import socket
import struct
import time

def test_socks5_handshake(host='127.0.0.1', port=19050):
    """Test SOCKS5 handshake with detailed debugging"""
    
    print(f"🔍 Testing SOCKS5 handshake to {host}:{port}")
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
            
        print("   ✓ SOCKS5 handshake successful!")
        
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
            
        print("   ✓ SOCKS5 connect successful!")
        
        # Step 6: Send HTTP request
        print("\n6. Sending HTTP request...")
        http_request = f"GET /ip HTTP/1.1\r\nHost: {target_host}\r\nConnection: close\r\n\r\n".encode()
        sock.send(http_request)
        
        # Step 7: Receive HTTP response
        print("\n7. Receiving HTTP response...")
        response = sock.recv(1024)
        print(f"   Received {len(response)} bytes")
        
        if response:
            print(f"   ✓ HTTP response received: {response[:100].decode('utf-8', errors='ignore')}...")
        else:
            print("   ✗ No HTTP response received")
            return False
        
        sock.close()
        print("\n🎉 SOCKS5 test successful!")
        return True
        
    except Exception as e:
        print(f"   ✗ SOCKS5 test failed: {e}")
        return False

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
