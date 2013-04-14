#!/usr/bin/python

from lobafx.lang.predicate import AtomicPredicate
from lobafx.lang.selector import Selector
from lobafx.lang.action import Action
from lobafx.fx import core

def testLang():
	p1 = AtomicPredicate('p1')
	p2 = AtomicPredicate('p2')
	p3 = AtomicPredicate('p3')
	s1 = Selector('s1')
	s2 = Selector('s2')
	a1 = Action('a1')
	a2 = Action('a2')
	a3 = Action('a3')

	r0 = (p1 & p2 | ~p3) >> [a1 % s1, a2 % s2, a3]
	r0.debugPrint()

	p = p1 | p3
	r1 = p >> [a1, a2 % s1]
	r1.debugPrint()

	print core.ruleMgr.count()

def startup():
	pass

if __name__ == '__main__':
	testLang()
	startup()