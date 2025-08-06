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

def main():
    parser = argparse.ArgumentParser(description="Compress and base64-encode a binary file into a PowerShell script that writes it back to disk.")
    parser.add_argument("-i", "--infile", help="Input binary file to compress and encode", required=True)
    parser.add_argument("-o", "--outfile", help="Output PowerShell script", default="server/rdp2tcp.ps1")
    parser.add_argument("-b", "--output-bin-name", help="Filename to write on the target system (default: same as input file name)", default=None)
    args = parser.parse_args()

    infile = args.infile
    outfile = args.outfile
    output_bin_name = args.output_bin_name or path.basename(infile)

    try:
        with open(infile, 'rb') as f:
            data = f.read()
    except Exception as e:
        exit(1)

    b64_data = compress_and_encode(data)
    ps_script = generate_powershell_script(b64_data, output_bin_name)

    try:
        with open(outfile, 'w') as f:
            f.write(ps_script)
        print(f"\n[+] Wrote the PS1 script to {outfile}\n\t Run: cat {outfile} |xclip -selection clipboard")
    except Exception as e:
        stderr.write(f"Failed to write output: {e}\n")
        exit(1)

if __name__ == '__main__':
    main()
