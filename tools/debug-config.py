#!/usr/bin/env python3
"""
Debug script to test config loading
"""

import yaml
import sys
import os

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

if __name__ == '__main__':
    config_file = "config.yaml"
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    
    if os.path.exists(config_file):
        debug_config(config_file)
    else:
        print(f"Config file {config_file} not found")
        sys.exit(1)
