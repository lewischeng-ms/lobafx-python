class Nal(object):
	def __init__(self):
		self.listener = None

	def register(self, listener):
		self.listener = listener