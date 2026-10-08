# rdp2tcp

rdp2tcp carries TCP connections through an existing Remote Desktop Protocol
(RDP) virtual channel. It is useful when an RDP session is available but a
separate network tunnel is not.

The project has two native components:

- `client/rdp2tcp` runs beside the RDP client on the initiating host. It also
  exposes a local controller, normally on `127.0.0.1:8477`.
- `server/rdp2tcp.exe` runs inside the Windows RDP session and performs the
  remote connection, bind, or process operation.

```text
application -> local listener -> client/rdp2tcp == RDP channel == rdp2tcp.exe -> target
```

## Supported functionality

- TCP forwarding: listen on the RDP client side and connect from Windows.
- Reverse TCP forwarding: listen on Windows and connect back on the RDP client
  side.
- Process forwarding: connect a local TCP listener to a process running in the
  Windows session.
- SOCKS5 TCP `CONNECT`, including IPv4, IPv6, and domain-name destinations.
- A legacy controller script and a structured YAML/JSON-aware CLI.

rdp2tcp transports TCP only. SOCKS authentication, UDP forwarding, bandwidth
limiting, and data compression are not implemented. See
[`tools/FEATURES-CLI.md`](tools/FEATURES-CLI.md) for the current CLI feature
matrix and limitations.

## Requirements

The initiating host needs:

- A C compiler for the POSIX client.
- A compatible RDP client capable of attaching the out-of-process rdp2tcp
  virtual-channel helper. The repository documents patched `rdesktop` and a
  FreeRDP integration using `/rdp2tcp:`.
- Python 3. The enhanced CLI additionally requires PyYAML.

Building the Windows server on a POSIX host requires the 32-bit MinGW-w64
compiler named `i686-w64-mingw32-gcc` by the current Makefile. The compiler can
be changed in `server/Makefile.mingw32` if necessary.

## Build

From the repository root:

```sh
make client       # build client/rdp2tcp
make server       # cross-compile server/rdp2tcp.exe
make              # build both
```

The standard client/server build does not require zlib or LZ4. Compression
source scaffolding exists under `common/`, but it is not connected to the data
path or linked into the normal binaries.

## Start a session

### 1. Start the client-side channel helper

Use an absolute path. The following is the FreeRDP form used by this project;
the option must be available in your FreeRDP build:

```sh
xfreerdp /u:USER /v:WINDOWS_HOST \
  /rdp2tcp:/absolute/path/to/rdp2tcp/client/rdp2tcp
```

Avoid putting a password directly on the command line. With the historical
out-of-process `rdesktop` patch, the equivalent form is:

```sh
rdesktop -r addin:rdp2tcp:/absolute/path/to/rdp2tcp/client/rdp2tcp WINDOWS_HOST
```

The helper accepts an optional controller host and port:

```text
rdp2tcp [CONTROLLER_HOST [CONTROLLER_PORT]]
```

The defaults are `127.0.0.1` and `8477`. If an out-of-process launcher passes
arguments, provide both values when changing the port; for example,
`127.0.0.1 8478`.

### 2. Run the Windows server

Transfer `server/rdp2tcp.exe` into the Windows session and run it from `cmd.exe`:

```bat
rdp2tcp.exe
```

Administrator privileges are not normally required. The optional argument is a
custom virtual-channel name:

```bat
rdp2tcp.exe rdp2tcp-2
```

The name must match the channel configured by the RDP client. Run a separate
server process for each custom channel.

If normal file transfer is unavailable, these helpers generate a PowerShell
payload or an `xte` typing script:

```sh
python3 tools/exe_to_ps1.py -i server/rdp2tcp.exe
python3 tools/exe_to_xte_script_ps1.py -i server/rdp2tcp.exe
```

The generated files may contain the full executable and are intentionally
ignored by Git. `xte` comes from `xautomation`.

### 3. Wait for the channel

The initiating terminal should report:

```text
virtual channel connected
```

The controller is then available on `127.0.0.1:8477` by default.

## Enhanced CLI quick start

Run the CLI from the repository root:

```sh
python3 tools/rdp2tcp-cli.py --help
```

### Forward a local port to the Windows side

This listens locally on `127.0.0.1:10001`. Connections are carried through RDP,
then `rdp2tcp.exe` connects to `127.0.0.1:8000` as seen from Windows.

```sh
python3 tools/rdp2tcp-cli.py tunnel create \
  --name web \
  --type tcp \
  --local-host 127.0.0.1 \
  --local-port 10001 \
  --remote-host 127.0.0.1 \
  --remote-port 8000

curl http://127.0.0.1:10001/
```

### Start a SOCKS5 listener

```sh
python3 tools/rdp2tcp-cli.py tunnel create \
  --name socks \
  --type socks5 \
  --local-host 127.0.0.1 \
  --local-port 19050
```

Configure the application for SOCKS5 at `127.0.0.1:19050`. Use proxy-side DNS
resolution (often called `SOCKS5 hostname`, `socks5h`, or “Proxy DNS when using
SOCKS v5”) when names are resolvable only from the Windows network.

For example:

```sh
curl --proxy socks5h://127.0.0.1:19050 https://example.com/
```

### Create a reverse tunnel

This asks Windows to listen on `127.0.0.1:2222`; accepted connections are sent
through RDP to `127.0.0.1:22` on the initiating side:

```sh
python3 tools/rdp2tcp-cli.py tunnel create \
  --name reverse-ssh \
  --type reverse \
  --local-host 127.0.0.1 \
  --local-port 22 \
  --remote-host 127.0.0.1 \
  --remote-port 2222
```

### Create a process tunnel

The following listens locally and attaches connections to `cmd.exe` in the
Windows session:

```sh
python3 tools/rdp2tcp-cli.py tunnel create \
  --name command-shell \
  --type process \
  --local-host 127.0.0.1 \
  --local-port 4444 \
  --command cmd.exe
```

The convenience command performs the same type of operation and can launch a
local Telnet client:

```sh
python3 tools/rdp2tcp-cli.py sh --local-port 4444 --shell-command cmd.exe
python3 tools/rdp2tcp-cli.py sh --local-port 4444 --shell-command cmd.exe --connect
```

Process tunnels execute commands under the account running `rdp2tcp.exe`; use
them only on systems you are authorized to administer.

### List and delete tunnels

```sh
python3 tools/rdp2tcp-cli.py tunnel list
python3 tools/rdp2tcp-cli.py tunnel list --format json
python3 tools/rdp2tcp-cli.py tunnel delete \
  --local-host 127.0.0.1 --local-port 10001
```

## Configuration files

Copy the sanitized example and edit the private copy:

```sh
cp tools/config.example.yaml tools/config.yaml
python3 tools/rdp2tcp-cli.py --config tools/config.yaml config load
```

Only entries with `enabled: true` are created. `tools/config.yaml` is ignored by
Git because it may contain private addresses or commands; keep
`tools/config.example.yaml` sanitized.

Configuration may be YAML or JSON. Global `--host`, `--port`, and `--log-level`
options override values loaded from the file and must appear before the
subcommand.

## Chaining two RDP sessions

A TCP forward can carry a second SOCKS5 connection unchanged. This allows a
browser on the local computer to reach a site that is accessible only from a
second RDP host:

```text
local browser
    -> SOCKS5 127.0.0.1:19050
    -> first rdp2tcp session (local -> box A)
    -> box A 127.0.0.1:19051
    -> second rdp2tcp SOCKS5 session (box A -> box B)
    -> internal website, connected from box B
```

Box A has two roles: it runs `rdp2tcp.exe` for the first session and the
client-side helper/controller for the second session.

### On box A

Establish the RDP session from box A to box B with the rdp2tcp client helper,
run `rdp2tcp.exe` on box B, and create the second-hop SOCKS listener:

```sh
python3 tools/rdp2tcp-cli.py tunnel create \
  --name hop2-socks \
  --type socks5 \
  --local-host 127.0.0.1 \
  --local-port 19051
```

### On the local computer

Forward a local port through the first RDP session to box A's second-hop SOCKS
listener:

```sh
python3 tools/rdp2tcp-cli.py tunnel create \
  --name chained-socks \
  --type tcp \
  --local-host 127.0.0.1 \
  --local-port 19050 \
  --remote-host 127.0.0.1 \
  --remote-port 19051
```

Configure the browser for SOCKS5 at `127.0.0.1:19050` with proxy-side DNS.

This works without a protocol change only when box A can run a compatible
client-side helper for its session to box B. The current client is POSIX code
connected to an out-of-process FreeRDP/rdesktop channel. It is not an MSTSC
plugin. If box A is Windows and the second session must use `mstsc.exe`, a
Windows RDP client virtual-channel plugin or a native FreeRDP client extension
is required.

If box A can already reach the destination directly, a SOCKS listener on the
first session is sufficient and the second hop is unnecessary.

## Tunnel direction reference

| Type | Listener | Final connection or action |
| --- | --- | --- |
| `tcp` | RDP client side (`local_host:local_port`) | Windows connects to `remote_host:remote_port` |
| `reverse` | Windows (`remote_host:remote_port`) | RDP client side connects to `local_host:local_port` |
| `process` | RDP client side | Windows starts `command` and forwards stdin/stdout |
| `socks5` | RDP client side | Windows makes each SOCKS5 TCP connection |

The raw controller protocol uses newline-terminated ASCII commands:

```text
l
t LHOST LPORT RHOST RPORT
r LHOST LPORT RHOST RPORT
x LHOST LPORT COMMAND
s LHOST LPORT
- LHOST LPORT
```

The simpler legacy wrapper remains available:

```sh
python3 tools/rdp2tcp.py info
python3 tools/rdp2tcp.py add forward 127.0.0.1 10001 127.0.0.1 8000
python3 tools/rdp2tcp.py add socks5 127.0.0.1 19050
python3 tools/rdp2tcp.py del 127.0.0.1 10001
```

## Security and operational notes

- Bind the controller and tunnel listeners to `127.0.0.1` unless remote access
  is explicitly required and protected by another control.
- The controller protocol and SOCKS5 listener do not authenticate clients.
- A SOCKS listener exposed on a non-loopback address can become an open proxy.
- RDP session loss interrupts every tunnel carried by that session; a chained
  tunnel depends on both sessions.
- Chaining adds latency and traverses both virtual channels for every byte.
- SOCKS5 supports TCP `CONNECT` only. UDP-based traffic such as QUIC/HTTP/3 is
  not tunneled; applications may fall back to TCP.
- Tunnel names are CLI/configuration labels, not persistent controller IDs.
- The CLI's `monitor --tunnel-id` option is currently accepted but does not
  filter the polling output.

## Development

- Uncomment `-DDEBUG` in the relevant Makefile to build debug logging.
- Set `DEBUG` and `TRACE` environment variables to control the legacy debug
  output.
- `client/memcheck.sh` runs the client under Valgrind from the `client/`
  directory.
- Doxygen configuration is provided in `Doxyfile-client` and
  `Doxyfile-server`.
- Live integration scripts under `tools/test-*.py` require an RDP session and
  controller. The scripts that use `tools/testutil.py` require explicit opt-in
  with `RDP2TCP_RUN_INTEGRATION=1` or `--run`; inspect other diagnostic scripts
  before running them against an active session.

## License

rdp2tcp is distributed under the GNU General Public License version 3 or later.
See [`COPYING`](COPYING).
