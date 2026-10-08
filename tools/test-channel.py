#!/usr/bin/env python3
"""
Test RDP2TCP channel status in detail
"""

import sys
import time
import subprocess

from testutil import require_integration

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
    import socket
    from rdp2tcp import rdp2tcp, R2TException
    from socks5_util import (socks5_handshake, build_connect_request,
                             read_socks5_reply, SOCKS5Error)

    print("\nTesting SOCKS5 after channel activity...")
    r2t = None
    sock = None
    ok = False
    try:
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

        socks5_handshake(sock)
        print("✓ Handshake successful, trying connect...")

        sock.sendall(build_connect_request("ifconfig.io", 80))
        reply = read_socks5_reply(sock)
        print(f"✓ SOCKS5 connect successful (bound {reply['addr']}:{reply['port']})")
        ok = True

    except SOCKS5Error as e:
        print(f"✗ SOCKS5 exchange failed: {e}")
    except Exception as e:
        print(f"SOCKS5 with activity test failed: {e}")
    finally:
        if sock is not None:
            sock.close()
        if r2t is not None:
            # Best-effort cleanup; don't let a cleanup error mask the result.
            for addr in (('127.0.0.1', 8888), ('127.0.0.1', 19050)):
                try:
                    r2t.del_tunnel(addr)
                except R2TException:
                    pass
            r2t.close()

    return ok

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
    require_integration('test-channel.py')

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
