from lobafx.lang.node import Node
from lobafx.lang.action import Action
from lobafx.lang.rule import Rule

class Predicate(Node):
	def __init__(self, name = 'Pred', lhs = None, rhs = None):	
		super(Predicate, self).__init__(name)

		self.leftOperand = lhs
		self.rightOperand = rhs

	def __and__(self, rhs):
		Predicate._validateRhs(rhs, Predicate, '&')
		return AndExpression(lhs = self, rhs = rhs)

	def __or__(self, rhs):
		Predicate._validateRhs(rhs, Predicate, '|')
		return OrExpression(lhs = self, rhs = rhs)

	def __invert__(self):
		return NotExpression(rhs = self)

	def __rshift__(self, rhs):
		Predicate._validateRhs(rhs, list, '>>')
		Predicate._validateActions(rhs)
		return Rule(pred = self, acts = rhs)

	def test(self, obj):
		return False

	def debugPrint(self, indent = 0):
		Predicate._printIndent(self.name, indent)
		self._debugPrintLeftOperand(indent)
		self._debugPrintRightOperand(indent)

	def _debugPrintLeftOperand(self, indent):
		if self.leftOperand:
			self.leftOperand.debugPrint(indent + 1)

	def _debugPrintRightOperand(self, indent):
		if self.rightOperand:
			self.rightOperand.debugPrint(indent + 1)

	@classmethod
	def _validateRhs(cls, rhs, tp, op):
		if not isinstance(rhs, tp):
			raise Exception('Not \'%s\' after \'%s\'' % (tp.__name__, op))
	
	@classmethod
	def _validateActions(cls, acts):
		for a in acts:
			if not isinstance(a, Action):
				raise Exception('Not \'Action\' in \'list\'')

class AtomicPredicate(Predicate):
	def __init__(self, name = 'APred'):
		super(AtomicPredicate, self).__init__(name, None, None)

class AndExpression(Predicate):
	def __init__(self, name = 'And', lhs = None, rhs = None):
		super(AndExpression, self).__init__(name, lhs, rhs)

	def test(self, obj):
		# If either lhs or rhs is None, operator & returns False.
		if not self.leftOperand or not self.rightOperand:
			return False
		else:
			return self.leftOperand.test(obj) and self.rightOperand.test(obj)

class OrExpression(Predicate):
	def __init__(self, name = 'Or', lhs = None, rhs = None):
		super(OrExpression, self).__init__(name, lhs, rhs)

	def test(self, obj):
		# If either lhs or rhs is None, operator | returns False.
		if not self.leftOperand or not self.rightOperand:
			return False
		else:
			return self.leftOperand.test(obj) or self.rightOperand.test(obj)

class NotExpression(Predicate):
	def __init__(self, name = 'Not', rhs = None):
		super(NotExpression, self).__init__(name, None, rhs)

	def test(self, obj):
		# If rhs is None, operator ~ returns False.
		if not self.rightOperand:
			return False
		else:
			return not self.rightOperand.test(obj)
