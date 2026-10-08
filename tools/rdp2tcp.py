#!/usr/bin/env python
import socket
from random import randint
from time import sleep
from os import system

DEFAULT_TIMEOUT = 10.0

def connect_to(host, port, timeout=DEFAULT_TIMEOUT):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
	s.settimeout(timeout)
	s.connect((host, port))
	return s

class R2TException(Exception):
	pass

server_type_names = {\
	'ctrl':'controller',\
	'tun':'tunnel',\
	'rtun':'tunnel',\
	's5':'socks5'
}

class R2TServer:

	def __init__(self, type, lhost, rhost=None, rev=False):
		self.type    = type
		self.lhost   = lhost
		self.rhost   = rhost
		self.reverse = rev
		self.clients = []

	def __str__(self):
		global server_type_names
		out = server_type_names[self.type] + ' ' + self.lhost
		if self.rhost:
			out += ' %s %s' % (self.reverse and '<--' or '-->', self.rhost)
		return out

class R2TClient:
	def __init__(self, rhost):
		self.rhost = rhost
	def __str__(self):
		return self.rhost

class rdp2tcp:

	def __init__(self, host, port, timeout=DEFAULT_TIMEOUT):
		try:
			s = connect_to(host, port, timeout)
		except socket.error as e:
			raise R2TException(str(e))
		self.sock = s

	def close(self):
		self.sock.close()

	def __read_answer(self, end_marker='\n'):
		marker = end_marker.encode()
		data = b''
		while True:
			# Controller errors are always terminated by a single newline,
			# even when we are waiting for a longer delimiter (e.g. '\n\n').
			if data.startswith(b'error: ') and b'\n' in data:
				raise R2TException(data[7:data.find(b'\n')].decode())
			if marker in data:
				break
			try:
				chunk = self.sock.recv(4096)
			except socket.timeout:
				raise R2TException('timed out waiting for controller response')
			if not chunk:
				# EOF before the expected delimiter: never report a truncated
				# response (or an empty one) as success.
				raise R2TException(
					'controller closed the connection before sending a complete response')
			data += chunk
		return data[:data.find(marker)].decode()

	def info(self):
		self.sock.sendall('l\n'.encode())
		return self.__read_answer('\n\n')

	def add_tunnel(self, type, src, dst):
		msg = '%s %s %i %s' % (type, src[0], src[1], dst[0])
		if type != 'x': msg += ' %i' % dst[1]
		self.sock.sendall((msg + '\n').encode())
		return self.__read_answer()

	def del_tunnel(self, src):
		self.sock.sendall(('- %s %i\n' % src).encode())
		return self.__read_answer()


if __name__ == '__main__':
	from sys import argv, exit, stdin, stdout

	def usage():
		print("""
usage: %s [-h host] [-p port] <cmd> [args..]

commands:
   info
   add forward <lhost> <lport> <rhost> <rport>
   add reverse <lhost> <lport> <rhost> <rport>
   add process <lhost> <lport> <command>
   add socks5  <lhost> <lport>
   del <lhost> <lport>
   sh [args]""" % argv[0])
		exit(0)

	
	def popup_telnet(x, type, dst):

		laddr = ('127.0.0.1', randint(1025, 0xffff))
		try:
			print(x.add_tunnel(type, laddr, dst))
		except R2TException as e:
			print('error:', e)
			return

		try:
			system('xterm -e telnet %s %i &' % laddr)
			sleep(0.8)
		except(KeyboardInterrupt):
			stdout.write('\n')

		try:
			print(x.del_tunnel(laddr))
		except R2TException as e:
			print('error:', e)


	argc = len(argv)
	if argc < 2:
		usage()

	host,port = '127.0.0.1',8477

	i = 1
	while i < argc and argv[i].startswith('-'):
		opt = argv[i]
		if opt in ('--help',):
			usage()
		if opt not in ('-h', '-p'):
			print('error: unknown option %s' % opt)
			usage()
		if i + 1 >= argc:
			print('error: option %s requires an argument' % opt)
			usage()
		val = argv[i + 1]
		if opt == '-h':
			host = val
		else:
			try:
				port = int(val)
			except ValueError:
				print('error: invalid port: %s' % val)
				usage()
		i += 2

	if i >= argc:
		usage()

	cmd = argv[i]
	if cmd not in ('info','add','del','sh','telnet'):
		usage()

	try:
		r2t = rdp2tcp(host, port)
	except R2TException as e:
		print('error: %s' % str(e))
		exit(0)
	
	argc -= i + 1
	if cmd == 'add':
		argc -= 1
		arg = argv[i+1]
		if arg == 'forward' and argc == 4:
			type = 't'
			src,dst = (argv[i+2], int(argv[i+3])),(argv[i+4], int(argv[i+5]))
		elif arg == 'reverse' and argc == 4:
			type = 'r'
			src,dst = (argv[i+2], int(argv[i+3])),(argv[i+4], int(argv[i+5]))
		elif arg == 'process' and argc == 3:
			type = 'x'
			src,dst = (argv[i+2], int(argv[i+3])),(argv[i+4], 0)
		elif arg == 'socks5' and argc == 2:
			type = 's'
			src,dst = (argv[i+2], int(argv[i+3])),('', 0)
		else:
			usage()

		try:
			print(r2t.add_tunnel(type, src, dst))
		except R2TException as e:
			print('error: %s' % str(e))

	elif cmd == 'del':
		if argc != 2: usage()

		try:
			print(r2t.del_tunnel((argv[i+1], int(argv[i+2]))))
		except R2TException as e:
			print('error: %s' % str(e))

	elif cmd == 'info':
		print(r2t.info())

	elif cmd == 'sh':
		proc = 'cmd.exe'
		if argc >= 1:
			proc += ' /C ' + ' '.join(argv[i+1:])
		popup_telnet(r2t, 'x', (proc, 0))

	elif cmd == 'telnet':
		if argc != 2:
			usage()
		popup_telnet(r2t, 't', (argv[i+1], int(argv[i+2])))

	r2t.close()
	
