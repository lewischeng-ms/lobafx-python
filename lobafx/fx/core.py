from lobafx.nal.poxnal import POXNal
from lobafx.nal.testnal import TestNal

class RuleManager(object):
	def __init__(self):
		self.rules = {}

	def register(self, rule):
		if not rule.predicate:
			raise Exception('No predicate in the rule \'%s\'' % rule.name)

		if self.rules.get(rule.name):
			raise Exception('Rule \'%s\' redefined' % rule.name)

		self.rules[rule.name] = rule

	def query(self, name):
		return self.rules.get(name)

	def count(self):
		return len(self.rules)

ruleMgr = RuleManager()


class Listener(object):
	def __init__(self):
		pass

listener = Listener()


nal = TestNal()
nal.register(listener)