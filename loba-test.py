#!/usr/bin/env python

# Add pox directory to path
import sys 
sys.path.append('/Users/lewischeng/Develop/pox')

from lobafx.lang.predicate import AtomicPredicate
from lobafx.lang.selector import Selector
from lobafx.lang.action import Action
from lobafx.fx.testlib import *
from lobafx.fx import core

def testLang():
	p1 = AtomicPredicate('p1')
	p2 = AtomicPredicate('p2')
	p3 = AtomicPredicate('p3')
	a1 = Action('a1')
	a2 = Action('a2')
	a3 = Action('a3')
	s1 = Selector('s1')
	s2 = Selector('s2')
	r0 = (p1 & p2 | ~p3) >> [a1 % s1, a2 % s2, a3]
	
	r0.debugPrint()

def decl4TestNal():
	(IsOdd() & ThreeTimes()) >> [PrintInclusion() % ConstantsSelector()]

def startup():
	print 'Rule Count: %d' % core.ruleMgr.count()
	core.nal.startup()

if __name__ == '__main__':
	testLang()
	decl4TestNal()
	startup()
