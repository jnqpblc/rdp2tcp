#!/usr/bin/env python3
"""
Enhanced RDP2TCP CLI Tool
Provides a modern command-line interface for managing RDP2TCP tunnels
"""

import argparse
import json
import yaml
import sys
import os
import time
import socket
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# Import the existing rdp2tcp module
from rdp2tcp import rdp2tcp, R2TException

@dataclass
class TunnelConfig:
    """Configuration for a tunnel"""
    name: str
    type: str  # 'tcp', 'udp', 'reverse', 'process', 'socks5'
    local_host: str
    local_port: int
    remote_host: Optional[str] = None
    remote_port: Optional[int] = None
    command: Optional[str] = None
    enabled: bool = True
    compression: Optional[str] = None  # 'gzip', 'lz4', 'none'
    bandwidth_limit: Optional[int] = None  # bytes per second

@dataclass
class GlobalConfig:
    """Global configuration"""
    controller_host: str = '127.0.0.1'
    controller_port: int = 8477
    log_level: str = 'INFO'
    log_file: Optional[str] = None
    tunnels: List[TunnelConfig] = None

class RDP2TCPEnhancedCLI:
    """Enhanced CLI for RDP2TCP management"""
    
    def __init__(self, config_file: Optional[str] = None):
        # Setup logging first with default config
        self.config = GlobalConfig()
        self.setup_logging()
        
        # Now load the actual config
        self.config = self.load_config(config_file)
        self.setup_logging()  # Re-setup with loaded config
        self.client = None
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.log_level.upper())
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(self.config.log_file) if self.config.log_file else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger('rdp2tcp-cli')
        
    def load_config(self, config_file: Optional[str]) -> GlobalConfig:
        """Load configuration from file or use defaults"""
        config = GlobalConfig()
        
        if config_file and os.path.exists(config_file):
            self.logger.info(f"Loading configuration from {config_file}")
            with open(config_file, 'r') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
                    
                # Update config with file data
                for key, value in data.items():
                    if hasattr(config, key):
                        if key == 'tunnels':
                            # Keep tunnels as list of dicts for easier handling
                            config.tunnels = value
                        else:
                            setattr(config, key, value)
                        
        return config
        
    def connect(self) -> bool:
        """Connect to RDP2TCP controller"""
        try:
            self.client = rdp2tcp(self.config.controller_host, self.config.controller_port)
            self.logger.info(f"Connected to controller at {self.config.controller_host}:{self.config.controller_port}")
            return True
        except R2TException as e:
            self.logger.error(f"Failed to connect: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from controller"""
        if self.client:
            self.client.close()
            self.client = None
            
    def tunnel_create(self, name: str, tunnel_type: str, local_host: str, local_port: int,
                     remote_host: Optional[str] = None, remote_port: Optional[int] = None,
                     command: Optional[str] = None, compression: Optional[str] = None,
                     bandwidth_limit: Optional[int] = None) -> bool:
        """Create a new tunnel"""
        if not self.connect():
            return False
            
        try:
            # Map tunnel types to RDP2TCP commands
            type_map = {
                'tcp': 't',
                'reverse': 'r', 
                'process': 'x',
                'socks5': 's'
            }
            
            if tunnel_type not in type_map:
                self.logger.error(f"Unsupported tunnel type: {tunnel_type}")
                return False
                
            cmd_type = type_map[tunnel_type]
            
            if tunnel_type == 'process':
                if not command:
                    self.logger.error("Command required for process tunnels")
                    return False
                result = self.client.add_tunnel(cmd_type, (local_host, local_port), (command, 0))
            elif tunnel_type == 'socks5':
                result = self.client.add_tunnel(cmd_type, (local_host, local_port), ('', 0))
            else:
                if not remote_host or not remote_port:
                    self.logger.error("Remote host and port required for TCP/reverse tunnels")
                    return False
                result = self.client.add_tunnel(cmd_type, (local_host, local_port), (remote_host, remote_port))
                
            self.logger.info(f"Tunnel '{name}' created: {result}")
            
            # Store tunnel configuration
            tunnel_config = TunnelConfig(
                name=name,
                type=tunnel_type,
                local_host=local_host,
                local_port=local_port,
                remote_host=remote_host,
                remote_port=remote_port,
                command=command,
                compression=compression,
                bandwidth_limit=bandwidth_limit
            )
            
            if not self.config.tunnels:
                self.config.tunnels = []
            self.config.tunnels.append(tunnel_config)
            
            return True
            
        except R2TException as e:
            self.logger.error(f"Failed to create tunnel: {e}")
            return False
        finally:
            self.disconnect()
            
    def tunnel_delete(self, local_host: str, local_port: int) -> bool:
        """Delete a tunnel"""
        if not self.connect():
            return False
            
        try:
            result = self.client.del_tunnel((local_host, local_port))
            self.logger.info(f"Tunnel deleted: {result}")
            return True
        except R2TException as e:
            self.logger.error(f"Failed to delete tunnel: {e}")
            return False
        finally:
            self.disconnect()
            
    def tunnel_list(self, format_type: str = 'table') -> bool:
        """List all tunnels"""
        if not self.connect():
            return False
            
        try:
            info = self.client.info()
            
            if format_type == 'json':
                # Parse the info and convert to JSON
                tunnels = self.parse_tunnel_info(info)
                print(json.dumps(tunnels, indent=2))
            elif format_type == 'yaml':
                tunnels = self.parse_tunnel_info(info)
                print(yaml.dump(tunnels, default_flow_style=False))
            else:
                print(info)
                
            return True
            
        except R2TException as e:
            self.logger.error(f"Failed to list tunnels: {e}")
            return False
        finally:
            self.disconnect()
            
    def parse_tunnel_info(self, info: str) -> List[Dict[str, Any]]:
        """Parse tunnel info string into structured data"""
        tunnels = []
        lines = info.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.split()
            if len(parts) < 2:
                continue
                
            tunnel_type = parts[0]
            if tunnel_type in ['tunsrv', 's5srv', 'rtunsrv']:
                tunnel = {
                    'type': tunnel_type,
                    'local_address': parts[1],
                    'remote_address': ' '.join(parts[2:]) if len(parts) > 2 else None
                }
                tunnels.append(tunnel)
            elif tunnel_type in ['tuncli', 's5cli', 'rtuncli']:
                tunnel = {
                    'type': tunnel_type,
                    'local_address': parts[1],
                    'tunnel_id': parts[2] if len(parts) > 2 else None,
                    'remote_address': ' '.join(parts[3:]) if len(parts) > 3 else None
                }
                tunnels.append(tunnel)
                
        return tunnels
        
    def monitor(self, tunnel_id: Optional[str] = None, duration: int = 60) -> bool:
        """Monitor tunnel statistics"""
        if not self.connect():
            return False
            
        try:
            start_time = time.time()
            print(f"Monitoring tunnels for {duration} seconds...")
            print("Press Ctrl+C to stop")
            
            while time.time() - start_time < duration:
                try:
                    info = self.client.info()
                    print(f"\n[{time.strftime('%H:%M:%S')}] Tunnel Status:")
                    print(info)
                    time.sleep(5)
                except KeyboardInterrupt:
                    break
                    
            return True
            
        except R2TException as e:
            self.logger.error(f"Failed to monitor tunnels: {e}")
            return False
        finally:
            self.disconnect()
            
    def config_save(self, output_file: str) -> bool:
        """Save current configuration to file"""
        try:
            config_data = asdict(self.config)
            
            if output_file.endswith('.yaml') or output_file.endswith('.yml'):
                with open(output_file, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            else:
                with open(output_file, 'w') as f:
                    json.dump(config_data, f, indent=2)
                    
            self.logger.info(f"Configuration saved to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
            
    def config_load_tunnels(self) -> bool:
        """Load and create tunnels from configuration"""
        if not self.config.tunnels:
            self.logger.warning("No tunnels defined in configuration")
            return True
            
        success_count = 0
        total_count = len(self.config.tunnels)
        
        for tunnel_data in self.config.tunnels:
            # Handle both dict and TunnelConfig objects
            if isinstance(tunnel_data, dict):
                # Convert dict to TunnelConfig-like access
                enabled = tunnel_data.get('enabled', True)
                name = tunnel_data.get('name', 'unnamed')
                tunnel_type = tunnel_data.get('type')
                local_host = tunnel_data.get('local_host', '127.0.0.1')
                local_port = tunnel_data.get('local_port')
                remote_host = tunnel_data.get('remote_host')
                remote_port = tunnel_data.get('remote_port')
                command = tunnel_data.get('command')
                compression = tunnel_data.get('compression')
                bandwidth_limit = tunnel_data.get('bandwidth_limit')
            else:
                # Assume it's a TunnelConfig object
                enabled = getattr(tunnel_data, 'enabled', True)
                name = getattr(tunnel_data, 'name', 'unnamed')
                tunnel_type = getattr(tunnel_data, 'type', None)
                local_host = getattr(tunnel_data, 'local_host', '127.0.0.1')
                local_port = getattr(tunnel_data, 'local_port', None)
                remote_host = getattr(tunnel_data, 'remote_host', None)
                remote_port = getattr(tunnel_data, 'remote_port', None)
                command = getattr(tunnel_data, 'command', None)
                compression = getattr(tunnel_data, 'compression', None)
                bandwidth_limit = getattr(tunnel_data, 'bandwidth_limit', None)
            
            if not enabled:
                self.logger.info(f"Skipping disabled tunnel: {name}")
                continue
                
            if not tunnel_type or not local_port:
                self.logger.error(f"Invalid tunnel configuration for {name}: missing type or local_port")
                continue
                
            self.logger.info(f"Creating tunnel: {name}")
            
            try:
                success = self.tunnel_create(
                    name=name,
                    tunnel_type=tunnel_type,
                    local_host=local_host,
                    local_port=local_port,
                    remote_host=remote_host,
                    remote_port=remote_port,
                    command=command,
                    compression=compression,
                    bandwidth_limit=bandwidth_limit
                )
                
                if success:
                    success_count += 1
                    self.logger.info(f"Successfully created tunnel: {name}")
                else:
                    self.logger.error(f"Failed to create tunnel: {name}")
                    
            except Exception as e:
                self.logger.error(f"Error creating tunnel {name}: {e}")
                
        self.logger.info(f"Tunnel creation complete: {success_count}/{total_count} successful")
        return success_count == total_count

def main():
    parser = argparse.ArgumentParser(
        description='Enhanced RDP2TCP CLI Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rdp2tcp-cli --config config.yaml tunnel create --name web --type tcp --local 8080 --remote 80
  rdp2tcp-cli tunnel list --format json
  rdp2tcp-cli monitor --duration 300
  rdp2tcp-cli config save --output config.yaml
  rdp2tcp-cli --config config.yaml config load
        """
    )
    
    # Global options
    parser.add_argument('--config', '-c', help='Configuration file (YAML or JSON)')
    parser.add_argument('--host', help='Controller host (overrides config)')
    parser.add_argument('--port', type=int, help='Controller port (overrides config)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Log level (overrides config)')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Tunnel commands
    tunnel_parser = subparsers.add_parser('tunnel', help='Tunnel management')
    tunnel_subparsers = tunnel_parser.add_subparsers(dest='tunnel_command')
    
    # Create tunnel
    create_parser = tunnel_subparsers.add_parser('create', help='Create a new tunnel')
    create_parser.add_argument('--name', required=True, help='Tunnel name')
    create_parser.add_argument('--type', required=True, 
                              choices=['tcp', 'reverse', 'process', 'socks5'],
                              help='Tunnel type')
    create_parser.add_argument('--local-host', default='127.0.0.1', help='Local host')
    create_parser.add_argument('--local-port', type=int, required=True, help='Local port')
    create_parser.add_argument('--remote-host', help='Remote host (required for tcp/reverse)')
    create_parser.add_argument('--remote-port', type=int, help='Remote port (required for tcp/reverse)')
    create_parser.add_argument('--command', help='Command for process tunnels')
    create_parser.add_argument('--compression', choices=['gzip', 'lz4', 'none'], help='Compression type')
    create_parser.add_argument('--bandwidth-limit', type=int, help='Bandwidth limit (bytes/sec)')
    
    # Delete tunnel
    delete_parser = tunnel_subparsers.add_parser('delete', help='Delete a tunnel')
    delete_parser.add_argument('--local-host', required=True, help='Local host')
    delete_parser.add_argument('--local-port', type=int, required=True, help='Local port')
    
    # List tunnels
    list_parser = tunnel_subparsers.add_parser('list', help='List tunnels')
    list_parser.add_argument('--format', choices=['table', 'json', 'yaml'], 
                            default='table', help='Output format')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor tunnels')
    monitor_parser.add_argument('--tunnel-id', help='Specific tunnel ID to monitor')
    monitor_parser.add_argument('--duration', type=int, default=60, help='Monitor duration (seconds)')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='config_command')
    
    save_parser = config_subparsers.add_parser('save', help='Save configuration')
    save_parser.add_argument('--output', required=True, help='Output file')
    
    load_parser = config_subparsers.add_parser('load', help='Load tunnels from configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    # Initialize CLI
    cli = RDP2TCPEnhancedCLI(args.config)
    
    # Override config with command line arguments
    if args.host:
        cli.config.controller_host = args.host
    if args.port:
        cli.config.controller_port = args.port
    if args.log_level:
        cli.config.log_level = args.log_level
        
    # Execute commands
    try:
        if args.command == 'tunnel':
            if args.tunnel_command == 'create':
                success = cli.tunnel_create(
                    name=args.name,
                    tunnel_type=args.type,
                    local_host=args.local_host,
                    local_port=args.local_port,
                    remote_host=args.remote_host,
                    remote_port=args.remote_port,
                    command=args.command,
                    compression=args.compression,
                    bandwidth_limit=args.bandwidth_limit
                )
            elif args.tunnel_command == 'delete':
                success = cli.tunnel_delete(args.local_host, args.local_port)
            elif args.tunnel_command == 'list':
                success = cli.tunnel_list(args.format)
            else:
                tunnel_parser.print_help()
                return 1
                
        elif args.command == 'monitor':
            success = cli.monitor(args.tunnel_id, args.duration)
            
        elif args.command == 'config':
            if args.config_command == 'save':
                success = cli.config_save(args.output)
            elif args.config_command == 'load':
                success = cli.config_load_tunnels()
            else:
                config_parser.print_help()
                return 1
                
        else:
            parser.print_help()
            return 1
            
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        cli.logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
