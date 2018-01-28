#! /usr/bin/env python
# -*- coding: utf-8 -*-
#======================================================================
#
# fasd.py - 
#
# Created by skywind on 2018/01/27
# Last change: 2018/01/27 00:19:27
#
#======================================================================
from __future__ import print_function
import sys
import time
import os
import shutil
import codecs
import random
import re


#----------------------------------------------------------------------
# data file
#----------------------------------------------------------------------
class FasdData (object):

	def __init__ (self, filename, owner = None):
		if '~' in filename:
			filename = os.path.expanduser(filename)
		self.name = filename
		self.user = owner
		self.mode = -1
		self.home = os.path.expanduser('~')
		self.unix = (sys.platform[:3] != 'win')
		self.nocase = False
		self.maxage = 2000
		self.exclude = []

	# load z/fasd compatible file to a list of [path, rank, atime, 0]
	def load (self):
		data = []
		try:
			with codecs.open(self.name, 'r', encoding = 'utf-8') as fp:
				for line in fp:
					part = line.split('|')
					if len(part) != 3:
						continue
					path = part[0]
					rank = part[1].isdigit() and int(part[1]) or 0
					atime = part[2].rstrip('\n')
					atime = atime.isdigit() and int(atime) or 0
					score = 0
					data.append([path, rank, atime, score])
		except IOError:
			return []
		return data

	# save data into text file in the line format of "path|rank|atime" 
	def save (self, data):
		def make_tempname(filename):
			if sys.platform[:3] == 'win':
				ts = int(time.time() * 1000)
				ts = hex(ts)[2:]
			else:
				ts = int(time.time() * 1000000)
				ts = hex(ts)[2:]
			ts += hex(random.randrange(65536))[2:]
			return filename + '.' + ts.lower()
		tmpname = self.make_tempname()
		retval = 0
		try:
			with codecs.open(tmpname, 'w', encoding = 'utf-8') as fp:
				for path, rank, atime, _ in data:
					fp.write('%s|%d|%d\n'%(path, rank, atime))
			if self.unix:
				if self.user:
					import pwd
					user = pwd.getpwnam(self.user)
					uid = user.pw_uid
					gid = user.pw_gid
					os.chown(self.name, uid, gid)
				if self.mode > 0:
					os.chmod(self.name, self.mode)
			shutil.move(tmpname, self.name)
		except IOError:
			retval = -1
		if os.path.exists(tmpname):
			try:
				os.remove(tmpname)
			except:
				pass
		return retval

	# check existence and filter
	def filter (self, data, what = 'a'):
		new_data = []
		for item in data:
			if what == 'a':
				if os.path.exists(item[0]):
					new_data.append(item)
			elif what == 'f':
				if os.path.isfile(item[0]):
					new_data.append(item)
			else:
				if os.path.isdir(item[0]):
					new_data.append(item)
		return new_data
			
	def print (self, data):
		for path, rank, atime, score in data:
			print('%s|%d|%d -> %s'%(path, rank, atime, score))
		return 0

	def pretty (self, data):
		output = [ (n[3], n[0]) for n in data ]
		output.sort()
		output = [ (str(n[0]), n[1]) for n in output ]
		maxlen = max([12] + [ len(n[0]) for n in output ]) + 2
		strfmt = '%%-%ds %%s'%maxlen
		for m, n in output:
			print(strfmt%(m, n))
		return 0

	def string_match_fasd (self, string, args, nocase):
		pos = 0
		if nocase:
			string = string.lower()
		for arg in args:
			if arg.endswith('$'):
				arg = arg[:-1]
			pos = string.find(arg, pos)
			if pos < 0:
				return False
			pos += len(arg)
		if args:
			lastarg = args[-1]
			if self.unix:
				if lastarg.endswith('/'):
					return True
			else:
				if lastarg.endswith('\\'):
					return True
			if lastarg[-1:] == '$':
				return string.endswith(lastarg[:-1])
			lastpath = os.path.split(string)[-1]
			lastpath = lastpath and lastpath or string
			if not lastarg in lastpath:
				return False
		return True

	def string_match_z (self, string, patterns):
		for pat in patterns:
			m = pat.search(string)
			if not m:
				return False
			string = string[m.end():]
		return True

	def match (self, data, args, nocase, mode):
		if mode in (0, 'f', 'fasd'):
			if nocase:
				args = [ n.lower() for n in args ]
			f = lambda n: self.string_match_fasd(n[0], args, nocase)
			m = filter(f, data)
		elif mode in (1, 'z', 2, 'zc'):
			flags = nocase and re.I or 0
			patterns = [ re.compile(n, flags) for n in args ]
			f = lambda n: self.string_match_z(n[0], patterns)
			m = filter(f, data)
		else:
			return []
		return m

	def common (self, data, args):
		perf = os.path.commonprefix([ n[0] for n in data ])
		if not perf or perf == '/':
			return None
		lowperf = perf.lower()
		find = False
		for item in data:
			path = item[0]
			test = perf
			if self.nocase:
				path = path.lower()
				test = lowerperf
			if test == path:
				find = True
				break
		if not find:
			return None
		for arg in args:
			flag = self.nocase and re.I or 0
			m = re.search(arg, perf, flag)
			if not m:
				return None
		return perf

	def search (self, data, args, mode):
		if self.nocase:
			m = self.match(data, args, True, mode)
		else:
			m = self.match(data, args, False, mode)
			if not m:
				m = self.match(data, args, True, mode)
		return m

	def score (self, data, mode):
		current = int(time.time())
		if mode in (0, 'frecent', 'f'):
			for item in data:
				atime = item[2]
				delta = current - atime
				if delta < 3600: 
					score = item[1] * 4
				elif delta < 86400: 
					score = item[1] * 2
				elif delta < 604800: 
					score = item[1] / 2
				else:
					score = item[1] / 4
				item[3] = score
		elif mode in (1, 'rank', 'r'):
			for item in data:
				item[3] = item[1]
		elif mode in (2, 'time', 't'):
			for item in data:
				atime = item[2]
				item[3] = atime - current
		return 0

	def insert (self, data, path):
		key = self.nocase and path.lower() or path
		current = int(time.time())
		count = sum([ n[1] for n in data ])
		if count >= self.maxage:
			newdata = []
			for item in data:
				key = int(item[1] * 0.9)
				if key > 0:
					newdata.append(item)
			data = newdata
		find = False
		for item in data:
			name = item[0]
			if self.nocase:
				name = name.lower()
			if name == key:
				item[1] += 1
				item[2] = current
				find = True
				break
		if not find:
			item = [path, 1, current, 0]
			data.append(item)
		return data

	def normalize (self, path):
		path = path.strip('\r\n\t ')
		if not path:
			return None
		path = os.path.normpath(path)
		key = self.nocase and path.lower() or path
		if (not path) or (not os.path.exists(path)):
			return None
		if self.unix:
			home = self.nocase and self.home.lower() or self.home
			if key == home:
				return None
		for exclude in self.exclude:
			if self.nocase:
				exclude = exclude.lower()
			if key.startswith(exclude):
				return None
		return path

	def add (self, data, path):
		path = self.normalize(path)
		if not path:
			return data
		return self.insert(data, path)

	def converge (self, data_list):
		path_dict = {}
		for data in data_list:
			for item in data:
				key = item[0]
				if self.nocase:
					key = key.lower()
				if not key in path_dict:
					path_dict[key] = item
				else:
					oi = path_dict[key]
					rank = oi[1]
					atime = oi[2]
					oi[1] = rank + item[1]
					oi[2] = max(atime, item[2])
		data = []
		for key in path_dict:
			data.append(path_dict[key])
		return data


#----------------------------------------------------------------------
# FasdNg
#----------------------------------------------------------------------
class FasdNg (object):

	def __init__ (self):
		datafile = os.environ.get('_F_DATA', os.path.expanduser('~/.fasdng'))
		owner = os.environ.get('_F_OWNER', None)
		self.fd = FasdData(datafile, owner)
		self.unix = self.fd.unix
		self._init_environ()
		self.common = None
		self.data = None
		self.method = 'frecent'

	def _init_environ (self):
		exclude = os.environ.get('_F_BLACKLIST', '')
		for black in exclude.split(self.unix and ':' or ';'):
			black = black.strip('\r\n\t ')
			if not black:
				continue
			self.fd.exclude.append(black)
		if sys.platform in ('cygwin', 'msys') or sys.platform[:3] == 'win':
			self.fd.nocase = True
		else:
			self.fd.nocase = False
		self.matcher = 0
		if os.environ.get('_F_MATCHER', 0) in ('z', '1'):
			self.matcher = 1
		self.track_pwd = True
		if os.environ.get('_F_TRACK_PWD', '') in ('0', 'no', 'false'):
			self.track_pwd = False
		self.track_file = True
		if os.environ.get('_F_TRACK_FILE', '') in ('0', 'no', 'false'):
			self.track_file = False
		self.readonly = False
		if os.environ.get('_F_READ_ONLY') in ('1', 'yes', 'true'):
			self.readonly = True
		self.backends = {}
		sep = self.unix and ':' or ';'
		for n in os.environ.get('_F_BACKENDS', '').split(sep):
			self.backends[n.strip('\r\n\t ')] = 1
		self.sources = {}
		self.final_data = []
		return 0

	def load (self):
		if self.data is None:
			data = self.fd.load()
			self.data = self.fd.filter(data)
		return self.data

	def save (self):
		if self.readonly:
			return False
		self.fd.save(self.data)
		return True

	def add (self, path):
		if self.readonly:
			return False
		path = os.path.normpath(path)
		if not os.path.exists(path):
			return False
		if os.path.isdir(path):
			if not self.track_pwd:
				return False
		else:
			if not self.track_file:
				return False
		self.load()
		self.data = self.fd.add(self.data, path)
		self.save()
		return True

	# st: f, d, a
	def search (self, args, st):
		data = self.load()
		for backend in self.backends:
			source = []
			try:
				if backend == 'viminfo':
					source = self.backend_viminfo()
				elif backend.startswith('+'):
					source = self.backend_command(backend[1:])
			except:
				continue
			source = self.fd.filter(source)
			data = self.fd.converge([data, source])
		self.common = None
		m = self.fd.search(data, args, self.matcher)
		if st == 'f':
			m = filter(lambda n: os.path.isfile(n[0]), m)
		elif st == 'd':
			m = filter(lambda n: os.path.isdir(n[0]), m)
			self.common = self.fd.common(m, args)
		if self.method in (0, '0', 'f', 'frecent'):
			self.fd.score(m, 'r')
		elif self.method in (1, '1', 'r', 'rank', 'ranked'):
			self.fd.score(m, 'r')
		else:
			self.fd.score(m, 't')
		return m

	def backend_command (self, command):
		import subprocess
		p = subprocess.Popen(command, shell = True,
			stdin = None, stdout = subprocess.PIPE, stderr = None)
		output = p.stdout.read()
		p.wait()
		if isinstance(output, bytes):
			if sys.stdout and sys.stdout.encoding:
				output = output.encode(sys.stdout.encoding, 'ignore')
			elif sys.stdin and sys.stdin.encoding:
				output = output.encode(sys.stdin.encoding, 'ignore')
			else:
				output = output.encode('utf-8', 'ignore')
		data = []
		for line in output.split('\n'):
			part = line.rstrip('\r\n\t ').split('|')
			if len(part) != 3:
				continue
			path = part[0]
			rank = part[1].isdigit() and int(part[1]) or 0
			atime = part[2].rstrip('\n')
			atime = atime.isdigit() and int(atime) or 0
			score = 0
			data.append([path, rank, atime, score])
		return data
		
	def backend_viminfo (self):
		data = []
		viminfo = os.environ.get('_F_VIMINFO', '')
		if not viminfo:
			if self.unix:
				viminfo = os.path.expanduser('~/.viminfo')
			else:
				viminfo = os.path.expanduser('~/_viminfo')
		if not os.path.exists(viminfo):
			return data
		current = int(time.time())
		with open(viminfo, 'rb') as fp:
			content = fp.read()
			pos = 0
			encoding = 'utf-8'
			while True:
				next_pos = content.find(b'\n', pos)
				if next_pos < 0:
					break
				line = content[pos:next_pos]
				pos = next_pos + 1
				line = line.strip(b'\r\n\t ')
				if line.startswith(b'*encoding='):
					enc = line[len(b'*encoding='):].strip(b'\r\n\t ')
					encoding = enc.decode('utf-8', 'ignore')
			state = 0
			filename = ''
			text = content.decode(encoding, 'ignore')
			for line in text.split('\n'):
				line = line.rstrip('\r\n\t')
				if state == 0:
					if line.startswith('>'):
						filename = line[1:].lstrip(' \t')
						state = 1
				else:
					state = 0
					if not line[:1].isspace():
						data.append([filename, 2, current, 0])
						continue
					line = line.lstrip(' \t')
					if line[:1] != '*':
						data.append([filename, 2, current, 0])
						continue
					for part in line.split():
						if part.isdigit():
							ts = int(part)
							data.append([filename, 2, ts, 0])
							break
		new_data = []
		ignore_prefix = ['git:', 'ssh:', 'gista:']
		for item in data:
			name = item[0]
			skip = False
			for ignore in ignore_prefix:
				if name.startswith(ignore):
					skip = True
					break
			if not skip:
				if '~' in name:
					item[0] = os.path.expanduser(name)
				new_data.append(item)
		# return data
		return self.fd.filter(new_data)


#----------------------------------------------------------------------
# testing
#----------------------------------------------------------------------
if __name__ == '__main__':

	def test1():
		fd = FasdData('d:/navdb.txt')
		data = fd.load()
		# data.append(['fuck', 0, 0])
		# print(len(data))
		fd.print(data)
		# fd.pretty(data)
		print()
		data = fd.filter(data)
		print(len(data))
		print()
		# fd.save(data)
		args = ['github', 'im']
		# args = ['D:\\']
		# args = []
		print(fd.string_match_fasd('d:\\acm\\github\\vim', args, 0))
		m = []
		# args = ['qemu']
		m = fd.search(data, args, 1)
		fd.score(m, 'f')
		# m = fd.match(data, ['vim$'])
		fd.pretty(m)
		print(fd.common(m, args))
		return 0

	def test2():
		fn = FasdNg()
		# data = fn.backend_viminfo()
		fn.backends = ['+type d:\\navdb.txt']
		# fn.fd.score(data, 'f')
		# fn.fd.pretty(fn.load())
		data = fn.search([''], 'd')
		# print(data)
		fn.fd.pretty(data)
		return 0

	test2()



