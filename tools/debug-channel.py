#!/usr/bin/env python3
"""
/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
RDP2TCP Channel Connection Debug Script
"""

import sys
import socket
import time
import subprocess

def check_controller_connection(host='127.0.0.1', port=8477):
    """Check if the RDP2TCP controller is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        sock.close()
        return True
    except Exception as e:
        print(f"Controller connection failed: {e}")
        return False

def test_channel_communication():
    """Test basic channel communication"""
    try:
        from rdp2tcp import rdp2tcp, R2TException
        
        print("Testing RDP2TCP channel communication...")
        r2t = rdp2tcp('127.0.0.1', 8477)
        
        # Test basic info command
        info = r2t.info()
        print(f"Channel info: {info}")
        
        # Test simple tunnel creation
        print("Testing tunnel creation...")
        result = r2t.add_tunnel('t', ('127.0.0.1', 9999), ('127.0.0.1', 9998))
        print(f"Tunnel creation result: {result}")
        
        # Test tunnel deletion
        print("Testing tunnel deletion...")
        result = r2t.del_tunnel(('127.0.0.1', 9999))
        print(f"Tunnel deletion result: {result}")
        
        r2t.close()
        return True
        
    except ImportError:
        print("rdp2tcp module not found")
        return False
    except Exception as e:
        print(f"Channel communication failed: {e}")
        return False

def check_rdp_processes():
    """Check for RDP-related processes"""
    print("Checking RDP processes...")
    
    try:
        # Check for rdesktop processes
        result = subprocess.run(['pgrep', '-f', 'rdesktop'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✓ Found {len(pids)} rdesktop processes: {pids}")
        else:
            print("✗ No rdesktop processes found")
            
        # Check for rdp2tcp processes
        result = subprocess.run(['pgrep', '-f', 'rdp2tcp'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✓ Found {len(pids)} rdp2tcp processes: {pids}")
        else:
            print("✗ No rdp2tcp processes found")
            
    except Exception as e:
        print(f"Error checking processes: {e}")

def check_network_connections():
    """Check network connections"""
    print("Checking network connections...")
    
    try:
        # Check for connections to port 8477
        result = subprocess.run(['netstat', '-tuln'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if '8477' in line:
                    print(f"✓ Found connection: {line.strip()}")
                    
        # Check for listening ports
        result = subprocess.run(['ss', '-tuln'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if '8477' in line or '19050' in line:
                    print(f"✓ Found listening port: {line.strip()}")
                    
    except Exception as e:
        print(f"Error checking network: {e}")

def restart_rdp2tcp_client():
    """Instructions for restarting RDP2TCP client"""
    print("\n" + "="*50)
    print("CHANNEL CONNECTION TROUBLESHOOTING")
    print("="*50)
    
    print("\nThe 'channel not connected' error indicates that the RDP2TCP")
    print("virtual channel connection is broken or not properly established.")
    print("\nTo fix this:")
    print("\n1. **Restart the RDP session completely:**")
    print("   - Close rdesktop completely")
    print("   - Wait 5-10 seconds")
    print("   - Restart rdesktop with the RDP2TCP addin:")
    print("     rdesktop -r addin:rdp2tcp:/path/to/rdp2tcp <target-ip>")
    print("\n2. **Check RDP2TCP server on remote machine:**")
    print("   - Ensure rdp2tcp.exe is running in the RDP session")
    print("   - Check Windows Event Logs for any errors")
    print("   - Restart rdp2tcp.exe if necessary")
    print("\n3. **Verify virtual channel:**")
    print("   - The RDP virtual channel must be active")
    print("   - Check if the channel is listed in rdesktop output")
    print("\n4. **Network connectivity:**")
    print("   - Ensure no firewall is blocking the RDP connection")
    print("   - Check if the RDP session is stable")
    print("\n5. **Alternative approach:**")
    print("   - Use TCP tunnels instead of SOCKS5")
    print("   - Create a simple TCP tunnel to test connectivity")

def main():
    print("RDP2TCP Channel Connection Debug")
    print("="*40)
    
    # Check controller connection
    print("1. Checking controller connection...")
    if check_controller_connection():
        print("✓ Controller is accessible")
    else:
        print("✗ Controller is not accessible")
        restart_rdp2tcp_client()
        return
    
    # Check processes
    print("\n2. Checking RDP processes...")
    check_rdp_processes()
    
    # Check network
    print("\n3. Checking network connections...")
    check_network_connections()
    
    # Test channel communication
    print("\n4. Testing channel communication...")
    if test_channel_communication():
        print("✓ Channel communication working")
        print("\nThe channel appears to be working. The SOCKS5 issue might be")
        print("a separate problem with the SOCKS5 implementation.")
    else:
        print("✗ Channel communication failed")
        restart_rdp2tcp_client()

if __name__ == '__main__':
    main()
