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

# Collect host load

# Test rules.
s1 = FromSwitch('00-00-00-00-00-01')
s1 >> [ L2Learn() ]

vg = VirtualGateway('10.0.0.254', '02:00:DE:AD:BE:EF', '00-00-00-00-00-02', 1)
m1 = Host('10.0.0.101', 'D6:F6:C3:05:CA:B9', 2)
m2 = Host('10.0.0.102', '76:4F:72:F3:10:59', 3)
m3 = Host('10.0.0.103', '36:8A:3B:4D:EF:2E', 4)

s2 = FromSwitch('00-00-00-00-00-02')
(s2 & InPort(1) & HttpTo(vg)) >> \
	[ \
		ForwardProxy() % SelectLowestLoad([ m1, m2, m3 ]), \
	  	PrintLoad() % SelectAll([ m1, m2, m3]) \
	]
(s2 & ~InPort(1) & HttpFromAny()) >> [ ReverseProxy(vg) ]

######## Startup core ########
def startup():
	# Rule for processing unmatched packets.
	Anything() >> [ PrintEvent() ]

	global nal
	nal.startup()

