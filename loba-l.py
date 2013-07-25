#!/usr/bin/env python

# Add pox directory to path
import sys
sys.path.append('/Users/lewischeng/Develop/pox')

from lobafx import fx

def startup():
	fx.core.startup()
	
from lobafx.fx.poxlib import *

def setupRules():
	s1 = FromSwitch('00-00-00-00-00-01')
	s2 = FromSwitch('00-00-00-00-00-02')
	s3 = FromSwitch('00-00-00-00-00-03')
	s4 = FromSwitch('00-00-00-00-00-04')
	s5 = FromSwitch('00-00-00-00-00-05')
	s6 = FromSwitch('00-00-00-00-00-06')

	s1 >> [ L2Learn() ]
	s3 >> [ L2Learn() ]
	s4 >> [ L2Learn() ]
	s5 >> [ L2Learn() ]

	l1 = Link(s2, 1, s6, 1)
	l2 = Link(s2, 2, s6, 2)
	l3 = Link(s2, 3, s6, 3)

#	(s2 & InPort(4)) >> [ ApplyForwardLink() % SelectLowestLoad([ l1, l2, l3 ]) ]
	(s2 & InPort(4)) >> [ ApplyForwardLink() % RandomSelector([ l1, l2, l3 ]) ]
	(s2 & ~InPort(4)) >> [ SimpleForward(4) ]
#	(s6 & InPort(4)) >> [ ApplyReverseLink() % SelectLowestLoad([ l1, l2, l3 ]) ]
	(s6 & InPort(4)) >> [ ApplyReverseLink() % RandomSelector([ l1, l2, l3 ]) ]
	(s6 & ~InPort(4)) >> [ SimpleForward(4) ]

if __name__ == '__main__':
	setupRules()
	startup()
