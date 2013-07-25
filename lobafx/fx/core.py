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

######## Setup link manager ########
class LinkManager(object):
	def __init__(self):
		self.links = []
		self.conns = {}
		self.wentDown = False
	
	def register(self, link):
		self.links.append(link)
	
	def count(self):
		return len(self.links)
	
	def startup(self):
		t = threading.Thread(target = self.worker, args = [])
		t.start()
		
	def shutdown(self):
		self.wentDown = True
	
	def worker(self):
		while not self.wentDown:
			for link in self.links:
				dpidStr = link.switch1.dpidStr
				if not dpidStr in self.conns:
					continue
				conn = self.conns[dpidStr]
				conn.send(of.ofp_stats_request( \
					type = of.OFPST_PORT, \
					body = of.ofp_port_stats_request(port_no = link.port1)))
			time.sleep(1)

linkMgr = LinkManager()

######## Setup host manager ########
class HostManager(object):
	def __init__(self):
		self.hosts = []
		self.wentDown = False
	
	def register(self, host):
		self.hosts.append(host)
	
	def count(self):
		return len(self.hosts)
	
	def startup(self):
		t = threading.Thread(target = self.worker, args = [])
		t.start()
		
	def shutdown(self):
		self.wentDown = True
	
	def worker(self):
		while not self.wentDown:
			for host in self.hosts:
				# Update host loads.
				host.load += random.randint(1, 5)
			time.sleep(1)

hostMgr = HostManager()

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
				if not rule.fallThrough:
					return

listener = Listener()

######## Setup NOS abstraction layer ########
from lobafx.nal.poxnal import POXNal
# from lobafx.nal.testnal import TestNal

# nal = TestNal()
nal = POXNal()
nal.register(listener)

######## Actions that needed by the core ########
from lobafx.lang.action import Action

class UpdateLinkStats(Action):
	def perform(self, event):
		stats = event.stats[0]
		for link in linkMgr.links:
			if link.switch1.test(event) and link.port1 == stats.port_no:
				link.stats = stats
				
class RememberConnection(Action):
	def __init__(self, map):
		self.map = map
	
	def perform(self, event):
		dpidStr = dpidToStr(event.dpid)
		log.info("Remember connection with '%s'" % dpidStr)
		self.map[dpidStr] = event.connection
		
class ForgetConnection(Action):
	def __init__(self, map):
		self.map = map
	
	def perform(self, event):
		dpidStr = dpidToStr(event.dpid)
		log.info("Forget connection with '%s'" % dpidStr)
		self.map[dpidStr] = None
		
class Finalize(Action):
	def perform(self, event):
		from lobafx.fx.core import linkMgr
		linkMgr.shutdown()
		from lobafx.fx.core import hostMgr
		hostMgr.shutdown()
		print 'Stats:'
		for link in linkMgr.links:
			print 'Link: %s, Load: %d' % (link, link.load)
		for host in hostMgr.hosts:
			print 'Host: %s, Load: %d' % (host.ipStr, host.load)

######## Setup core rules ########
from lobafx.fx.poxlib import *

# Print all ErrorIn packets.
IsErrorIn() >> [ PrintError() ]

(IsConnectionUp() >> [ RememberConnection(linkMgr.conns) ]) \
	.fallThrough = True
(IsConnectionDown() >> [ ForgetConnection(linkMgr.conns) ]) \
	.fallThrough = True

# Use the received port stats to update link stats.
IsPortStatsReceived() >> [ UpdateLinkStats() ]

# Do some finalizing work when POX goes down.
IsGoingDown() >> [ Finalize() ]

######## Startup core ########
def startup():
	# Rule for processing all unmatched packets.
	Anything() >> [ PrintEvent() ]
	
	linkMgr.startup()
	hostMgr.startup()
	nal.startup()
	
