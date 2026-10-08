#!/usr/bin/env python3
"""
Test script to verify the compression fix
"""

import sys

from testutil import require_integration

def test_basic_connection():
    """Test basic RDP2TCP connection without compression"""
    try:
        from rdp2tcp import rdp2tcp, R2TException
        
        print("Testing basic RDP2TCP connection...")
        r2t = rdp2tcp('127.0.0.1', 8477)
        
        # Get info to test basic communication
        info = r2t.info()
        print(f"✓ RDP2TCP connection successful: {info}")
        
        # Test tunnel creation
        result = r2t.add_tunnel('t', ('127.0.0.1', 8888), ('127.0.0.1', 8889))
        print(f"✓ Tunnel creation successful: {result}")
        
        # Clean up
        r2t.del_tunnel(('127.0.0.1', 8888))
        r2t.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Basic connection test failed: {e}")
        return False

def test_socks5_tunnel():
    """Test SOCKS5 tunnel creation"""
    try:
        from rdp2tcp import rdp2tcp, R2TException
        
        print("\nTesting SOCKS5 tunnel creation...")
        r2t = rdp2tcp('127.0.0.1', 8477)
        
        # Create SOCKS5 tunnel
        result = r2t.add_tunnel('s', ('127.0.0.1', 19050), ('', 0))
        print(f"✓ SOCKS5 tunnel creation successful: {result}")
        
        # Get info to verify tunnel is listed
        info = r2t.info()
        print(f"✓ Server info: {info}")
        
        # Clean up
        r2t.del_tunnel(('127.0.0.1', 19050))
        r2t.close()
        
        return True
        
    except Exception as e:
        print(f"✗ SOCKS5 tunnel test failed: {e}")
        return False

def test_compression_ignored():
    """Confirm that normal operations still work.

    NOTE: compression is NOT implemented in the rdp2tcp protocol — both the
    client and server command handlers explicitly ignore R2TCMD_COMPRESS. This
    only verifies that ordinary controller traffic is unaffected; it does not
    (and cannot) prove any compression actually happens.
    """
    try:
        from rdp2tcp import rdp2tcp, R2TException

        print("\nVerifying controller still responds (compression is a no-op)...")
        r2t = rdp2tcp('127.0.0.1', 8477)
        info = r2t.info()
        print(f"✓ Controller responsive: {info}")

        r2t.close()
        return True

    except Exception as e:
        print(f"✗ Controller check failed: {e}")
        return False

def main():
    require_integration('test-compression.py')

    print("Compression Fix Test")
    print("="*30)
    
    # Test 1: Basic connection
    if not test_basic_connection():
        print("\n❌ Basic connection test failed!")
        print("The compression fix may not be working properly.")
        return False
    
    # Test 2: SOCKS5 tunnel
    if not test_socks5_tunnel():
        print("\n❌ SOCKS5 tunnel test failed!")
        print("SOCKS5 functionality may still be broken.")
        return False
    
    # Test 3: Compression handling
    if not test_compression_ignored():
        print("\n❌ Compression handling test failed!")
        print("Compression commands may still be causing issues.")
        return False
    
    print("\n🎉 All tests passed!")
    print("Controller and SOCKS5 tunnel creation work. (Compression is a")
    print("protocol no-op; these tests do not exercise real compression.)")

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
