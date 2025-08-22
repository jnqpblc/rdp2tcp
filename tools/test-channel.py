#!/usr/bin/env python3
"""
Test RDP2TCP channel status in detail
"""

import sys
import time
import subprocess

def test_channel_activity():
    """Test if the RDP2TCP channel is active"""
    try:
        from rdp2tcp import rdp2tcp, R2TException
        
        print("Testing RDP2TCP channel activity...")
        r2t = rdp2tcp('127.0.0.1', 8477)
        
        # Get initial info
        info = r2t.info()
        print(f"Initial info: {info}")
        
        # Try to create multiple tunnels to generate channel activity
        print("\nGenerating channel activity...")
        tunnels = []
        
        for i in range(3):
            try:
                result = r2t.add_tunnel('t', ('127.0.0.1', 8000 + i), ('127.0.0.1', 9000 + i))
                print(f"Tunnel {i+1}: {result}")
                tunnels.append(('127.0.0.1', 8000 + i))
            except Exception as e:
                print(f"Tunnel {i+1} failed: {e}")
        
        # Wait a moment for channel activity
        time.sleep(1)
        
        # Get updated info
        info = r2t.info()
        print(f"\nUpdated info: {info}")
        
        # Clean up tunnels
        print("\nCleaning up tunnels...")
        for tunnel in tunnels:
            try:
                result = r2t.del_tunnel(tunnel)
                print(f"Deleted {tunnel}: {result}")
            except Exception as e:
                print(f"Delete {tunnel} failed: {e}")
        
        r2t.close()
        return True
        
    except Exception as e:
        print(f"Channel activity test failed: {e}")
        return False

def test_socks5_with_activity():
    """Test SOCKS5 after generating channel activity"""
    try:
        from rdp2tcp import rdp2tcp, R2TException
        import socket
        import struct
        
        print("\nTesting SOCKS5 after channel activity...")
        r2t = rdp2tcp('127.0.0.1', 8477)
        
        # Generate some channel activity first
        print("Generating channel activity...")
        result = r2t.add_tunnel('t', ('127.0.0.1', 8888), ('127.0.0.1', 8889))
        print(f"Activity tunnel: {result}")
        
        # Wait for channel to be active
        time.sleep(1)
        
        # Create SOCKS5 tunnel
        print("Creating SOCKS5 tunnel...")
        result = r2t.add_tunnel('s', ('127.0.0.1', 19050), ('', 0))
        print(f"SOCKS5 tunnel: {result}")
        
        # Wait a moment
        time.sleep(1)
        
        # Test SOCKS5 connection
        print("Testing SOCKS5 connection...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(('127.0.0.1', 19050))
        
        # Send handshake
        handshake = b'\x05\x01\x00'
        sock.send(handshake)
        response = sock.recv(2)
        print(f"Handshake response: {response.hex()}")
        
        if response == b'\x05\x00':
            print("✓ Handshake successful, trying connect...")
            
            # Send connect request
            target_host = "ifconfig.io"
            target_port = 80
            domain = target_host.encode()
            connect_req = struct.pack('!BBBB', 5, 1, 0, 3) + struct.pack('B', len(domain)) + domain + struct.pack('!H', target_port)
            sock.send(connect_req)
            
            # Get full response
            response = sock.recv(10)
            print(f"Connect response: {response.hex()}")
            
            if len(response) >= 4:
                ver, rep, rsv, atyp = struct.unpack('!BBBB', response[:4])
                print(f"Version: {ver}, Reply: {rep}, RSV: {rsv}, ATYPE: {atyp}")
                
                if rep == 0:
                    print("✓ SOCKS5 connect successful!")
                else:
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
                    print(f"✗ SOCKS5 connect failed: {error_msg}")
            else:
                print(f"✗ Incomplete connect response: {response.hex()}")
        else:
            print(f"✗ Handshake failed: {response.hex()}")
        
        sock.close()
        
        # Clean up
        r2t.del_tunnel(('127.0.0.1', 8888))
        r2t.del_tunnel(('127.0.0.1', 19050))
        r2t.close()
        
        return True
        
    except Exception as e:
        print(f"SOCKS5 with activity test failed: {e}")
        return False

def check_rdp_processes():
    """Check RDP-related processes"""
    print("\nChecking RDP processes...")
    
    try:
        # Check for rdesktop processes
        result = subprocess.run(['pgrep', 'rdesktop'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✓ Found {len(pids)} rdesktop processes: {pids}")
        else:
            print("✗ No rdesktop processes found")
        
        # Check for xfreerdp processes
        result = subprocess.run(['pgrep', 'xfreerdp'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✓ Found {len(pids)} xfreerdp processes: {pids}")
        else:
            print("✗ No xfreerdp processes found")
        
        # Check for rdp2tcp processes
        result = subprocess.run(['pgrep', 'rdp2tcp'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✓ Found {len(pids)} rdp2tcp processes: {pids}")
        else:
            print("✗ No rdp2tcp processes found")
            
    except Exception as e:
        print(f"Process check failed: {e}")

def main():
    print("RDP2TCP Channel Status Test")
    print("="*40)
    
    # Check processes
    check_rdp_processes()
    
    # Test channel activity
    if not test_channel_activity():
        print("\n❌ Channel activity test failed!")
        return False
    
    # Test SOCKS5 with activity
    if not test_socks5_with_activity():
        print("\n❌ SOCKS5 with activity test failed!")
        return False
    
    print("\n🎉 All tests completed!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
