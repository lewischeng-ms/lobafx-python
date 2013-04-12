#!/usr/bin/python

import copy

from pox.core import core
log = core.getLogger()

import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt

from pox.lib.addresses import EthAddr, IPAddr
from pox.lib.revent import *

def loadPrettyLog():
	import pox.log.color
	pox.log.color.launch()
	import pox.log
	pox.log.launch(format="[@@@bold@@@level%(name)-22s@@@reset] " +
	                      "@@@bold%(message)s@@@normal")

def loadOpenFlow():
	import pox.openflow.of_01 as of_01
	of_01.launch(port = 8888)

class Foo(EventMixin):
	def __init__(self):
		self.connection = None
		
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

	def insertFlow(self, packet, connection, buffer_id):
		log.debug('Installing flow on switch %d' % self.dpid)

		msg = of.ofp_flow_mod()
		msg.match.dl_type = pkt.ethernet.IP_TYPE
		msg.match.nw_src = IPAddr('10.0.0.1')
		msg.buffer_id = buffer_id
		msg.actions.append(of.ofp_action_nw_addr.set_dst(IPAddr('10.0.0.102')))
		msg.actions.append(of.ofp_action_dl_addr.set_dst(EthAddr('00:00:01:02:03:04')))
		msg.actions.append(of.ofp_action_output(port = 2))
		
		connection.send(msg.pack())
		
	def _handle_PacketIn(self, event):
		self.insertFlow(event.parse(), event.connection, event.ofp.buffer_id)

	def _handle_ConnectionDown(self, event):
		self.disconnect()

class TestController(EventMixin):
	'''The controller is designed for the LobaTopo.'''

	def __init__(self):
		self.foo = None

		# Listen to core.openflow so that we can receive ConnectionUp events.
		self.listenTo(core.openflow)

	def _handle_ConnectionUp(self, event):
		if self.foo is None:
			self.foo = Foo()
		self.foo.connect(event.connection)		

def launch():
	loadPrettyLog()
	loadOpenFlow()
	core.registerNew(TestController)

