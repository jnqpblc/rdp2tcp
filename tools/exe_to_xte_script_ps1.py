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
    ps_script = f'''$b64 = "{encoded_data}"
$compressed = [Convert]::FromBase64String($b64)
$ms = New-Object System.IO.MemoryStream
$ms.Write($compressed, 2, $compressed.Length - 2)
$ms.Seek(0, 0) | Out-Null

$ds = New-Object System.IO.Compression.DeflateStream($ms, [System.IO.Compression.CompressionMode]::Decompress)
$out = New-Object System.IO.MemoryStream
$ds.CopyTo($out)
$ms.Close()

[System.IO.File]::WriteAllBytes("$env:USERPROFILE\\{output_filename}", $out.ToArray())
$out.Close()
'''
    return ps_script

def encode_xte(text, focus_delay, sleep):
    from io import BytesIO
    output = BytesIO()

    def xsleep(t):
        output.write(f'usleep {int(t * 1000000 * sleep)}\n'.encode())

    special_key_map = {
        '\n': 'Return',
        '\t': 'Tab',
        ' ': 'space',
        '+': 'plus',
        '/': 'slash',
        '=': 'equal',
    }

    output.write(f'usleep {int(focus_delay)}\n'.encode())

    for line in text.splitlines():
        buffer = ''
        for c in line:
            if c in special_key_map:
                if buffer:
                    output.write(f'str {buffer}\n'.encode())
                    xsleep(0.08)
                    buffer = ''
                output.write(f'key {special_key_map[c]}\n'.encode())
                xsleep(0.05)
            else:
                buffer += c

        if buffer:
            output.write(f'str {buffer}\n'.encode())
            xsleep(0.08)
        output.write(b'key Return\n')
        xsleep(0.1)

    return output.getvalue()

def main():
    parser = argparse.ArgumentParser(description="Compress and base64-encode a binary file into a PowerShell script that writes it back to disk.")
    parser.add_argument("-i", "--infile", help="Input binary file to compress and encode", required=True)
    parser.add_argument("-o", "--outfile", help="Output PowerShell script", default="server/rdp2tcp_ps1.xte")
    parser.add_argument("-b", "--output-bin-name", help="Filename to write on the target system (default: same as input file name)", default=None)
    parser.add_argument("-d", "--delay", help="Delay before typing starts (default: 10.0 sec)", default=10.0)
    parser.add_argument("-s", "--sleep", help="Sleep multiplier between keystrokes (default: 5.0)", default=5.0)
    args = parser.parse_args()

    infile = args.infile
    outfile = args.outfile
    delay = args.delay
    sleep = args.sleep
    output_bin_name = args.output_bin_name or path.basename(infile)

    try:
        with open(infile, 'rb') as f:
            data = f.read()
    except Exception as e:
        exit(1)

    b64_data = compress_and_encode(data)
    ps_script = generate_powershell_script(b64_data, output_bin_name)
    xte_script_bytes = encode_xte(ps_script, delay, sleep)

    try:
        with open(outfile, 'wb') as f:
            f.write(xte_script_bytes)
        print(f"\n[+] Wrote the XTE script to {outfile}\n\t Run: cat {outfile} |xte")
    except Exception as e:
        stderr.write(f"Failed to write output: {e}\n")
        exit(1)

if __name__ == '__main__':
    main()
