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

	vg = VirtualGateway('10.0.0.254', '02:00:DE:AD:BE:EF', '00-00-00-00-00-02', 1)
	m1 = Host('10.0.0.101', 'D6:F6:C3:05:CA:B9', 2)
	m2 = Host('10.0.0.102', '76:4F:72:F3:10:59', 3)
	m3 = Host('10.0.0.103', '36:8A:3B:4D:EF:2E', 4)

	s1 >> [ L2Learn() ]
	
#	(s2 & InPort(1) & HttpTo(vg)) >> [ ForwardProxy() % SelectLowestLoad([ m1, m2, m3 ]) ]
	(s2 & InPort(1) & HttpTo(vg)) >> [ ForwardProxy() % RandomSelector([ m1, m2, m3 ]) ]
	(s2 & ~InPort(1) & HttpFromAny()) >> [ ReverseProxy(vg) ]

if __name__ == '__main__':
	setupRules()
	startup()
