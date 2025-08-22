#!/usr/bin/env python3
"""
Test script for the shell tunnel functionality
"""

import sys
import time
import subprocess

def test_shell_tunnel():
    """Test the shell tunnel functionality"""
    try:
        # Import the CLI class using the same method as test-cli.py
        import importlib.util
        import os
        
        # Try to find the CLI file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        current_dir = os.getcwd()
        
        cli_paths = [
            os.path.join(script_dir, "rdp2tcp-cli.py"),  # In tools directory
            os.path.join(current_dir, "rdp2tcp-cli.py"),  # In current directory
            os.path.join(current_dir, "tools", "rdp2tcp-cli.py")  # In tools subdirectory
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
        
        print("Testing Shell Tunnel Functionality")
        print("="*40)
        
        # Initialize CLI
        cli = RDP2TCPEnhancedCLI()
        
        # Test 1: Create shell tunnel without connecting
        print("\n1. Testing shell tunnel creation...")
        success = cli.shell_tunnel(
            local_port=0,  # Random port
            command='cmd.exe',
            args=None,
            auto_connect=False
        )
        
        if success:
            print("✓ Shell tunnel creation successful")
        else:
            print("✗ Shell tunnel creation failed")
            return False
        
        # Test 2: Create shell tunnel with specific port
        print("\n2. Testing shell tunnel with specific port...")
        success = cli.shell_tunnel(
            local_port=4444,
            command='cmd.exe',
            args=['/C', 'echo Hello from shell tunnel'],
            auto_connect=False
        )
        
        if success:
            print("✓ Shell tunnel with specific port successful")
        else:
            print("✗ Shell tunnel with specific port failed")
            return False
        
        # Test 3: Test with PowerShell
        print("\n3. Testing PowerShell tunnel...")
        success = cli.shell_tunnel(
            local_port=4445,
            command='powershell.exe',
            args=['-Command', 'Write-Host "PowerShell tunnel test"'],
            auto_connect=False
        )
        
        if success:
            print("✓ PowerShell tunnel successful")
        else:
            print("✗ PowerShell tunnel failed")
            return False
        
        print("\n🎉 All shell tunnel tests passed!")
        print("\nTo test manual connection:")
        print("  telnet 127.0.0.1 4444")
        print("  telnet 127.0.0.1 4445")
        
        return True
        
    except Exception as e:
        print(f"✗ Shell tunnel test failed: {e}")
        return False

def test_cli_shell_command():
    """Test the CLI shell command"""
    try:
        print("\nTesting CLI Shell Command")
        print("="*30)
        
        # Test basic shell command
        cmd = [
            sys.executable, 'tools/rdp2tcp-cli.py',
            'sh',
            '--shell-command', 'cmd.exe',
            '--local-port', '4446'
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ CLI shell command successful")
            print(f"Output: {result.stdout}")
        else:
            print("✗ CLI shell command failed")
            print(f"Error: {result.stderr}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("✗ CLI shell command timed out")
        return False
    except Exception as e:
        print(f"✗ CLI shell command test failed: {e}")
        return False

def main():
    print("Shell Tunnel Test Suite")
    print("="*30)
    
    # Test 1: Direct function call
    if not test_shell_tunnel():
        print("\n❌ Shell tunnel function test failed!")
        return False
    
    # Test 2: CLI command
    if not test_cli_shell_command():
        print("\n❌ CLI shell command test failed!")
        return False
    
    print("\n🎉 All tests completed successfully!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
