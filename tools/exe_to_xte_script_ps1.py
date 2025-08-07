#!/usr/bin/env python3
import argparse
import base64
import zlib
from sys import argv, stderr, exit
from os import path

def compress_and_encode(data):
    compressed = zlib.compress(data, level=9)
    return base64.b64encode(compressed).decode()

def generate_powershell_script(encoded_data, output_filename):
    ps_script = f'''
$b64 = "{encoded_data}"

$compressed = [Convert]::FromBase64String($b64)

$ms = New-Object System.IO.MemoryStream

$null = $ms.Write($compressed, 2, $compressed.Length - 2)

$null = $ms.Seek(0, 0)

$ds = New-Object System.IO.Compression.DeflateStream($ms,[System.IO.Compression.CompressionMode]::Decompress)

$out = New-Object System.IO.MemoryStream

$ds.CopyTo($out)

$ms.Close()

$ds.Close()

$outputPath = Join-Path $env:USERPROFILE "{output_filename}"

[System.IO.File]::WriteAllBytes($outputPath, $out.ToArray())

$out.Close()
'''
    return ps_script

def encode_xte(text, focus_delay, sleep):
    from io import BytesIO
    output = BytesIO()
    total_seconds = focus_delay  # Start with initial focus delay

    def xsleep(t):
        nonlocal total_seconds
        adjusted = t * sleep
        total_seconds += adjusted
        output.write(f'usleep {int(adjusted * 1_000_000)}\n'.encode())

    special_key_map = {
        '\n': 'Return',
        '\t': 'Tab',
        ' ': 'space',
        '/': 'slash',
        '\\': 'backslash',
        '.': 'period',
        ',': 'comma',
        ';': 'semicolon',
        ':': 'colon',
        '\'': 'apostrophe',
        '"': 'quotedbl',
        '[': 'bracketleft',
        ']': 'bracketright',
        '{': ('Shift_L', 'bracketleft'),
        '}': ('Shift_L', 'bracketright'),
        '(': ('Shift_L', '9'),
        ')': ('Shift_L', '0'),
        '!': ('Shift_L', '1'),
        '@': ('Shift_L', '2'),
        '#': ('Shift_L', '3'),
        '$': ('Shift_L', '4'),
        '%': ('Shift_L', '5'),
        '^': ('Shift_L', '6'),
        '&': ('Shift_L', '7'),
        '*': ('Shift_L', '8'),
        '+': ('Shift_L', 'equal'),
        '=': 'equal',
        '-': 'minus',
        '_': ('Shift_L', 'minus'),
        '?': ('Shift_L', 'slash'),
        '<': ('Shift_L', 'comma'),
        '>': ('Shift_L', 'period'),
        '|': ('Shift_L', 'backslash'),
        '`': 'grave',
        '~': ('Shift_L', 'grave'),
    }

    output.write(f'usleep {int(focus_delay * 1_000_000)}\n'.encode())

    for line in text.splitlines():
        buffer = ''
        for c in line:
            if c in special_key_map:
                if buffer:
                    output.write(f'str {buffer}\n'.encode())
                    xsleep(0.08)
                    buffer = ''
                key = special_key_map[c]
                if isinstance(key, tuple):
                    output.write(f'keydown {key[0]}\n'.encode())
                    output.write(f'key {key[1]}\n'.encode())
                    output.write(f'keyup {key[0]}\n'.encode())
                else:
                    output.write(f'key {key}\n'.encode())
                xsleep(0.05)
            else:
                output.write(f'str {c}\n'.encode())
                xsleep(0.02)

        if buffer:
            output.write(f'str {buffer}\n'.encode())
            xsleep(0.08)
        output.write(b'key Return\n')
        xsleep(0.1)

    return output.getvalue(), total_seconds

def main():
    parser = argparse.ArgumentParser(description="Compress and base64-encode a binary file into a PowerShell script that writes it back to disk.")
    parser.add_argument("-i", "--infile", help="Input binary file to compress and encode", required=True)
    parser.add_argument("-o", "--outfile", help="Output PowerShell script", default="server/rdp2tcp_ps1.xte")
    parser.add_argument("-b", "--output-bin-name", help="Filename to write on the target system (default: same as input file name)", default=None)
    parser.add_argument("-d", "--delay", help="Delay before typing starts (default: 10.0 sec)", default=10.0)
    parser.add_argument("-s", "--sleep", help="Sleep multiplier between keystrokes (default: 2.0)", default=2.0)
    args = parser.parse_args()

    infile = args.infile
    outfile = args.outfile
    delay = float(args.delay)
    sleep = float(args.sleep)
    output_bin_name = args.output_bin_name or path.basename(infile)

    try:
        with open(infile, 'rb') as f:
            data = f.read()
    except Exception as e:
        exit(1)

    b64_data = compress_and_encode(data)
    ps_script = generate_powershell_script(b64_data, output_bin_name)
    xte_script_bytes, total_time = encode_xte(ps_script, delay, sleep)
    print(f"[+] Estimated time to execute xte script: {total_time/60:.1f} minutes ({total_time/3600:.1f} hours)")

    try:
        with open(outfile, 'wb') as f:
            f.write(xte_script_bytes)
        print(f"\n[+] Wrote the XTE script to {outfile}\n\t Run: cat {outfile} |xte")
    except Exception as e:
        stderr.write(f"Failed to write output: {e}\n")
        exit(1)

if __name__ == '__main__':
    main()
