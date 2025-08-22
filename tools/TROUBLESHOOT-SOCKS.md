# SOCKS5 Troubleshooting Guide

## Problem Description
The SOCKS5 tunnel is running on port 19050, but connections are being reset immediately after the handshake attempt.

## Root Cause Analysis

### 1. **RDP Connection Issues**
The most likely cause is that the RDP2TCP server is not properly connected or the RDP session is not active.

**Check:**
```bash
# Check if RDP2TCP server is running on the remote machine
# Look for rdp2tcp.exe process in Task Manager

# Check if the RDP session is active
# The SOCKS5 server needs an active RDP connection to work
```

### 2. **Server-Side SOCKS5 Implementation**
The SOCKS5 implementation might have issues with the handshake response.

**Symptoms:**
- Connection accepted but immediately reset
- No response to SOCKS5 handshake
- Port is open but protocol not working

### 3. **Network/Firewall Issues**
Firewall or network policies might be interfering.

## Troubleshooting Steps

### Step 1: Verify RDP Connection
```bash
# Check if the RDP session is active
# Look for rdp2tcp.exe in the remote machine's process list
# Ensure you're connected via RDP to the target machine
```

### Step 2: Test Basic Connectivity
```bash
# Test if the port is actually listening
nc -zv 127.0.0.1 19050

# Test with telnet
telnet 127.0.0.1 19050
# If it connects, try sending: 05 01 00
# Should get response: 05 00
```

### Step 3: Check RDP2TCP Server Logs
Look for any error messages in the RDP2TCP server output or Windows Event Logs.

### Step 4: Alternative SOCKS5 Port
Try using a different port:
```bash
# Update config.yaml to use port 1080
local_port: 1080

# Recreate the tunnel
python3 tools/rdp2tcp-cli.py tunnel delete 127.0.0.1 19050
python3 tools/rdp2tcp-cli.py --config tools/config.yaml config load
```

### Step 5: Test with Different Tools
```bash
# Test with curl
curl --socks5 127.0.0.1:19050 -v http://httpbin.org/ip

# Test with proxychains
proxychains4 -f tools/proxychains-test.conf curl -v http://httpbin.org/ip

# Test with our debug script
python3 tools/debug-socks5.py 19050
```

## Alternative Solutions

### 1. **Use TCP Tunnel Instead**
If SOCKS5 continues to fail, use a TCP tunnel to a local SOCKS5 proxy:

```bash
# Install a local SOCKS5 proxy (like dante-server)
sudo apt-get install dante-server

# Create a TCP tunnel to the remote SOCKS5 proxy
python3 tools/rdp2tcp-cli.py tunnel create --name socks-tunnel --type tcp --local 1080 --remote 127.0.0.1 1080
```

### 2. **Use SSH Tunnel as Alternative**
```bash
# If SSH is available on the remote machine
ssh -D 1080 user@remote-machine
```

### 3. **Use Reverse Tunnel**
```bash
# Create a reverse tunnel from remote to local
python3 tools/rdp2tcp-cli.py tunnel create --name reverse-socks --type reverse --local 1080 --remote 127.0.0.1 1080
```

## Debugging Commands

### Check Tunnel Status
```bash
python3 tools/rdp2tcp-cli.py tunnel list
```

### Monitor Tunnel Activity
```bash
python3 tools/rdp2tcp-cli.py monitor --duration 60
```

### Test SOCKS5 Protocol
```bash
python3 tools/debug-socks5.py 19050
```

## Common Issues and Solutions

### Issue 1: "Connection reset by peer"
**Cause:** RDP connection not active or server not responding
**Solution:** Ensure RDP session is active and rdp2tcp.exe is running

### Issue 2: "No response to handshake"
**Cause:** SOCKS5 implementation issue
**Solution:** Try different port or use TCP tunnel alternative

### Issue 3: "Port already in use"
**Cause:** Another service using the port
**Solution:** Change port in config or stop conflicting service

### Issue 4: "DNS resolution fails"
**Cause:** SOCKS5 proxy not handling DNS properly
**Solution:** Use IP addresses instead of hostnames or configure DNS properly

## Verification Checklist

- [ ] RDP session is active
- [ ] rdp2tcp.exe is running on remote machine
- [ ] Port 19050 is open and listening
- [ ] No firewall blocking the connection
- [ ] SOCKS5 handshake receives response
- [ ] DNS resolution works through proxy
- [ ] HTTP requests work through proxy

## Next Steps

If SOCKS5 continues to fail:

1. **Use TCP tunnel** to a local SOCKS5 proxy
2. **Use SSH tunnel** if available
3. **Check RDP2TCP server logs** for errors
4. **Try different ports** (1080, 9050, etc.)
5. **Use alternative tunneling tools** (SSH, netcat, etc.)
