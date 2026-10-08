# Enhanced CLI and multi-hop usage

`rdp2tcp-cli.py` is the structured Python 3 interface to the local rdp2tcp
controller. It manages the same controller protocol as `rdp2tcp.py`, while
adding configuration files, structured list output, cleanup helpers, polling,
and a process-tunnel convenience command.

Run it from the repository root:

```sh
python3 tools/rdp2tcp-cli.py --help
```

PyYAML is required for the enhanced CLI, including when JSON configuration is
used, because the module is imported at startup.

## Current feature status

| Capability | Status | Notes |
| --- | --- | --- |
| TCP forwarding | Supported | Local listener; connection originates on Windows |
| Reverse TCP forwarding | Supported | Windows listener; connection originates on the RDP client side |
| Process stdin/stdout forwarding | Supported | Starts a process in the Windows session |
| SOCKS5 | Supported for TCP `CONNECT` | No authentication, `BIND`, or UDP support |
| IPv4, IPv6, and SOCKS domain names | Supported | Domain names are resolved from the Windows side |
| YAML/JSON configuration | Supported | Only enabled entries are created |
| Raw text (`table`), JSON, and YAML list output | Supported | Diagnostics go to stderr |
| Tunnel polling | Supported | Polls the full controller list every five seconds |
| Named cleanup | Supported through config | Names are mapped to configured listener addresses |
| Data compression | Not implemented | Protocol/source scaffolding exists; handlers ignore it |
| Bandwidth limiting/QoS | Not implemented | No controller or data-path support |
| Advanced C structured logging | Not integrated | Source exists under `common/`, but normal binaries do not link or initialize it |

The CLI deliberately does not expose compression or bandwidth-limit command
options. A configuration requesting non-`none` compression or a bandwidth
limit is rejected rather than silently accepted.

## Global options

Global options must appear before the command:

```text
--config, -c FILE   Load YAML or JSON configuration
--host HOST         Override the controller host
--port PORT         Override the controller port
--log-level LEVEL   DEBUG, INFO, WARNING, or ERROR
```

Example:

```sh
python3 tools/rdp2tcp-cli.py \
  --config tools/config.yaml \
  --host 127.0.0.1 \
  --port 8477 \
  tunnel list --format json
```

CLI diagnostics are written to stderr, keeping JSON and YAML on stdout usable
by other programs. If `log_file` is set in configuration, the same diagnostics
are also written to that file.

## Tunnel commands

### TCP forwarding

Listen on the RDP client side and ask Windows to connect to the destination:

```sh
python3 tools/rdp2tcp-cli.py tunnel create \
  --name web \
  --type tcp \
  --local-host 127.0.0.1 \
  --local-port 8080 \
  --remote-host 192.0.2.10 \
  --remote-port 80
```

### Reverse forwarding

Ask Windows to listen on `remote-host:remote-port`, then forward accepted
connections to `local-host:local-port` on the RDP client side:

```sh
python3 tools/rdp2tcp-cli.py tunnel create \
  --name reverse-ssh \
  --type reverse \
  --local-host 127.0.0.1 \
  --local-port 22 \
  --remote-host 127.0.0.1 \
  --remote-port 2222
```

### SOCKS5

```sh
python3 tools/rdp2tcp-cli.py tunnel create \
  --name socks \
  --type socks5 \
  --local-host 127.0.0.1 \
  --local-port 19050
```

Use proxy-side DNS when the hostname is resolvable only from Windows:

```sh
curl --proxy socks5h://127.0.0.1:19050 https://example.com/
```

### Process tunnels

```sh
python3 tools/rdp2tcp-cli.py tunnel create \
  --name command-shell \
  --type process \
  --local-host 127.0.0.1 \
  --local-port 4444 \
  --command cmd.exe
```

The `sh` convenience command creates a process tunnel bound to loopback. It
selects a random high port when `--local-port` is omitted:

```sh
python3 tools/rdp2tcp-cli.py sh --shell-command cmd.exe
python3 tools/rdp2tcp-cli.py sh \
  --local-port 4444 \
  --shell-command powershell.exe \
  --connect
```

`--connect` launches the local `telnet` program. The remote command executes
under the account running `rdp2tcp.exe`.

### List, monitor, and delete

```sh
python3 tools/rdp2tcp-cli.py tunnel list
python3 tools/rdp2tcp-cli.py tunnel list --format json
python3 tools/rdp2tcp-cli.py tunnel list --format yaml

python3 tools/rdp2tcp-cli.py monitor --duration 300

python3 tools/rdp2tcp-cli.py tunnel delete \
  --local-host 127.0.0.1 \
  --local-port 8080
```

Monitoring currently prints the complete controller status every five seconds.
`--tunnel-id` is accepted by the parser but is not yet used to filter results.

## Configuration management

Start with the sanitized example:

```sh
cp tools/config.example.yaml tools/config.yaml
```

`tools/config.yaml` is ignored by Git because real configurations may contain
private addresses and commands. Keep examples in `tools/config.example.yaml`
disabled and free of environment-specific data.

Minimal configuration:

```yaml
controller_host: "127.0.0.1"
controller_port: 8477
log_level: "INFO"
log_file: null

tunnels:
  - name: "socks-proxy"
    type: "socks5"
    local_host: "127.0.0.1"
    local_port: 19050
    enabled: false

  - name: "web-forward"
    type: "tcp"
    local_host: "127.0.0.1"
    local_port: 8080
    remote_host: "192.0.2.10"
    remote_port: 80
    enabled: false
```

Create all enabled entries:

```sh
python3 tools/rdp2tcp-cli.py --config tools/config.yaml config load
```

Cleanup commands operate only on listener rows (`tunsrv`, `s5srv`, and
`rtunsrv`), never per-connection client rows:

```sh
# Close every listener reported by the controller
python3 tools/rdp2tcp-cli.py cleanup all

# Close enabled listeners that match entries in the loaded config
python3 tools/rdp2tcp-cli.py --config tools/config.yaml cleanup config

# Close selected configured names; host and port must match the config
python3 tools/rdp2tcp-cli.py --config tools/config.yaml cleanup specific \
  --tunnels web-forward socks-proxy
```

Tunnel names are local configuration labels. They are not sent to, stored by,
or returned from the native controller.

Save the currently loaded/default configuration model as YAML or JSON:

```sh
python3 tools/rdp2tcp-cli.py \
  --config tools/config.yaml \
  config save --output tools/config.local.yaml
```

`config save` does not discover active tunnels from the controller.

## Chaining two RDP sessions

No protocol change is required to carry a second-hop SOCKS connection through
a first-hop TCP forward:

```text
browser on local computer
    -> local SOCKS5 127.0.0.1:19050
    -> first RDP channel to box A
    -> box A second-hop SOCKS listener 127.0.0.1:19051
    -> second RDP channel to box B
    -> internal destination, connected from box B
```

Box A runs both halves needed for the chain:

- `rdp2tcp.exe` is the server for the local-computer-to-box-A session.
- `client/rdp2tcp` is the client helper for the box-A-to-box-B session.

### Configure the second hop on box A

After starting a compatible RDP client/helper from box A to box B and running
`rdp2tcp.exe` on box B:

```sh
python3 tools/rdp2tcp-cli.py tunnel create \
  --name hop2-socks \
  --type socks5 \
  --local-host 127.0.0.1 \
  --local-port 19051
```

The SOCKS listener is on box A, but each requested connection originates from
box B.

### Carry that SOCKS listener through the first hop

On the local computer:

```sh
python3 tools/rdp2tcp-cli.py tunnel create \
  --name chained-socks \
  --type tcp \
  --local-host 127.0.0.1 \
  --local-port 19050 \
  --remote-host 127.0.0.1 \
  --remote-port 19051
```

Configure the browser for SOCKS5 at `127.0.0.1:19050` and enable proxy-side
DNS. Every byte crosses both RDP virtual channels, so expect additional latency
and dependence on both sessions remaining connected.

### Platform limitation

The current client helper is POSIX code that communicates with a compatible
FreeRDP/rdesktop out-of-process channel. It is not a Microsoft MSTSC plugin.
Therefore:

- No extension is needed if box A can run the compatible client helper for its
  RDP session to box B.
- If box A is Windows and must open the second session with `mstsc.exe`, the
  project needs a Windows RDP client virtual-channel plugin or a native FreeRDP
  client-side integration.
- If box A can already reach the internal destination, use a first-hop SOCKS5
  listener instead of chaining.

## Security and behavior notes

- Keep the controller, SOCKS listeners, and tunnel listeners on `127.0.0.1`
  unless exposure is deliberate and independently protected.
- The controller protocol and SOCKS5 implementation have no authentication.
- SOCKS5 supports TCP `CONNECT`; it does not support UDP association, SOCKS
  `BIND`, or authentication methods.
- Process tunnels are remote command execution functionality. Treat access to
  the local listener as privileged.
- Controller operations have a default ten-second socket timeout.
- Loss of the RDP channel closes or interrupts dependent connections.

## Developer-only scaffolding

`common/compress.c`, `common/compress.h`, and `R2TCMD_COMPRESS` define proposed
compression support. The normal client and server Makefiles do not link the
compression object, and both command handlers currently ignore compression
messages. Compression must not be described or treated as active.

Similarly, `common/logger.c` provides an advanced structured C logger, but the
normal client/server binaries neither link nor initialize it. The enhanced
Python CLI uses Python's standard logging module; that is separate from the C
logger implementation.

Integration test scripts can create listeners, processes, or network traffic.
Those guarded by `tools/testutil.py` require explicit opt-in:

```sh
RDP2TCP_RUN_INTEGRATION=1 python3 tools/test-socks5.py
# or
python3 tools/test-socks5.py --run
```
