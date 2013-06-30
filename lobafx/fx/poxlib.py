from lobafx.lang.predicate import AtomicPredicate
from lobafx.lang.selector import Selector
from lobafx.lang.action import Action
from pox.lib.revent import *
from pox.openflow import ConnectionUp, ConnectionDown, PacketIn, ErrorIn
from pox.lib.util import dpidToStr
from pox.core import core
import time

log = core.getLogger('fx.poxlib')

class Anything(AtomicPredicate):
	def test(self, event):
		return True

class IsErrorIn(AtomicPredicate):
	def test(self, event):
		return isinstance(event, ErrorIn)

class IsPacketIn(AtomicPredicate):
	def test(self, event):
		return isinstance(event, PacketIn)

class FromSwitch(AtomicPredicate):
	def __init__(self, dpidStr):
		super(FromSwitch, self).__init__()
		self.dpidStr = dpidStr

	def test(self, event):
		return dpidToStr(event.dpid) == self.dpidStr

class PrintError(Action):
	def perform(self, event):
		print 'Error: \'%s\' from switch %s' % (dpidToStr(event.dpid), event.asString())

######## Action: L2 Learning ########
import pox.openflow.libopenflow_01 as of

'''
Perform L2 Learning.

Adapted from pox.forwarding.l2_learning.
'''
class L2Learn(Action):
	def __init__(self):
		super(L2Learn, self).__init__()

		self.mac2Port = {}
		self.connected = False
		self.dpid = None

	def perform(self, event):
		if isinstance(event, ConnectionUp): # switch up
			self._handleConnectionUp(event)
			return

		if isinstance(event, ConnectionDown): # switch down
			self._handleConnectionDown()
			return

		if not self.connected: # not up yet
			return

		if event.dpid != self.dpid: # not from my switch
			log.warning("Not from my switch")
			return

		if isinstance(event, PacketIn): # not PacketIn
			self._handlePacketIn(event)

	def _handleConnectionUp(self, event):
		self.connected = True
		self.connection = event.connection
		self.dpid = event.dpid

	def _handleConnectionDown(self):
		self.connected = False
		self.connection = None
		self.dpid = None

	def _handlePacketIn(self, event):
		packet = event.parse()

		def flood():
			if event.ofp.buffer_id == -1:
				log.warning("Not flooding unbuffered packet on %s",
							dpidToStr(event.dpid))
				return
			msg = of.ofp_packet_out()
			if time.time() - event.connection.connect_time > 5:
				msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
			msg.buffer_id = event.ofp.buffer_id
			msg.in_port = event.port
			self.connection.send(msg)

		def drop(duration = None):
			if duration is not None:
				msg = of.ofp_flow_mod()
				msg.match = of.ofp_match.from_packet(packet)
				msg.idle_timeout = duration
				msg.hard_timeout = duration
				msg.buffer_id = event.ofp.buffer_id
				self.connection.send(msg)
			elif event.ofp.buffer_id != -1:
				msg = of.ofp_packet_out()
				msg.buffer_id = event.ofp.buffer_id
				msg.in_port = event.port
				self.connection.send(msg)

		self.mac2Port[packet.src] = event.port # 1
		# Ignore Case #2
		if packet.dst.isMulticast():
			flood() # 3a
		else:
			if packet.dst not in self.mac2Port: #4
				log.debug("Port for %s unknown -- flooding" % packet.dst)
				flood() # 4a
			else:
				port = self.mac2Port[packet.dst]
				if port == event.port: #5
					# 5a
					log.warning("Same port for packet from %s -> %s on %s.  Drop."
						% (packet.src, packet.dst, dpidToStr(event.dpid)))
					drop(10)
					return
				# 6
				log.debug("installing flow for %s.%i -> %s.%i" %
						  (packet.src, event.port, packet.dst, port))
				msg = of.ofp_flow_mod()
				msg.match = of.ofp_match.from_packet(packet, event.port)
				msg.idle_timeout = 10
				msg.hard_timeout = 30
				msg.actions.append(of.ofp_action_output(port = port))
				msg.buffer_id = event.ofp.buffer_id # 6a
				self.connection.send(msg)

			
class PrintTwo(Action):
	def perform(self, event):
		print '[2]',

class PrintEvent(Action):
	def perform(self, event):
		print 'Unhandled event: ',

		if isinstance(event, ConnectionUp):
			print 'ConnectionUp from switch %s' % dpidToStr(event.dpid)
		elif isinstance(event, ConnectionDown):
			print 'ConnectionDown from switch %s' % dpidToStr(event.dpid)	
		elif isinstance(event, PacketIn):
			print 'PacketIn from switch %s' % dpidToStr(event.dpid)
		else:
			print event

class RandomSelector(Selector):
	def select(self, event):
		return [2, 3, 9]
