from lobafx.lang.node import Node

class Selector(Node):
	def __init__(self, name = 'Sel'):
		super(Selector, self).__init__(name)

	def select(self, event):
		return []

	def debugPrint(self, indent = 0):
		Selector._printIndent(self.name, indent)
