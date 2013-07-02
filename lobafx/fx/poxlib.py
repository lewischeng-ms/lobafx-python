from lobafx.lang.predicate import AtomicPredicate
from lobafx.lang.selector import Selector
from lobafx.lang.action import Action
from pox.lib.revent import *
from pox.openflow import ConnectionUp, ConnectionDown, PacketIn, ErrorIn
from pox.lib.util import dpidToStr, strToDPID
from pox.lib.addresses import EthAddr, IPAddr
from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
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

class InPort(AtomicPredicate):
	def __init__(self, port):
		super(InPort, self).__init__()
		self.port = port

	def test(self, event):
		return isinstance(event, PacketIn) and event.port == self.port

class HttpTo(AtomicPredicate):
	def __init__(self, host):
		self.host = host

	def test(self, event):
		packet = event.parse()
		ipv4 = packet.find("ipv4")
		tcp = packet.find("tcp")

		return ipv4 != None and ipv4.dstip == host.ipAddr and \
			tcp != None and tcp.dstport == 80

class PrintError(Action):
	def perform(self, event):
		print 'Error: \'%s\' from switch %s' % (dpidToStr(event.dpid), event.asString())

######## Predicate: ArpRequest ########
class ArpRequest(AtomicPredicate):
	def __init__(self, ipStr):
		super(ArpRequest, self).__init__()
		self.ipAddr = IPAddr(ipStr)

	def test(self, event):
		packet = event.parse()
		arp = packet.find("arp")

		return arp != None and arp.opcode == arp.REQUEST and \
			arp.prototype == arp.PROTO_TYPE_IP and \
			arp.protodst == self.ipAddr

######## Action: ArpReply ########
class ArpReply(Action):
	def __init__(self, macStr):
		super(ArpReply, self).__init__()
		self.macAddr = EthAddr(macStr)

	def perform(self, event):
		packet = event.parse()
		a = packet.find("arp")

		# Create arp reply r.
		r = pkt.arp()
		r.hwtype = a.hwtype
		r.prototype = a.prototype
		r.hwlen = a.hwlen
		r.protolen = a.protolen
		r.opcode = r.REPLY
		r.hwdst = a.hwsrc
		r.protodst = a.protosrc
		r.protosrc = a.protodst
		r.hwsrc = self.macAddr
		
		# Create ethernet packet e.
		e = pkt.ethernet(type = packet.type, src = self.macAddr, dst = packet.src)
		e.payload = r

		# Create PacketOut msg.
		msg = of.ofp_packet_out()
		msg.data = e.pack()
		msg.in_port = event.port
		msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
		event.connection.send(msg)

######## Predicate: EchoRequest ########
class EchoRequest(AtomicPredicate):
	def __init__(self, ipStr):
		super(EchoRequest, self).__init__()
		self.ipAddr = IPAddr(ipStr)

	def test(self, event):
		packet = event.parse()
		ipv4 = packet.find("ipv4")
		icmp = packet.find("icmp")

		return icmp != None and  icmp.type == pkt.TYPE_ECHO_REQUEST and \
			ipv4 != None and ipv4.dstip == self.ipAddr

######## Action: EchoReply ########
class EchoReply(Action):
	def perform(self, event):
		packet = event.parse()
		n = packet.find("ipv4")
		i = packet.find("icmp")

		# Create echo reply icmp.
		icmp = pkt.icmp()
		icmp.type = pkt.TYPE_ECHO_REPLY
		icmp.payload = i.payload

		# Create ipv4 packet ipp.
		ipp = pkt.ipv4()
		ipp.protocol = ipp.ICMP_PROTOCOL
		ipp.srcip = n.dstip
		ipp.dstip = n.srcip

		# Create ethernet packet e.
		e = pkt.ethernet()
		e.src = packet.dst
		e.dst = packet.src
		e.type = e.IP_TYPE

		# Link the payloads.
		ipp.payload = icmp
		e.payload = ipp

		# Create PacketOut msg.
		msg = of.ofp_packet_out()
		msg.data = e.pack()
		msg.in_port = event.port
		msg.actions.append(of.ofp_action_output(port = of.OFPP_IN_PORT))
		event.connection.send(msg)

######## VirtualHost ########
'''
Act as a virtual host in the network.

Can reply to arp and ping as if it were a real host.
'''
class VirtualHost(object):
	def __init__(self, ipStr, macStr, dpidStr, port):
		self.ipStr = ipStr
		self.ipAddr = IPAddr(ipStr)

		self.macStr = macStr
		self.macAddr = EthAddr(macStr)

		self.dpidStr = dpidStr
		self.dpid = strToDPID(self.dpidStr)

		self.port = port

		self._installDefaultRules()

	def _installDefaultRules(self):
		# The following rule makes the virtual host reply to arp requests.
		(FromSwitch(self.dpidStr) & InPort(self.port) & ArpRequest(self.ipStr)) >> \
			[ ArpReply(self.macStr) ]

		# The following rule makes the virtual host reply to echo requests.
		(FromSwitch(self.dpidStr) & InPort(self.port) & EchoRequest(self.ipStr)) >> \
			[ EchoReply() ]

######## Host ########
'''
Represent a real host in the network.
'''
class Host(object):
	def __init__(self, ipStr, macStr):
		self.ipStr = ipStr
		self.ipAddr = IPAddr(ipStr)

		self.macStr = macStr
		self.macAddr = EthAddr(macStr)

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

######## Action: Proxy ########
class Proxy(Action):
	def __init__(self, virtualHost):
		super(Proxy, self).__init__()
		self.virtualHost = virtualHost

	def perform(self, event):
		# Get selection result from selector.
		selection = self._getSelection(event)

		if len(selection) < 1:
			log.warning("No member is selected to proxy")
			return

		# Just get the first one.
		member = selection[0]

		# install rules to proxy the communication between
		# virtualhost and member.
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

import random
class RandomMemberSelector(Selector):
	def __init__(self, members):
		super(RandomMemberSelector, self).__init__()
		self.members = members

	def select(self, event):
		return [ random.choice(self.members) ]
