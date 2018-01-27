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
					date = part[2].isdigit() and int(part[2]) or 0
					data.append([path, rank, date])
		except IOError:
			return []
		return data

	def save (self, data):
		tmpname = self.name + '.' + self._random()
		retval = 0
		try:
			with codecs.open(tmpname, 'w', encoding = 'utf-8') as fp:
				for path, rank, date in data:
					fp.write('%s|%d|%d\n'%(path, rank, date))
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

	def filter_exists (self, data):
		new_data = []
		for path, rank, date in data:
			pass
			
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
		for path, rank, date in data:
			print('%s|%d|%d'%(path, rank, date))
		return 0



#----------------------------------------------------------------------
# 
#----------------------------------------------------------------------
if __name__ == '__main__':

	def test1():
		fd = FasdData('d:/navdb.txt')
		data = fd.load()
		print(len(data))
		fd.print(data)
		print(fd.save(data))

		return 0

	test1()



