#!/usr/bin/python

class GrammerNode(object):
	def __init__(self, name):
		self.setName(name)
	
	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	def printName(self, indent):
		paddedLen = indent * 2 + len(self.name)
		print self.name.rjust(paddedLen, '-')
	
	def printNode(self, indent):
		self.printName(indent)

class Rule(GrammerNode):
	def __init__(self, name, p, l):
		super(Rule, self).__init__(name)

		self.predicate = p
		self.actionList = l

	def printNode(self, indent):
		self.printName(indent)
		self.printPredicate(indent + 1)
		self.printActionList(indent + 1)

	def printPredicate(self, indent):
		self.predicate.printNode(indent)

	def printActionList(self, indent):
		for action in self.actionList:
			action.printNode(indent)

class Predicate(GrammerNode):
	def __init__(self, name, lhs, rhs):	
		super(Predicate, self).__init__(name)

		self.leftOperand = lhs
		self.rightOperand = rhs

	def __and__(self, rhs):
		self.validateArg(rhs, Predicate, '&')
		return AndExpression('AND', self, rhs)

	def __or__(self, rhs):
		self.validateArg(rhs, Predicate, '|')
		return OrExpression('OR', self, rhs)

	def __invert__(self):
		return NotExpression('NOT', self)

	def __rshift__(self, rhs):
		self.validateArg(rhs, list, '>>')
		self.validateList(rhs)
		return Rule('RULE', self, rhs)

	def printNode(self, indent):
		self.printName(indent)
		self.printLeftOperand(indent + 1)
		self.printRightOperand(indent + 1)

	def printLeftOperand(self, indent):
		if self.leftOperand:
			self.leftOperand.printNode(indent)
	
	def printRightOperand(self, indent):
		if self.rightOperand:
			self.rightOperand.printNode(indent)

	def validateArg(self, arg, t, op):
		if not isinstance(arg, t):
			raise Exception('Not \'%s\' after \'%s\'' % (t.__name__, op))
	
	def validateList(self, l):
		for a in l:
			if not isinstance(a, Action):
				raise Exception('Not \'Action\' in \'list\'')

class AndExpression(Predicate):
	def __init__(self, name, lhs, rhs):
		super(AndExpression, self).__init__(name, lhs, rhs)

class OrExpression(Predicate):
	def __init__(self, name, lhs, rhs):
		super(OrExpression, self).__init__(name, lhs, rhs)

class NotExpression(Predicate):
	def __init__(self, name, rhs):
		super(NotExpression, self).__init__(name, None, rhs)

class AtomicPredicate(Predicate):
	def __init__(self, name):
		super(AtomicPredicate, self).__init__(name, None, None)

class Action(GrammerNode):
	def __init__(self, name):
		super(Action, self).__init__(name)

		self.selector = None
	
	def __mod__(self, rhs):
		self.validateArg(rhs)
		self.selector = rhs
		return self

	def printNode(self, indent):
		self.printName(indent)
		self.printSelector(indent + 1)
	
	def printSelector(self, indent):
		if self.selector:
			self.selector.printNode(indent)
	
	def validateArg(self, arg):
		if not isinstance(arg, Selector):
			raise Exception('Not \'Selector\' after \'%\'')

class Selector(GrammerNode):
	def __init__(self, name):
		super(Selector, self).__init__(name)

	def printNode(self, indent):
		self.printName(indent)

def printRule(r):
	r.printNode(0)

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
	r0.setName('r0')
	printRule(r0)

	p = p1 | p3
	r1 = p >> [a1, a2 % s1]
	r1.setName('r1')
	printRule(r1)

if __name__ == '__main__':
	testLang()
