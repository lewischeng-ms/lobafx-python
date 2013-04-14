class Node(object):
	def __init__(self, name = 'Node'):
		self.name = name

	def debugPrint(self, indent = 0):
		Node._printIndent(self.name, indent)

	@classmethod
	def _printIndent(cls, str, indent):
		paddedLen = indent * 2 + len(str)
		print str.rjust(paddedLen, '-')
