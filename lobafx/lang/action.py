from lobafx.lang.node import Node
from lobafx.lang.selector import Selector

class Action(Node):
	def __init__(self, name = 'Act'):
		super(Action, self).__init__(name)

		self.selector = None
	
	def __mod__(self, rhs):
		Action._validateRhs(rhs)
		self.selector = rhs
		return self
	
	def _getSelection(self, event):
		if self.selector:
			return self.selector.select(event)
		else:
			return []

	def perform(self, event):
		pass

	def debugPrint(self, indent = 0):
		Action._printIndent(self.name, indent)
		self._debugPrintSelector(indent)
	
	def _debugPrintSelector(self, indent):
		if self.selector:
			self.selector.debugPrint(indent + 1)
	
	@classmethod
	def _validateRhs(cls, rhs):
		if not isinstance(rhs, Selector):
			raise Exception('Not \'Selector\' after \'%\'')
