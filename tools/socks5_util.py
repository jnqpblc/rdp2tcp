#!/usr/bin/env python3
"""
/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
Small helpers for speaking SOCKS5 correctly over a stream socket.

TCP is a byte stream, so a single recv() is not guaranteed to return a whole
protocol message. These helpers read exactly as many bytes as each SOCKS5
frame requires, and parse the variable-length reply according to its ATYP.
"""

import socket
import struct

# SOCKS5 address types
ATYP_IPV4 = 0x01
ATYP_DOMAIN = 0x03
ATYP_IPV6 = 0x04

SOCKS5_ERRORS = {
    1: "General SOCKS server failure",
    2: "Connection not allowed by ruleset",
    3: "Network unreachable",
    4: "Host unreachable",
    5: "Connection refused",
    6: "TTL expired",
    7: "Command not supported",
    8: "Address type not supported",
}


class SOCKS5Error(Exception):
    """Raised when a SOCKS5 exchange fails or is malformed."""


def recv_exact(sock, n):
    """Receive exactly ``n`` bytes or raise SOCKS5Error on premature EOF."""
    chunks = []
    remaining = n
    while remaining > 0:
        try:
            chunk = sock.recv(remaining)
        except socket.timeout:
            raise SOCKS5Error(f"timed out waiting for {n} bytes "
                              f"({n - remaining} received)")
        if not chunk:
            raise SOCKS5Error(f"connection closed after {n - remaining}/{n} bytes")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b''.join(chunks)


def socks5_handshake(sock):
    """Perform the no-auth method negotiation. Raises on failure."""
    sock.sendall(b'\x05\x01\x00')
    ver, method = struct.unpack('!BB', recv_exact(sock, 2))
    if ver != 5:
        raise SOCKS5Error(f"unexpected SOCKS version in handshake: {ver}")
    if method != 0:
        raise SOCKS5Error(f"server requires unsupported auth method: {method}")


def build_connect_request(host, port):
    """Build a CONNECT request for a domain name target."""
    domain = host.encode()
    if len(domain) > 255:
        raise SOCKS5Error("domain name too long for SOCKS5")
    return (struct.pack('!BBBB', 5, 1, 0, ATYP_DOMAIN)
            + struct.pack('!B', len(domain)) + domain
            + struct.pack('!H', port))


def read_socks5_reply(sock):
    """Read a full SOCKS5 reply, sized correctly by its ATYP.

    Returns a dict with keys: ver, rep, atyp, addr, port.
    Raises SOCKS5Error if the reply code is non-zero or the frame is malformed.
    """
    header = recv_exact(sock, 4)  # VER REP RSV ATYP
    ver, rep, _rsv, atyp = struct.unpack('!BBBB', header)
    if ver != 5:
        raise SOCKS5Error(f"unexpected SOCKS version in reply: {ver}")

    if atyp == ATYP_IPV4:
        addr_bytes = recv_exact(sock, 4)
        addr = socket.inet_ntop(socket.AF_INET, addr_bytes)
    elif atyp == ATYP_IPV6:
        addr_bytes = recv_exact(sock, 16)
        addr = socket.inet_ntop(socket.AF_INET6, addr_bytes)
    elif atyp == ATYP_DOMAIN:
        length = recv_exact(sock, 1)[0]
        addr = recv_exact(sock, length).decode('idna', errors='replace')
    else:
        raise SOCKS5Error(f"unknown address type in reply: {atyp}")

    port = struct.unpack('!H', recv_exact(sock, 2))[0]

    if rep != 0:
        raise SOCKS5Error(SOCKS5_ERRORS.get(rep, f"unknown SOCKS5 error {rep}"))

    return {'ver': ver, 'rep': rep, 'atyp': atyp, 'addr': addr, 'port': port}
