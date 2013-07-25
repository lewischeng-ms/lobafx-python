from lobafx.lang.predicate import AtomicPredicate
from lobafx.lang.selector import Selector
from lobafx.lang.action import Action
from pox.lib.revent import *
from pox.openflow import ConnectionUp, ConnectionDown, PacketIn, ErrorIn, PortStatsReceived
from pox.core import GoingDownEvent
from pox.lib.util import dpidToStr, strToDPID
from pox.lib.addresses import EthAddr, IPAddr
from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
import threading
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
		
class IsConnectionUp(AtomicPredicate):
	def test(self, event):
		return isinstance(event, ConnectionUp)
		
class IsConnectionDown(AtomicPredicate):
	def test(self, event):
		return isinstance(event, ConnectionDown)
		
class IsGoingDown(AtomicPredicate):
	def test(self, event):
		return isinstance(event, GoingDownEvent)

class IsPortStatsReceived(AtomicPredicate):
	def test(self, event):
		return isinstance(event, PortStatsReceived)

class FromSwitch(AtomicPredicate):
	def __init__(self, dpidStr):
		super(FromSwitch, self).__init__()
		self.dpidStr = dpidStr

	def test(self, event):
		return dpidToStr(event.connection.dpid) == self.dpidStr

class InPort(AtomicPredicate):
	def __init__(self, port):
		super(InPort, self).__init__()
		self.port = port

	def test(self, event):
		return isinstance(event, PacketIn) and event.port == self.port

class DstPort(AtomicPredicate):
	def __init__(self, port):
		super(DstPort, self).__init__()
		self.port = port

	def test(self, event):
		if not isinstance(event, PacketIn):
			return

		packet = event.parse()
		tcp = packet.find("tcp")

		return tcp != None and tcp.dstport == self.port

class DstIp(AtomicPredicate):
	def __init__(self, ipStr):
		super(DstIp, self).__init__()
		self.ipAddr = IPAddr(ipStr)

	def test(self, event):
		if not isinstance(event, PacketIn):
			return

		packet = event.parse()
		ipv4 = packet.find("ipv4")

		return ipv4 != None and ipv4.dstip == self.ipAddr
        

class SrcIp(AtomicPredicate):
	def __init__(self, ipStr):
		super(SrcIp, self).__init__()
		self.ipAddr = IPAddr(ipStr)

	def test(self, event):
		if not isinstance(event, PacketIn):
			return

		packet = event.parse()
		ipv4 = packet.find("ipv4")

		return ipv4 != None and ipv4.srcip == self.ipAddr

def HttpTo(host):
	return DstIp(host.ipStr) & DstPort(80)

class SrcPort(AtomicPredicate):
	def __init__(self, port):
		super(SrcPort, self).__init__()
		self.port = port

	def test(self, event):
		if not isinstance(event, PacketIn):
			return

		packet = event.parse()
		tcp = packet.find("tcp")

		return tcp != None and tcp.srcport == self.port

def HttpFrom(host):
    return SrcIp(host.ipStr) & SrcPort(80)

def HttpFromAny():
	return SrcPort(80)

class PrintError(Action):
	def perform(self, event):
		print 'Error: \'%s\' from switch %s' % (dpidToStr(event.dpid), event.asString())

######## Predicate: ArpRequestTo ########
class ArpRequestTo(AtomicPredicate):
	def __init__(self, ipStr):
		super(ArpRequestTo, self).__init__()
		self.ipAddr = IPAddr(ipStr)

	def test(self, event):
		packet = event.parse()
		arp = packet.find("arp")

		return arp != None and arp.opcode == arp.REQUEST and \
			arp.prototype == arp.PROTO_TYPE_IP and \
			arp.protodst == self.ipAddr

######## Predicate: ArpRequest ########
class ArpRequest(AtomicPredicate):
	def test(self, event):
		if not isinstance(event, PacketIn):
			return

		packet = event.parse()
		arp = packet.find("arp")

		return arp != None and arp.opcode == arp.REQUEST

######## Predicate: ArpReply ########
class ArpReply(AtomicPredicate):
	def test(self, event):
		if not isinstance(event, PacketIn):
			return

		packet = event.parse()
		arp = packet.find("arp")

		return arp != None and arp.opcode == arp.REPLY

######## Action: ArpReplyWith ########
class ArpReplyWith(Action):
	def __init__(self, macStr):
		super(ArpReplyWith, self).__init__()
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
	def test(self, event):
		packet = event.parse()
		icmp = packet.find("icmp")

		return icmp != None and  icmp.type == pkt.TYPE_ECHO_REQUEST

def EchoRequestTo(ipStr):
	return EchoRequest() & DstIp(ipStr)

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

######## Action: SimpleForward ########
class SimpleForward(Action):
	def __init__(self, port):
		self.port = port

	def perform(self, event):
		if not isinstance(event, PacketIn):
			return

		msg = of.ofp_packet_out()
		msg.actions.append(of.ofp_action_output(port = self.port))
		msg.buffer_id = event.ofp.buffer_id
		msg.in_port = event.port

		event.connection.send(msg)

######## VirtualGateway ########
'''
Act as a virtual gateway in the network.

Can reply to arp and ping as if it were a real gateway.
'''
class VirtualGateway(object):
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
		# The makes the gateway reply to arp requests.
		(FromSwitch(self.dpidStr) & InPort(self.port) & ArpRequestTo(self.ipStr)) >> \
			[ ArpReplyWith(self.macStr) ]

		# This makes the gateway reply to echo requests.
		(FromSwitch(self.dpidStr) & InPort(self.port) & EchoRequestTo(self.ipStr)) >> \
			[ EchoReply() ]

		# This allows arp request to go out.
		(FromSwitch(self.dpidStr) & ~InPort(self.port) & ArpRequest()) >> \
			[ SimpleForward(self.port) ]

		# This allows arp reply to go in.
		(FromSwitch(self.dpidStr) & InPort(self.port) & ArpReply()) >> \
			[ SimpleForward(of.OFPP_FLOOD) ]

######## Host ########
'''
Represent a real host in the network.
'''
class Host(object):
	def __init__(self, ipStr, macStr, port):
		self.ipStr = ipStr
		self.ipAddr = IPAddr(ipStr)

		self.macStr = macStr
		self.macAddr = EthAddr(macStr)

		self.port = port

		self.load = 0
		
		from lobafx.fx.core import hostMgr
		hostMgr.register(self)

######## Link ########
'''
Represent a link in the network.
'''
class Link(object):
    def __init__(self, switch1, port1, switch2, port2):
        self.switch1 = switch1
        self.port1 = port1
        self.switch2 = switch2
        self.port2 = port2
        self.stats = None
		
        from lobafx.fx.core import linkMgr
        linkMgr.register(self)
	
    def __str__(self):
        return "'%s[%d]' => '%s[%d]'" % ( \
            self.switch1.dpidStr, \
            self.port1, \
            self.switch2.dpidStr, \
            self.port2)
			
    @property
    def load(self):
        if self.stats is None:
            return 0
        return self.stats.tx_bytes + self.stats.rx_bytes

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

######## Actions: ApplyLink, ApplyReverseLink ########
class ApplyForwardLink(Action):
	def __init__(self):
		super(ApplyForwardLink, self).__init__()
    
	def perform(self, event):
		if not isinstance(event, PacketIn):
			return
		
		selection = self._getSelection(event)
        
		if len(selection) < 1:
			log.warning("No link is selected to apply")
			return
            
		link = selection[0]
		log.info("Apply link %s whose load is %d" % (link, link.load))
        
		if not link.switch1.test(event):
			log.warning("The link is not associated to the switch")
			return
        
		packet = event.parse()

		msg = of.ofp_flow_mod()
		msg.match = of.ofp_match.from_packet(packet)
		msg.idle_timeout = 3
		msg.hard_timeout = 10
		msg.actions.append(of.ofp_action_output(port = link.port1))
		msg.buffer_id = event.ofp.buffer_id

		event.connection.send(msg)
        
class ApplyReverseLink(Action):
	def __init__(self):
		super(ApplyReverseLink, self).__init__()
    
	def perform(self, event):
		if not isinstance(event, PacketIn):
			return
			
		selection = self._getSelection(event)
        
		if len(selection) < 1:
			log.warning("No link is selected to apply")
			return
            
		link = selection[0]
		log.info("Apply reverse link %s whose load is %d" % (link, link.load))
        
		if not link.switch2.test(event):
			log.warning("The link is not associated to the switch")
			return
        
		packet = event.parse()

		msg = of.ofp_flow_mod()
		msg.match = of.ofp_match.from_packet(packet)
		msg.idle_timeout = 3
		msg.hard_timeout = 10
		msg.actions.append(of.ofp_action_output(port = link.port2))
		msg.buffer_id = event.ofp.buffer_id

		event.connection.send(msg)

######## Actions: ForwardProxy, ReverseProxy ########
class ForwardProxy(Action):
	def __init__(self):
		super(ForwardProxy, self).__init__()

	def perform(self, event):
		# Get selection result from selector.
		selection = self._getSelection(event)

		if len(selection) < 1:
			log.warning("No member is selected to proxy")
			return

		# Just need one.
		member = selection[0]

		packet = event.parse()

		msg = of.ofp_flow_mod()
		msg.match = of.ofp_match.from_packet(packet, event.port)
		msg.idle_timeout = 3
		msg.hard_timeout = 10
		msg.actions.append(of.ofp_action_nw_addr.set_dst(member.ipAddr))
		msg.actions.append(of.ofp_action_dl_addr.set_dst(member.macAddr))
		msg.actions.append(of.ofp_action_output(port = member.port))
		msg.buffer_id = event.ofp.buffer_id

		event.connection.send(msg)

class ReverseProxy(Action):
	def __init__(self, vgw):
		super(ReverseProxy, self).__init__()
		self.vgw = vgw

	def perform(self, event):
		packet = event.parse()

		msg = of.ofp_flow_mod()
		msg.match = of.ofp_match.from_packet(packet, event.port)
		msg.idle_timeout = 3
		msg.hard_timeout = 10
		msg.actions.append(of.ofp_action_nw_addr.set_src(self.vgw.ipAddr))
		msg.actions.append(of.ofp_action_dl_addr.set_src(self.vgw.macAddr))
		msg.actions.append(of.ofp_action_output(port = self.vgw.port))
		msg.buffer_id = event.ofp.buffer_id
		
		event.connection.send(msg)

class PrintLoad(Action):
	def perform(self, event):
		print 'Load dist:',
		for host in self._getSelection(event):
			print host.load,
		print
			
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
			print 'PacketIn from switch %s [%d]' % (dpidToStr(event.dpid), event.port)
		else:
			print event
	  
import random
class RandomSelector(Selector):
	def __init__(self, members):
		super(RandomSelector, self).__init__()
		self.members = members

	def select(self, event):
		return [ random.choice(self.members) ]

class RoundRobinSelector(Selector):
	def __init__(self, members):
		super(RoundRobinSelector, self).__init__()
		self.members = members
		self.index = 0

	def select(self, event):
		ret = [ self.members[self.index] ]
		self.index = (self.index + 1) % len(self.members)
		return ret

class SelectLowestLoad(Selector):
	def __init__(self, members):
		super(SelectLowestLoad, self).__init__()
		self.members = members

	def select(self, event):
		if len(self.members) < 1:
			return []

		minMember = self.members[0]
		minLoad = minMember.load

		for member in self.members:
			if member.load < minLoad:
				minMember = member
				minLoad = member.load

		return [ minMember ]


class SelectAll(Selector):
	def __init__(self, members):
		super(SelectAll, self).__init__()
		self.members = members

	def select(self, event):
		return self.members
