#!/usr/bin/env python3
"""
/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
SOCKS5 Workaround Script
Creates a TCP tunnel to a local SOCKS5 proxy as an alternative to the built-in SOCKS5
"""

import sys
import os
import subprocess
import time
import socket

def check_socks5_proxy(host='127.0.0.1', port=1080):
    """Check if a SOCKS5 proxy is running locally"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, port))
        sock.close()
        return True
    except:
        return False

def install_dante_server():
    """Install dante-server SOCKS5 proxy"""
    print("Installing dante-server...")
    try:
        subprocess.run(['sudo', 'apt-get', 'update'], check=True)
        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'dante-server'], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dante-server: {e}")
        return False

def setup_dante_config():
    """Create dante-server configuration"""
    config = """# Dante SOCKS5 server configuration
logoutput: stderr
internal: 127.0.0.1 port = 1080
external: eth0

# Allow all connections (for testing)
socksmethod: none
clientmethod: none

client pass {
    from: 127.0.0.1/32 to: 0.0.0.0/0
    log: error connect disconnect
}

socks pass {
    from: 127.0.0.1/32 to: 0.0.0.0/0
    command: bind connect udpassociate
    log: error connect disconnect
}
"""
    
    try:
        with open('/tmp/dante.conf', 'w') as f:
            f.write(config)
        print("Created dante configuration at /tmp/dante.conf")
        return True
    except Exception as e:
        print(f"Failed to create dante config: {e}")
        return False

def start_dante_server():
    """Start dante-server"""
    try:
        # Stop any existing dante-server
        subprocess.run(['sudo', 'pkill', '-f', 'dante-server'], 
                      capture_output=True, text=True)
        time.sleep(1)
        
        # Start dante-server
        subprocess.Popen(['sudo', 'dante-server', '/tmp/dante.conf'],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        
        if check_socks5_proxy():
            print("✓ dante-server started successfully")
            return True
        else:
            print("✗ dante-server failed to start")
            return False
    except Exception as e:
        print(f"Failed to start dante-server: {e}")
        return False

def create_tcp_tunnel():
    """Create a TCP tunnel to the local SOCKS5 proxy"""
    try:
        from rdp2tcp import rdp2tcp, R2TException
        
        print("Creating TCP tunnel to local SOCKS5 proxy...")
        r2t = rdp2tcp('127.0.0.1', 8477)
        
        # Create tunnel from local 1080 to remote 1080
        result = r2t.add_tunnel('t', ('127.0.0.1', 1080), ('127.0.0.1', 1080))
        print(f"Tunnel created: {result}")
        
        r2t.close()
        return True
    except ImportError:
        print("rdp2tcp module not found. Please install it first.")
        return False
    except Exception as e:
        print(f"Failed to create tunnel: {e}")
        return False

def test_socks5_connection():
    """Test the SOCKS5 connection"""
    print("Testing SOCKS5 connection...")
    
    try:
        import requests
        
        # Test with requests using SOCKS5
        proxies = {
            'http': 'socks5://127.0.0.1:1080',
            'https': 'socks5://127.0.0.1:1080'
        }
        
        response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
        print(f"✓ SOCKS5 test successful: {response.json()}")
        return True
    except ImportError:
        print("requests module not found. Testing with curl...")
        try:
            result = subprocess.run(['curl', '--socks5', '127.0.0.1:1080', 
                                   'http://httpbin.org/ip'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✓ SOCKS5 test successful: {result.stdout}")
                return True
            else:
                print(f"✗ SOCKS5 test failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"Failed to test with curl: {e}")
            return False
    except Exception as e:
        print(f"✗ SOCKS5 test failed: {e}")
        return False

def main():
    print("SOCKS5 Workaround Script")
    print("=" * 40)
    
    # Check if SOCKS5 proxy is already running
    if check_socks5_proxy():
        print("✓ SOCKS5 proxy already running on port 1080")
    else:
        print("No SOCKS5 proxy found. Setting up dante-server...")
        
        if not setup_dante_config():
            print("Failed to create dante configuration")
            return False
            
        if not start_dante_server():
            print("Failed to start dante-server")
            return False
    
    # Create TCP tunnel
    if not create_tcp_tunnel():
        print("Failed to create TCP tunnel")
        return False
    
    # Test the connection
    if test_socks5_connection():
        print("\n🎉 SOCKS5 workaround is working!")
        print("\nUsage:")
        print("  # With curl")
        print("  curl --socks5 127.0.0.1:1080 http://httpbin.org/ip")
        print("")
        print("  # With proxychains")
        print("  proxychains4 -f tools/proxychains-test.conf curl http://httpbin.org/ip")
        print("")
        print("  # With Python requests")
        print("  import requests")
        print("  proxies = {'http': 'socks5://127.0.0.1:1080', 'https': 'socks5://127.0.0.1:1080'}")
        print("  response = requests.get('http://httpbin.org/ip', proxies=proxies)")
        return True
    else:
        print("\n❌ SOCKS5 workaround failed")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
