from lobafx.lang.predicate import AtomicPredicate
from lobafx.lang.selector import Selector
from lobafx.lang.action import Action

class IsOdd(AtomicPredicate):
	def test(self, event):
		return (event & 1) == 1

class ThreeTimes(AtomicPredicate):
	def test(self, event):
		return (event % 3) == 0

class PrintInclusion(Action):
	def perform(self, event):
		sel = self._getSelection(event)
		if event in sel:
			print "%d is in %s" % (event, sel)
		else:
			print "%d is not in %s" % (event, sel)

class ConstantsSelector(Selector):
	def select(self, event):
		return [2, 3, 9]
