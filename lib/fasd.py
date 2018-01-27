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

	def __init__ (self, filename, owner = None, mode = -1):
		if '~' in filename:
			filename = os.path.expanduser(filename)
		self.name = filename
		self.user = owner
		self.mode = mode
		self.unix = (sys.platform[:3] != 'win')

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
					data.append([path, rank, atime])
		except IOError:
			return []
		return data

	def save (self, data):
		tmpname = self.name + '.' + self._random()
		retval = 0
		try:
			with codecs.open(tmpname, 'w', encoding = 'utf-8') as fp:
				for path, rank, atime in data:
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
			os.remove(tmpname)
		return retval

	def filter_out (self, data, what = 'a'):
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
			
	def _random (self):
		if sys.platform[:3] == 'win':
			ts = int(time.time() * 1000)
			ts = hex(ts)[2:]
		else:
			ts = int(time.time() * 1000000)
			ts = hex(ts)[2:]
		ts += hex(random.randrange(65536))[2:]
		return ts.lower()
	
	def print (self, data):
		for path, rank, atime in data:
			print('%s|%d|%d'%(path, rank, atime))
		return 0

	def pretty (self, data):
		output = [ (n[1], n[0]) for n in data ]
		output.sort()
		output = [ (str(n[0]), n[1]) for n in output ]
		maxlen = max([14] + [ len(n[0]) for n in output ])
		strfmt = '%%-%ds %%s'%maxlen
		for m, n in output:
			print(strfmt%(m, n))
		return 0

	def match (self, data, args, incase = False):
		def compare_string (string, patterns):
			for pat in patterns:
				m = pat.search(string)
				if not m:
					return False
				string = string[m.end():]
			return True
		flags = incase and re.I or 0
		patterns = [ re.compile(n, flags) for n in args ]
		m = filter(lambda n: compare_string(n[0], patterns), data)
		return m



#----------------------------------------------------------------------
# 
#----------------------------------------------------------------------
if __name__ == '__main__':

	def test1():
		fd = FasdData('d:/navdb.txt')
		data = fd.load()
		# data.append(['fuck', 0, 0])
		# print(len(data))
		fd.pretty(data)
		print()
		data = fd.filter_out(data)
		print(len(data))
		print()
		# fd.save(data)
		m = fd.match(data, ['vim'])
		# m = fd.match(data, ['vim$'])
		fd.pretty(m)
		return 0

	test1()



