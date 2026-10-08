#!/usr/bin/env python3
"""
/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
Simple TCP Tunnel Test
Tests if the RDP2TCP channel is working by creating a simple TCP tunnel
"""

import sys
import socket
import time
import threading

from testutil import require_integration

def create_test_tunnel():
    """Create a simple TCP tunnel for testing"""
    try:
        from rdp2tcp import rdp2tcp, R2TException
        
        print("Creating test TCP tunnel...")
        r2t = rdp2tcp('127.0.0.1', 8477)
        
        # Create a tunnel from local 8888 to remote 8889
        result = r2t.add_tunnel('t', ('127.0.0.1', 8888), ('127.0.0.1', 8889))
        print(f"Tunnel creation result: {result}")
        
        return r2t
        
    except Exception as e:
        print(f"Failed to create tunnel: {e}")
        return None

def start_test_server():
    """Start a simple test server on port 8889"""
    def server():
        try:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('127.0.0.1', 8889))
            server_sock.listen(1)
            print("✓ Test server listening on port 8889")
            
            client_sock, addr = server_sock.accept()
            print(f"✓ Test server accepted connection from {addr}")
            
            # Send test data
            client_sock.send(b"Hello from test server!\n")
            
            # Receive data
            data = client_sock.recv(1024)
            print(f"✓ Test server received: {data.decode().strip()}")
            
            client_sock.close()
            server_sock.close()
            
        except Exception as e:
            print(f"✗ Test server error: {e}")
    
    server_thread = threading.Thread(target=server)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(1)  # Give server time to start

def test_tunnel_connection():
    """Test the tunnel connection"""
    try:
        print("Testing tunnel connection...")
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.settimeout(10)
        client_sock.connect(('127.0.0.1', 8888))
        
        # Send test data
        client_sock.send(b"Hello from tunnel client!\n")
        
        # Receive response
        data = client_sock.recv(1024)
        print(f"✓ Tunnel client received: {data.decode().strip()}")
        
        client_sock.close()
        return True
        
    except Exception as e:
        print(f"✗ Tunnel connection failed: {e}")
        return False

def cleanup_tunnel(r2t):
    """Clean up the test tunnel"""
    try:
        if r2t:
            result = r2t.del_tunnel(('127.0.0.1', 8888))
            print(f"Tunnel cleanup result: {result}")
            r2t.close()
    except Exception as e:
        print(f"Cleanup error: {e}")

def main():
    require_integration('test-tcp-tunnel.py')

    print("TCP Tunnel Test")
    print("="*30)
    print("NOTE: the forward tunnel's target (127.0.0.1:8889) is resolved on")
    print("      the REMOTE (rdp2tcp server) side, while this script's test")
    print("      server listens LOCALLY. This test therefore only passes when")
    print("      the rdp2tcp server runs on this same host (loopback).")
    print()

    # Create tunnel
    r2t = create_test_tunnel()
    if not r2t:
        print("Failed to create tunnel. Channel may not be working.")
        return False
    
    try:
        # Start test server
        start_test_server()
        
        # Test tunnel connection
        if test_tunnel_connection():
            print("\n🎉 TCP tunnel test successful!")
            print("The RDP2TCP channel is working correctly.")
            print("The SOCKS5 issue is likely a separate problem.")
            return True
        else:
            print("\n❌ TCP tunnel test failed!")
            print("The RDP2TCP channel is not working properly.")
            return False
            
    finally:
        # Cleanup
        cleanup_tunnel(r2t)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
