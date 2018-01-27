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

	def match (self, data, args, nocase = False):
		def match_string (string, patterns):
			for pat in patterns:
				m = pat.search(string)
				if not m:
					return False
				string = string[m.end():]
			return True
		flags = nocase and re.I or 0
		patterns = [ re.compile(n, flags) for n in args ]
		m = filter(lambda n: match_string(n[0], patterns), data)
		return m

	def search (self, data, args):
		if self.nocase:
			m = self.match(data, args, True)
		else:
			m = self.match(data, args, False)
			if not m:
				m = self.match(data, args, True)
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
				atime = itime[2]
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
		self.fd = FasdData()


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
		m = fd.search(data, ['Vim'])
		fd.score(m, 'f')
		# m = fd.match(data, ['vim$'])
		fd.pretty(m)
		return 0

	test1()



