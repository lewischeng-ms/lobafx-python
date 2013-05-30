from lobafx.nal import Nal

class TestNal(Nal):
	def startup(self):
		for i in range(20):
			self.listener.onEvent(i + 1)
