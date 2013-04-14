from lobafx.lang.node import Node
from lobafx.fx import core

class Rule(Node):
	def __init__(self, name = None, pred = None, acts = None):
		super(Rule, self).__init__(Rule._getName(name))

		self.predicate = pred
		self.actions = acts

		core.ruleMgr.register(self)

	def debugPrint(self, indent = 0):
		Rule._printIndent(self.name, indent)
		self._debugPrintPredicate(indent)
		self._debugPrintActions(indent)

	def _debugPrintPredicate(self, indent):
		self.predicate.debugPrint(indent + 1)

	def _debugPrintActions(self, indent):
		for action in self.actions:
			action.debugPrint(indent + 1)

	rid = 1

	@classmethod
	def _getName(cls, name):
		if not name:
			name = 'Rule%d' % Rule.rid
			Rule.rid += 1

		return name