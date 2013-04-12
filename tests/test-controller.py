#!/usr/bin/python

import copy

from pox.core import core
log = core.getLogger()

import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt

from pox.lib.addresses import EthAddr, IPAddr
from pox.lib.util import dpidToStr
from pox.lib.revent import *
from pox.forwarding.l2_learning import LearningSwitch

def loadPrettyLog():
	import pox.log.color
	pox.log.color.launch()
	import pox.log
	pox.log.launch(format="[@@@bold@@@level%(name)-22s@@@reset] " +
	                      "@@@bold%(message)s@@@normal")

def loadOpenFlow():
	import pox.openflow.of_01 as of_01
	of_01.launch(port = 8888)

class VirtualHost(object):
	def __init__(self, ip, mac):
		self.ip = ip
		self.mac = mac

	def arpToMe(self, packet):
		a = packet.find("arp")

		return a.opcode == a.REQUEST and \
			a.prototype == a.PROTO_TYPE_IP and \
			a.protodst == self.ip

	def pingToMe(self, packet):
		n = packet.find("ipv4")
		i = packet.find("icmp")

		return i.type == pkt.TYPE_ECHO_REQUEST and \
			n.dstip == self.ip

	def replyArp(self, packet):
		a = packet.find("arp")

		r = pkt.arp()
		r.hwtype = a.hwtype
		r.prototype = a.prototype
		r.hwlen = a.hwlen
		r.protolen = a.protolen
		r.opcode = r.REPLY
		r.hwdst = a.hwsrc
		r.protodst = a.protosrc
		r.protosrc = self.ip
		r.hwsrc = self.mac
		
		e = pkt.ethernet(type = packet.type, src = self.mac, dst = packet.src)
		e.payload = r

		return e.pack()

	def replyPing(self, packet):
		n = packet.find("ipv4")
		i = packet.find("icmp")

		icmp = pkt.icmp()
		icmp.type = pkt.TYPE_ECHO_REPLY
		icmp.payload = i.payload

		ipp = pkt.ipv4()
		ipp.protocol = ipp.ICMP_PROTOCOL
		ipp.srcip = n.dstip
		ipp.dstip = n.srcip

		e = pkt.ethernet()
		e.src = packet.dst
		e.dst = packet.src
		e.type = e.IP_TYPE

		ipp.payload = icmp
		e.payload = ipp

		return e.pack()

class Host(object):
	def __init__(self, ip, mac):
		self.ip = ip
		self.mac = mac
	
	def replyArp(self, packet):
		a = packet.find("arp")

		r = pkt.arp()
		r.hwtype = a.hwtype
		r.prototype = a.prototype
		r.hwlen = a.hwlen
		r.protolen = a.protolen
		r.opcode = r.REPLY
		r.hwdst = a.hwsrc
		r.protodst = a.protosrc
		r.protosrc = self.ip
		r.hwsrc = self.mac

		e = pkt.ethernet(type = packet.type, src = self.mac, dst = packet.src)
		e.payload = r

		return e.pack()

class LoadBalancer(EventMixin):
	SERVER_IPs = [ \
		IPAddr('10.0.0.101'), \
		IPAddr('10.0.0.102'), \
		IPAddr('10.0.0.103') \
	]
	
	def __init__(self, publicPort, privatePort):
		self.publicPort = publicPort
		self.privatePort = privatePort
		
		self.connection = None
		
		self.vhost = VirtualHost( \
			IPAddr('10.0.0.254'), \
			EthAddr('02:00:DE:AD:BE:EF') \
		)
		
		self.hosts = {}

	def connect(self, connection):
		self.connection = connection
		self.dpid = connection.dpid
		
		self._listeners = self.listenTo(connection)
		
	def disconnect(self):
		if self.connection:
			self.connection.removeListeners(self._listeners)
			
			self.connection = None
			self.dpid = None
			self._listeners = None

	def sendToPublicPort(self, packet):
		msg = of.ofp_packet_out()
		msg.data = packet
		msg.actions.append(of.ofp_action_output(port = self.publicPort))
		self.connection.send(msg)
	
	def sendToPrivatePort(self, packet):
		msg = of.ofp_packet_out()
		msg.data = packet
		msg.actions.append(of.ofp_action_output(port = self.privatePort))
		self.connection.send(msg)

	def forwardProxy(self, packet):
		return
		log.debug('Installing flow for forward proxy on switch %d' % self.dpid)

		# From exterior to interior.
		n = packet.find("ipv4")

		msg = of.ofp_flow_mod()
		msg.match.dl_type = pkt.ethernet.IP_TYPE;
		msg.match.nw_src = n.srcip
		#msg.buffer_id = buffer_id
		msg.actions.append(of.ofp_action_nw_addr.set_dst(IPAddr('10.0.0.102')))
		msg.actions.append(of.ofp_action_dl_addr.set_dst(self.hosts[IPAddr('10.0.0.102')].mac))
		msg.actions.append(of.ofp_action_output(port = self.privatePort))
		
		self.connection.send(msg)
		
	def reverseProxy(self, packet):
		log.debug('Installing flow for reverse proxy on switch %d' % self.dpid)

		# From interior to exterior.
		#n = packet.find("ipv4")

		msg = of.ofp_flow_mod()
		#msg.match.dl_type = pkt.ethernet.IP_TYPE;
		#msg.match.nw_src = self.vhost.ip
		#msg.match.nw_proto = pkt.ipv4.TCP_PROTOCOL
		#msg.match.tp_src = 80
		msg.match=of.ofp_match.from_packet(packet)
		#msg.buffer_id = buffer_id
		msg.actions.append(of.ofp_action_nw_addr.set_src(self.vhost.ip))
		msg.actions.append(of.ofp_action_dl_addr.set_src(self.vhost.mac))
		msg.actions.append(of.ofp_action_output(port = self.publicPort))

		self.connection.send(msg)

	def reverseArp(self, packet):
		a = packet.find("arp")

		r = pkt.arp()
		r.hwtype = a.hwtype
		r.prototype = a.prototype
		r.hwlen = a.hwlen
		r.protolen = a.protolen
		r.opcode = a.opcode
		r.hwdst = a.hwdst
		r.protodst = a.protodst
		r.protosrc = self.vhost.ip
		r.hwsrc = self.vhost.mac

		e = pkt.ethernet(type = packet.type, src = self.vhost.mac, dst = packet.dst)
		e.payload = r

		return e.pack()
		
	def replyArp(self, packet):
		a = packet.find("arp")
		host = self.hosts.get(a.protodst)
		if host is None:
			self.sendToPublicPort(self.reverseArp(packet))
		else:
			self.sendToPrivatePort(host.replyArp(packet))

	def macLearning(self, packet):
		ip = None
		mac = packet.src

		if packet.find("ipv4"):
			n = packet.find("ipv4")
			ip = n.srcip
		elif packet.find("arp"):
			a = packet.find("arp")
			if a.prototype == a.PROTO_TYPE_IP:
				ip = a.protosrc

		if ip is not None and self.hosts.get(ip) is None:
			self.hosts[ip] = Host(ip, mac)
			log.debug('Learned: %s <=> %s' % (ip, mac))
		
	def _handle_PacketIn(self, event):
		packet = event.parse()
		log.debug('PacketIn')
		if packet.find("ipv4"):
			self.reverseProxy(packet)
		
		self.macLearning(packet)
		
		if event.port == self.publicPort:
			# The packet comes from exterior.
			if packet.find("arp") and self.vhost.arpToMe(packet):
				self.sendToPublicPort(self.vhost.replyArp(packet))
			elif packet.find("ipv4"):
				if packet.find("icmp") and self.vhost.pingToMe(packet):
					self.sendToPublicPort(self.vhost.replyPing(packet))
				else:
					self.forwardProxy(packet)
			else:
				# Ignore packets that are not arp, ip ones.
				pass
		elif event.port == self.privatePort:
			# The packet comes from interior.
			if packet.find("arp"):
				self.replyArp(packet)
			elif packet.find("ipv4"):
				self.reverseProxy(packet)
			else:
				# Ignore packets that are not arp, ip ones.
				pass
		else:
			log.error('Unknown port %d in switch (dpid = %d)' % \
				(event.port, self.dpid))

	def _handle_ConnectionDown(self, event):
		self.disconnect()

class TestController(EventMixin):
	'''The controller is designed for the LobalTopo.'''

	DPID_L2_SWITCH_CLIENTS = 1
	DPID_BALANCER = 2
	DPID_L2_SWITCH_SERVERS = 3

	def __init__(self):
		self.balancer = None
		
		# Listen to core.openflow so that we can receive ConnectionUp events.
		self.listenTo(core.openflow)

	def _handle_ConnectionUp(self, event):	
		if event.dpid == self.DPID_L2_SWITCH_CLIENTS or \
		   event.dpid == self.DPID_L2_SWITCH_SERVERS:
			# We make the switch which is connected by the clients (servers)
			# a learning switch so that the clients (servers) can communicate
			# with each other.
			# The switch is named 's1' ('s3') in Mininet.
			LearningSwitch(event.connection, False)
			log.debug('Learning switch %d' % event.dpid)
		elif event.dpid == self.DPID_BALANCER:
			# We make the switch which is connected by the servers a load-balancer.
			# The switch is named 's2' in Mininet.
			if self.balancer is None:
				self.balancer = LoadBalancer(1, 2)
			
			self.balancer.connect(event.connection)

			log.debug('Balancer switch %d' % event.dpid)
		else:
			log.error('Unrecognized switch (dpid = %d)' % event.dpid)

def launch():
	loadPrettyLog()
	loadOpenFlow()
	core.registerNew(TestController)

