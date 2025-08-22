#!/usr/bin/env python3
"""
Simple test script for the RDP2TCP Enhanced CLI
"""

import sys
import os

# Add the current directory to the path so we can import the CLI
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the CLI class directly from the file
    import importlib.util
    spec = importlib.util.spec_from_file_location("rdp2tcp_cli", "rdp2tcp-cli.py")
    rdp2tcp_cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rdp2tcp_cli)
    RDP2TCPEnhancedCLI = rdp2tcp_cli.RDP2TCPEnhancedCLI
    
    print("Testing RDP2TCP Enhanced CLI...")
    
    # Test initialization with config file
    config_file = "config.yaml"
    if os.path.exists(config_file):
        print(f"Loading config from {config_file}")
        cli = RDP2TCPEnhancedCLI(config_file)
        print("CLI initialized successfully!")
        
        # Test listing tunnels
        print("\nTesting tunnel list...")
        try:
            cli.tunnel_list()
        except Exception as e:
            print(f"Tunnel list failed (expected if no server running): {e}")
            
        # Test config load
        print("\nTesting config load...")
        try:
            cli.config_load_tunnels()
        except Exception as e:
            print(f"Config load failed (expected if no server running): {e}")
            
    else:
        print(f"Config file {config_file} not found, testing without config")
        cli = RDP2TCPEnhancedCLI()
        print("CLI initialized successfully!")
        
    print("\nCLI test completed!")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the tools directory")
except Exception as e:
    print(f"Error: {e}")
