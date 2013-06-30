from lobafx.nal import Nal
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from pox.lib.revent import *
from pox.core import core

log = core.getLogger('nal.poxnal')

import pox
import pox.openflow
import pox.openflow.of_01 as of_01
import pox.openflow.connection_arbiter as ca 
import logging
import time

# Adapted from pox.py.
def _setup_logging():
	# This is kind of a hack, but we need to keep track of the handler we
	# install so that we can, for example, uninstall it later.  This code
	# originally lived in pox.core, so we explicitly reference it here.
	pox.core._default_log_handler = logging.StreamHandler()
	formatter = logging.Formatter(logging.BASIC_FORMAT)
	pox.core._default_log_handler.setFormatter(formatter)
	logging.getLogger().addHandler(pox.core._default_log_handler)
	logging.getLogger().setLevel(logging.DEBUG)

def loadPrettyLog():
	import pox.log.color
	pox.log.color.launch()
	import pox.log
	pox.log.launch(format="[@@@bold@@@level%(name)-22s@@@reset] " +
						  "@@@bold%(message)s@@@normal")

class _Controller(EventMixin):
	def __init__(self, nal):
		self.nal = nal
		self.listenTo(core)
	
	def _handle_GoingUpEvent(self, event):
		self.listenTo(core.openflow)

	def _handle_ConnectionUp(self, event):
		self.postEvent(event)
	
	def _handle_ConnectionDown(self, event):
		self.postEvent(event)

	def _handle_PacketIn(self, event):
		self.postEvent(event)

	def _handle_ErrorIn(self, event):
		self.postEvent(event)

	def postEvent(self, event):
		self.nal.listener.onEvent(event)

class POXNal(Nal):
	def startup(self):
		try:
			_setup_logging()

			# pre-startup
			ca.launch() # Default OpenFlow launch
			
			# launch components
			loadPrettyLog()
			of_01.launch(port = 8888)
			core.registerNew(_Controller, nal = self)

			# post-startup
			core.goUp()
			
			# forever loop for messaging.
			while True:
				time.sleep(5)
		except:
			core.quit()

