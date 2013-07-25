#!/usr/bin/env python

# Add pox directory to path
import sys
sys.path.append('/Users/lewischeng/Develop/pox')

from lobafx import fx

def startup():
	fx.core.startup()
	
from lobafx.fx.poxlib import *

def setupRules():
	pass
	
if __name__ == '__main__':
	setupRules()
	startup()
