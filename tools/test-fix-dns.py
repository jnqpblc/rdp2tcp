#!/usr/bin/env python3
"""
/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
DNS Resolution Fix Script
Tests and fixes DNS resolution issues with proxychains and SOCKS5
"""

import sys
import subprocess
import socket
import requests

def test_dns_resolution():
    """Test DNS resolution"""
    print("Testing DNS resolution...")
    
    # Test direct DNS resolution
    try:
        ip = socket.gethostbyname('ifconfig.io')
        print(f"✓ Direct DNS resolution: ifconfig.io -> {ip}")
    except Exception as e:
        print(f"✗ Direct DNS resolution failed: {e}")
        return False
    
    # Test with nslookup
    try:
        result = subprocess.run(['nslookup', 'ifconfig.io'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ nslookup result: {result.stdout}")
        else:
            print(f"✗ nslookup failed: {result.stderr}")
    except Exception as e:
        print(f"✗ nslookup error: {e}")
    
    return True

def test_proxychains_dns():
    """Test proxychains DNS resolution"""
    print("\nTesting proxychains DNS resolution...")
    
    # Test with curl through proxychains
    try:
        result = subprocess.run([
            'proxychains4', '-f', 'tools/proxychains-fixed.conf',
            'curl', '-s', 'http://ifconfig.io/ip'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✓ proxychains test successful: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ proxychains test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ proxychains test error: {e}")
        return False

def test_socks5_dns():
    """Test SOCKS5 DNS resolution directly"""
    print("\nTesting SOCKS5 DNS resolution...")
    
    try:
        import socks
        import socket
        
        # Configure SOCKS5
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 19050)
        socket.socket = socks.socksocket
        
        # Test DNS resolution
        ip = socket.gethostbyname('ifconfig.io')
        print(f"✓ SOCKS5 DNS resolution: ifconfig.io -> {ip}")
        
        # Test HTTP request
        response = requests.get('http://ifconfig.io/ip', timeout=10)
        print(f"✓ SOCKS5 HTTP test: {response.text.strip()}")
        
        return True
    except ImportError:
        print("PySocks not installed. Installing...")
        try:
            subprocess.run(['pip3', 'install', 'PySocks'], check=True)
            print("✓ PySocks installed. Please run this script again.")
        except Exception as e:
            print(f"✗ Failed to install PySocks: {e}")
        return False
    except Exception as e:
        print(f"✗ SOCKS5 DNS test failed: {e}")
        return False

def create_alternative_config():
    """Create alternative proxychains configuration"""
    print("\nCreating alternative configurations...")
    
    # Configuration with different DNS settings
    configs = {
        'tools/proxychains-no-dns.conf': """# proxychains configuration without DNS proxy
strict_chain
quiet_mode
# Disable proxy DNS to use local DNS
# proxy_dns

tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
socks5 127.0.0.1 19050
""",
        
        'tools/proxychains-google-dns.conf': """# proxychains configuration with Google DNS
strict_chain
quiet_mode
proxy_dns

tcp_read_time_out 15000
tcp_connect_time_out 8000

# Use Google DNS
dns 8.8.8.8
dns 8.8.4.4

[ProxyList]
socks5 127.0.0.1 19050
""",
        
        'tools/proxychains-cloudflare-dns.conf': """# proxychains configuration with Cloudflare DNS
strict_chain
quiet_mode
proxy_dns

tcp_read_time_out 15000
tcp_connect_time_out 8000

# Use Cloudflare DNS
dns 1.1.1.1
dns 1.0.0.1

[ProxyList]
socks5 127.0.0.1 19050
"""
    }
    
    for filename, content in configs.items():
        try:
            with open(filename, 'w') as f:
                f.write(content)
            print(f"✓ Created {filename}")
        except Exception as e:
            print(f"✗ Failed to create {filename}: {e}")

def test_alternative_configs():
    """Test alternative configurations"""
    print("\nTesting alternative configurations...")
    
    configs = [
        'tools/proxychains-no-dns.conf',
        'tools/proxychains-google-dns.conf', 
        'tools/proxychains-cloudflare-dns.conf'
    ]
    
    for config in configs:
        print(f"\nTesting {config}...")
        try:
            result = subprocess.run([
                'proxychains4', '-f', config,
                'curl', '-s', 'http://ifconfig.io/ip'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✓ {config} works: {result.stdout.strip()}")
            else:
                print(f"✗ {config} failed: {result.stderr}")
        except Exception as e:
            print(f"✗ {config} error: {e}")

def main():
    print("DNS Resolution Fix Script")
    print("="*40)
    
    # Test basic DNS
    test_dns_resolution()
    
    # Test proxychains
    if test_proxychains_dns():
        print("\n🎉 proxychains DNS is working!")
        return True
    
    # Test SOCKS5 directly
    if test_socks5_dns():
        print("\n🎉 SOCKS5 DNS is working!")
        return True
    
    # Create alternative configs
    create_alternative_config()
    
    # Test alternatives
    test_alternative_configs()
    
    print("\n" + "="*50)
    print("TROUBLESHOOTING TIPS")
    print("="*50)
    print("\nIf DNS resolution is still failing:")
    print("\n1. **Try without proxy DNS:**")
    print("   proxychains4 -f tools/proxychains-no-dns.conf curl http://ifconfig.io/ip")
    print("\n2. **Use IP addresses directly:**")
    print("   curl --socks5 127.0.0.1:19050 http://104.18.114.97/ip")
    print("\n3. **Check your SOCKS5 proxy:**")
    print("   python3 tools/debug-socks5.py 19050")
    print("\n4. **Use a different DNS server:**")
    print("   Add 'dns 1.1.1.1' to your proxychains config")
    print("\n5. **Test with a simple TCP tunnel:**")
    print("   python3 tools/test-tcp-tunnel.py")
    
    return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
