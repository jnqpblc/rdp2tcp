#!/usr/bin/env python3
"""
/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
Enhanced RDP2TCP CLI Tool
Provides a modern command-line interface for managing RDP2TCP tunnels
"""

import argparse
import json
import yaml
import sys
import os
import time
import random
import subprocess
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import logging

# Import the existing rdp2tcp module
from rdp2tcp import rdp2tcp, R2TException

# Tunnel types understood by the controller. Keys are the CLI-facing names,
# values are the single-character command codes used by the wire protocol.
TYPE_MAP = {
    'tcp': 't',
    'reverse': 'r',
    'process': 'x',
    'socks5': 's',
}

# Controller "info" rows that represent a listener we can delete. Client /
# per-connection sockets (tuncli, s5cli, rtuncli) must never be deleted by
# address, so they are deliberately excluded here.
LISTENER_TYPES = ('tunsrv', 's5srv', 'rtunsrv')

@dataclass
class TunnelConfig:
    """Configuration for a tunnel"""
    name: str
    type: str  # 'tcp', 'reverse', 'process', 'socks5'
    local_host: str
    local_port: int
    remote_host: Optional[str] = None
    remote_port: Optional[int] = None
    command: Optional[str] = None
    enabled: bool = True

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
        # A logger always exists; handlers are attached once, by setup_logging(),
        # after command-line overrides have been applied (see main()).
        self.logger = logging.getLogger('rdp2tcp-cli')
        self.config = self.load_config(config_file)
        self.client = None

    def setup_logging(self):
        """Configure logging exactly once.

        Diagnostics go to stderr so they never corrupt JSON/YAML written to
        stdout. force=True lets a later call (after config/CLI overrides) take
        effect instead of being silently ignored by basicConfig().
        """
        log_level = getattr(logging, str(self.config.log_level).upper(), logging.INFO)
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        handlers = [logging.StreamHandler(sys.stderr)]
        if self.config.log_file:
            handlers.append(logging.FileHandler(self.config.log_file))

        logging.basicConfig(level=log_level, format=log_format,
                             handlers=handlers, force=True)
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
                for key, value in (data or {}).items():
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
                      command: Optional[str] = None) -> bool:
        """Create a new tunnel"""
        if tunnel_type not in TYPE_MAP:
            self.logger.error(f"Unsupported tunnel type: {tunnel_type}")
            return False

        if not self.connect():
            return False

        try:
            cmd_type = TYPE_MAP[tunnel_type]

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
            if tunnel_type in LISTENER_TYPES:
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

    @staticmethod
    def _split_address(local_address: str) -> Tuple[Optional[str], Optional[int]]:
        """Split a controller 'host:port' address into (host, port).

        Returns (host, None) when the port cannot be parsed.
        """
        if not local_address:
            return None, None
        if ':' in local_address:
            host, port_str = local_address.rsplit(':', 1)
        else:
            host, port_str = '127.0.0.1', local_address
        try:
            return host, int(port_str)
        except ValueError:
            return host, None

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

    @staticmethod
    def _tunnel_field(tunnel_data, field, default=None):
        """Read a field from either a dict or a TunnelConfig object."""
        if isinstance(tunnel_data, dict):
            return tunnel_data.get(field, default)
        return getattr(tunnel_data, field, default)

    def config_load_tunnels(self) -> bool:
        """Load and create tunnels from configuration"""
        if not self.config.tunnels:
            self.logger.warning("No tunnels defined in configuration")
            return True

        success_count = 0
        attempted_count = 0  # only enabled tunnels we actually try to create

        for tunnel_data in self.config.tunnels:
            enabled = self._tunnel_field(tunnel_data, 'enabled', True)
            name = self._tunnel_field(tunnel_data, 'name', 'unnamed')

            if not enabled:
                self.logger.info(f"Skipping disabled tunnel: {name}")
                continue

            tunnel_type = self._tunnel_field(tunnel_data, 'type')
            local_host = self._tunnel_field(tunnel_data, 'local_host', '127.0.0.1')
            local_port = self._tunnel_field(tunnel_data, 'local_port')
            remote_host = self._tunnel_field(tunnel_data, 'remote_host')
            remote_port = self._tunnel_field(tunnel_data, 'remote_port')
            command = self._tunnel_field(tunnel_data, 'command')

            attempted_count += 1

            # Reject options that the protocol does not actually implement so
            # a config cannot silently appear to enable them.
            compression = self._tunnel_field(tunnel_data, 'compression')
            bandwidth_limit = self._tunnel_field(tunnel_data, 'bandwidth_limit')
            if (compression and compression != 'none') or bandwidth_limit:
                self.logger.error(
                    f"Tunnel '{name}' requests compression/bandwidth_limit, which are "
                    f"not implemented by the rdp2tcp protocol; refusing to create it")
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
                )

                if success:
                    success_count += 1
                    self.logger.info(f"Successfully created tunnel: {name}")
                else:
                    self.logger.error(f"Failed to create tunnel: {name}")

            except Exception as e:
                self.logger.error(f"Error creating tunnel {name}: {e}")

        self.logger.info(f"Tunnel creation complete: {success_count}/{attempted_count} successful")
        return success_count == attempted_count

    def _config_matches(self, host: Optional[str], port: Optional[int],
                        tunnel_names: list) -> bool:
        """True if a configured, named tunnel matches this listener host/port."""
        for tunnel_data in self.config.tunnels or []:
            name = self._tunnel_field(tunnel_data, 'name', '')
            cfg_port = self._tunnel_field(tunnel_data, 'local_port')
            cfg_host = self._tunnel_field(tunnel_data, 'local_host', '127.0.0.1')
            if name in tunnel_names and cfg_port == port and (cfg_host == host):
                return True
        return False

    def cleanup_tunnels(self, tunnel_names: list = None) -> bool:
        """Cleanup and close tunnel listeners.

        Only listener sockets (tunsrv/s5srv/rtunsrv) are ever deleted; live
        per-connection sockets are left alone. Success is measured against the
        set of listeners actually selected for closing, not every parsed row.
        """
        if not self.connect():
            return False

        try:
            info = self.client.info()
            all_entries = self.parse_tunnel_info(info)
            listeners = [t for t in all_entries if t.get('type') in LISTENER_TYPES]

            if not listeners:
                self.logger.info("No active tunnel listeners found")
                return True

            self.logger.info(f"Found {len(listeners)} active tunnel listener(s)")

            # Decide which listeners to close before touching any of them.
            selected = []
            for tunnel in listeners:
                local_address = tunnel.get('local_address', '')
                host, port = self._split_address(local_address)
                if port is None:
                    self.logger.warning(f"Could not parse address '{local_address}'; skipping")
                    continue

                if tunnel_names and not self._config_matches(host, port, tunnel_names):
                    self.logger.info(f"Skipping tunnel {local_address} (not in cleanup list)")
                    continue

                selected.append((local_address, host, port))

            if not selected:
                self.logger.info("No matching tunnel listeners to close")
                return True

            closed_count = 0
            for local_address, host, port in selected:
                self.logger.info(f"Closing tunnel: {local_address}")
                try:
                    if self.tunnel_delete(host, port):
                        closed_count += 1
                        self.logger.info(f"Successfully closed tunnel: {local_address}")
                    else:
                        self.logger.error(f"Failed to close tunnel: {local_address}")
                except Exception as e:
                    self.logger.error(f"Error closing tunnel {local_address}: {e}")

            self.logger.info(f"Tunnel cleanup complete: {closed_count}/{len(selected)} closed")
            return closed_count == len(selected)

        except Exception as e:
            self.logger.error(f"Error during tunnel cleanup: {e}")
            return False
        finally:
            self.disconnect()

    def cleanup_all_tunnels(self) -> bool:
        """Cleanup all active tunnel listeners"""
        return self.cleanup_tunnels()

    def cleanup_config_tunnels(self) -> bool:
        """Cleanup only tunnels defined in the configuration"""
        if not self.config.tunnels:
            self.logger.warning("No tunnels defined in configuration")
            return True

        tunnel_names = []
        for tunnel_data in self.config.tunnels:
            name = self._tunnel_field(tunnel_data, 'name', '')
            enabled = self._tunnel_field(tunnel_data, 'enabled', True)
            if enabled and name:
                tunnel_names.append(name)

        if not tunnel_names:
            self.logger.info("No enabled tunnels found in configuration")
            return True

        self.logger.info(f"Cleaning up {len(tunnel_names)} tunnel(s) from configuration: {', '.join(tunnel_names)}")
        return self.cleanup_tunnels(tunnel_names)

    def shell_tunnel(self, local_port=0, command='cmd.exe', args=None, auto_connect=False) -> bool:
        """Create a process (shell) tunnel and optionally connect to it"""
        if not self.connect():
            return False

        try:
            full_command = command
            if args:
                full_command += ' ' + ' '.join(args)

            self.logger.info(f"Creating shell tunnel with command: {full_command}")

            # Use a random high port if none specified.
            if not local_port:
                local_port = random.randint(1025, 65535)

            result = self.client.add_tunnel('x', ('127.0.0.1', local_port), (full_command, 0))
            self.logger.info(f"Shell tunnel created: {result}")
        except R2TException as e:
            self.logger.error(f"Failed to create shell tunnel: {e}")
            return False
        finally:
            self.disconnect()

        if auto_connect:
            self.logger.info("Connecting to shell tunnel...")
            return self._connect_to_shell(local_port)

        self.logger.info(f"Shell tunnel ready on 127.0.0.1:{local_port}")
        self.logger.info(f"To connect manually, use: telnet 127.0.0.1 {local_port}")
        return True

    def _connect_to_shell(self, port):
        """Connect to a shell tunnel using telnet"""
        cmd = ['telnet', '127.0.0.1', str(port)]
        try:
            self.logger.info(f"Starting telnet connection to 127.0.0.1:{port}")
            subprocess.run(cmd)
            return True
        except FileNotFoundError:
            self.logger.error("telnet not found. Please install telnet or connect manually:")
            self.logger.info(f"  telnet 127.0.0.1 {port}")
            return False
        except KeyboardInterrupt:
            self.logger.info("Connection interrupted by user")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            return False

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Enhanced RDP2TCP CLI Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  rdp2tcp-cli --config config.yaml tunnel create --name web --type tcp --local-port 8080 --remote-host 192.168.1.10 --remote-port 80
  rdp2tcp-cli tunnel list --format json
  rdp2tcp-cli monitor --duration 300
  rdp2tcp-cli config save --output config.yaml
  rdp2tcp-cli --config config.yaml config load
  rdp2tcp-cli cleanup all
  rdp2tcp-cli --config config.yaml cleanup config
  rdp2tcp-cli cleanup specific --tunnels web-server ssh-access
  rdp2tcp-cli sh --shell-command cmd.exe --connect
  rdp2tcp-cli sh --local-port 4444 --shell-command powershell.exe
        """
    )

    # Global options
    parser.add_argument('--config', '-c', help='Configuration file (YAML or JSON)')
    parser.add_argument('--host', help='Controller host (overrides config)')
    parser.add_argument('--port', type=int, help='Controller port (overrides config)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Log level (overrides config)')

    # Top-level subcommands. dest='action' avoids colliding with the
    # per-tunnel --command option (which stores into dest='process_command').
    subparsers = parser.add_subparsers(dest='action', help='Available commands')

    # Tunnel commands
    tunnel_parser = subparsers.add_parser('tunnel', help='Tunnel management')
    tunnel_subparsers = tunnel_parser.add_subparsers(dest='tunnel_command')

    create_parser = tunnel_subparsers.add_parser('create', help='Create a new tunnel')
    create_parser.add_argument('--name', required=True, help='Tunnel name')
    create_parser.add_argument('--type', required=True,
                               choices=['tcp', 'reverse', 'process', 'socks5'],
                               help='Tunnel type')
    create_parser.add_argument('--local-host', default='127.0.0.1', help='Local host')
    create_parser.add_argument('--local-port', type=int, required=True, help='Local port')
    create_parser.add_argument('--remote-host', help='Remote host (required for tcp/reverse)')
    create_parser.add_argument('--remote-port', type=int, help='Remote port (required for tcp/reverse)')
    create_parser.add_argument('--command', dest='process_command',
                               help='Command for process tunnels')

    delete_parser = tunnel_subparsers.add_parser('delete', help='Delete a tunnel')
    delete_parser.add_argument('--local-host', required=True, help='Local host')
    delete_parser.add_argument('--local-port', type=int, required=True, help='Local port')

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
    config_subparsers.add_parser('load', help='Load tunnels from configuration')

    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup and close tunnels')
    cleanup_subparsers = cleanup_parser.add_subparsers(dest='cleanup_command')
    cleanup_subparsers.add_parser('all', help='Close all active tunnels')
    cleanup_subparsers.add_parser('config', help='Close tunnels defined in configuration')
    cleanup_specific_parser = cleanup_subparsers.add_parser('specific', help='Close specific tunnels')
    cleanup_specific_parser.add_argument('--tunnels', '-t', nargs='+', required=True,
                                         help='Names of tunnels to close')

    # Shell command
    shell_parser = subparsers.add_parser('sh', help='Open a shell (process) tunnel')
    shell_parser.add_argument('--local-port', type=int, default=0,
                              help='Local port (random if not specified)')
    shell_parser.add_argument('--shell-command', default='cmd.exe',
                              help='Command to execute (default: cmd.exe)')
    shell_parser.add_argument('--args', nargs='*',
                              help='Additional arguments for the command')
    shell_parser.add_argument('--connect', action='store_true',
                              help='Automatically connect to the shell tunnel')

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        return 1

    # Load config first, then apply command-line overrides, and only then
    # configure logging once so every setting takes effect.
    cli = RDP2TCPEnhancedCLI(args.config)
    if args.host:
        cli.config.controller_host = args.host
    if args.port:
        cli.config.controller_port = args.port
    if args.log_level:
        cli.config.log_level = args.log_level
    cli.setup_logging()

    try:
        if args.action == 'tunnel':
            if args.tunnel_command == 'create':
                success = cli.tunnel_create(
                    name=args.name,
                    tunnel_type=args.type,
                    local_host=args.local_host,
                    local_port=args.local_port,
                    remote_host=args.remote_host,
                    remote_port=args.remote_port,
                    command=args.process_command,
                )
            elif args.tunnel_command == 'delete':
                success = cli.tunnel_delete(args.local_host, args.local_port)
            elif args.tunnel_command == 'list':
                success = cli.tunnel_list(args.format)
            else:
                parser.parse_args(['tunnel', '--help'])
                return 1

        elif args.action == 'monitor':
            success = cli.monitor(args.tunnel_id, args.duration)

        elif args.action == 'config':
            if args.config_command == 'save':
                success = cli.config_save(args.output)
            elif args.config_command == 'load':
                success = cli.config_load_tunnels()
            else:
                parser.parse_args(['config', '--help'])
                return 1

        elif args.action == 'cleanup':
            if args.cleanup_command == 'all':
                success = cli.cleanup_all_tunnels()
            elif args.cleanup_command == 'config':
                success = cli.cleanup_config_tunnels()
            elif args.cleanup_command == 'specific':
                success = cli.cleanup_tunnels(args.tunnels)
            else:
                parser.parse_args(['cleanup', '--help'])
                return 1

        elif args.action == 'sh':
            success = cli.shell_tunnel(
                local_port=args.local_port,
                command=args.shell_command,
                args=args.args,
                auto_connect=args.connect,
            )

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
