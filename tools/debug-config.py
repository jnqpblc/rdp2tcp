#!/usr/bin/env python3
"""
Debug script to test config loading
"""

import yaml
import sys
import os
import argparse

def debug_config(config_file):
    print(f"Loading config from: {config_file}")
    
    with open(config_file, 'r') as f:
        data = yaml.safe_load(f)
    
    print("Config structure:")
    print(f"  controller_host: {data.get('controller_host')}")
    print(f"  controller_port: {data.get('controller_port')}")
    print(f"  log_level: {data.get('log_level')}")
    print(f"  log_file: {data.get('log_file')}")
    
    tunnels = data.get('tunnels', [])
    print(f"  tunnels: {len(tunnels)} found")
    
    for i, tunnel in enumerate(tunnels):
        print(f"    Tunnel {i+1}:")
        print(f"      name: {tunnel.get('name')}")
        print(f"      type: {tunnel.get('type')}")
        print(f"      enabled: {tunnel.get('enabled')}")
        print(f"      local_host: {tunnel.get('local_host')}")
        print(f"      local_port: {tunnel.get('local_port')}")
        print(f"      remote_host: {tunnel.get('remote_host')}")
        print(f"      remote_port: {tunnel.get('remote_port')}")
        print(f"      command: {tunnel.get('command')}")
        print(f"      compression: {tunnel.get('compression')}")
        print(f"      bandwidth_limit: {tunnel.get('bandwidth_limit')}")
        print()

def main():
    parser = argparse.ArgumentParser(
        description='Debug RDP2TCP configuration file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 debug-config.py
  python3 debug-config.py --config my-config.yaml
  python3 debug-config.py -c tools/config.yaml
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"Debug mode enabled")
        print(f"Config file: {args.config}")
        print(f"File exists: {os.path.exists(args.config)}")
        print()
    
    if os.path.exists(args.config):
        debug_config(args.config)
    else:
        print(f"Error: Config file '{args.config}' not found")
        print(f"Current directory: {os.getcwd()}")
        print(f"Available files: {[f for f in os.listdir('.') if f.endswith(('.yaml', '.yml', '.json'))]}")
        sys.exit(1)

if __name__ == '__main__':
    main()
