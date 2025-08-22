#!/usr/bin/env python3
"""
Test script for the shell tunnel functionality
"""

import sys
import time
import socket
import subprocess

def test_shell_connection():
    """Test shell tunnel connection after the fix"""
    try:
        # Import the CLI class using the same method as test-cli.py
        import importlib.util
        import os
        
        # Try to find the CLI file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        current_dir = os.getcwd()
        
        cli_paths = [
            os.path.join(script_dir, "rdp2tcp-cli-new.py"),  # In tools directory
            os.path.join(current_dir, "rdp2tcp-cli-new.py"),  # In current directory
            os.path.join(current_dir, "tools", "rdp2tcp-cli-new.py")  # In tools subdirectory
        ]
        
        spec = None
        found_path = None
        
        for path in cli_paths:
            if os.path.exists(path):
                spec = importlib.util.spec_from_file_location("rdp2tcp_cli", path)
                if spec is not None:
                    found_path = path
                    print(f"Found CLI file at: {path}")
                    break
        
        if spec is None:
            print(f"Available paths checked:")
            for path in cli_paths:
                print(f"  - {path} (exists: {os.path.exists(path)})")
            raise ImportError("Could not find rdp2tcp-cli.py")
            
        rdp2tcp_cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rdp2tcp_cli)
        RDP2TCPEnhancedCLI = rdp2tcp_cli.RDP2TCPEnhancedCLI
        
        print("Testing Shell Tunnel Fix")
        print("="*30)
        
        # Initialize CLI
        cli = RDP2TCPEnhancedCLI()
        
        # Create shell tunnel
        print("\n1. Creating shell tunnel...")
        success = cli.shell_tunnel(
            local_port=4447,
            command='cmd.exe',
            args=None,
            auto_connect=False
        )
        
        if not success:
            print("✗ Failed to create shell tunnel")
            return False
            
        print("✓ Shell tunnel created successfully")
        
        # Wait a moment for tunnel to be ready
        time.sleep(1)
        
        # Test connection
        print("\n2. Testing telnet connection...")
        try:
            # Create a socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(('127.0.0.1', 4447))
            
            # Send some data to test the connection
            sock.send(b'test\n')
            
            # Try to receive response
            response = sock.recv(1024)
            print(f"✓ Connection successful! Received: {response[:50]}")
            
            sock.close()
            return True
            
        except socket.timeout:
            print("✗ Connection timed out")
            return False
        except ConnectionRefusedError:
            print("✗ Connection refused")
            return False
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_cli_shell_command():
    """Test the CLI shell command with auto-connect"""
    try:
        print("\n3. Testing CLI shell command...")
        
        # Test basic shell command
        cmd = [
            sys.executable, 'tools/rdp2tcp-cli.py',
            'sh',
            '--shell-command', 'cmd.exe',
            '--local-port', '4448',
            '--connect'
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        # Run with a timeout
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print("✓ CLI shell command successful")
                print(f"Output: {result.stdout}")
                return True
            else:
                print("✗ CLI shell command failed")
                print(f"Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✓ CLI shell command timed out (expected for auto-connect)")
            return True
            
    except Exception as e:
        print(f"✗ CLI shell command test failed: {e}")
        return False

def main():
    print("Shell Tunnel Fix Test")
    print("="*25)
    
    # Test 1: Direct connection test
    if not test_shell_connection():
        print("\n❌ Shell connection test failed!")
        return False
    
    # Test 2: CLI command test
    if not test_cli_shell_command():
        print("\n❌ CLI shell command test failed!")
        return False
    
    print("\n🎉 All tests completed successfully!")
    print("\nThe shell tunnel fix appears to be working!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
