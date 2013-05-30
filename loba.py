#!/usr/bin/python

# Add pox directory to path
import sys
sys.path.append('/home/mininet/pox')

from lobafx.fx import core

def startup():
	core.startup()

if __name__ == '__main__':
	startup()
