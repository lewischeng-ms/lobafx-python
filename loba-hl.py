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
	s7 = FromSwitch('00-00-00-00-00-07')

	vg = VirtualGateway('10.0.0.254', '02:00:DE:AD:BE:EF', '00-00-00-00-00-07', 4)
	m1 = Host('10.0.0.101', 'D6:F6:C3:05:CA:B9', 1)
	m2 = Host('10.0.0.102', '76:4F:72:F3:10:59', 2)
	m3 = Host('10.0.0.103', '36:8A:3B:4D:EF:2E', 3)

	s1 >> [ L2Learn() ]
	s3 >> [ L2Learn() ]
	s4 >> [ L2Learn() ]
	s5 >> [ L2Learn() ]

#	(s7 & InPort(4) & HttpTo(vg)) >> [ ForwardProxy() % SelectLowestLoad([ m1, m2, m3 ]) ]
	(s7 & InPort(4) & HttpTo(vg)) >> [ ForwardProxy() % RandomSelector([ m1, m2, m3 ]) ]
	(s7 & ~InPort(4) & HttpFromAny()) >> [ ReverseProxy(vg) ]

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
