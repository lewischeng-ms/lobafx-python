######## Setup rule mananger ########
class RuleManager(object):
	def __init__(self):
		self.rules = []

	def register(self, rule):
		if not rule.predicate:
			raise Exception('No predicate in the rule \'%s\'' % rule.name)

		for r in self.rules:
			if r.name == rule.name:
				raise Exception('Rule \'%s\' redefined' % rule.name)

		self.rules.append(rule)

	def count(self):
		return len(self.rules)

ruleMgr = RuleManager()


######## Setup core listener ########
class Listener(object):
	def __init__(self):
		pass

	# called when event raised.
	# access rule manager and call corresponding rules.
	def onEvent(self, event):
		for rule in ruleMgr.rules:
			if rule.testPredicate(event):
				rule.performActions(event)
				return # Match exactly one rule.

listener = Listener()


######## Setup NOS abstraction layer ########
from lobafx.nal.poxnal import POXNal
# from lobafx.nal.testnal import TestNal

global nal
# nal = TestNal()
nal = POXNal()
nal.register(listener)


######## Setup core rules ########
from lobafx.fx.poxlib import *

# Print all ErrorIn packets.
IsErrorIn() >> [PrintError()]

# Collect link load.

# Collect host load.

# Test rules.
FromSwitch('00-00-00-00-00-01') >> [ L2Learn() ]

######## Startup core ########
def startup():
	# Rule for processing unmatched packets.
	Anything() >> [PrintEvent()]

	global nal
	nal.startup()

