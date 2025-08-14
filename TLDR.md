# TLDR
```
$ make
$ python3 tools/exe_to_ps1.py -i server/rdp2tcp.exe
$ xfreerdp /w:1368 /h:768 /bpp:16 /jpeg /jpeg-quality:50 /v:{SERVER_IP} /u:{USER} /rdp2tcp:`pwd`/client/rdp2tcp +clipboard
$ cat server/rdp2tcp.ps1 |xclip -selection clipboard
$ python3 tools/rdp2tcp.py add socks5 127.0.0.1 19050
$ sudo nano /etc/proxychains4.conf
$ proxychains4 python3 bloodhound.py -u jnqpblc -p {PWD} -ns {DC_IP} --dns-tcp -d {DOM} --zip -c DCOnly
```
