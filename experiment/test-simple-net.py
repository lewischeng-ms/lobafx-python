#!/usr/bin/python

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, UserSwitch
from mininet.topo import Topo
from mininet.util import ensureRoot

class LobaTopo(Topo):
	'''Single switch connected to two hosts.'''

	def __init__(self, **opts):
		super(LobaTopo, self).__init__(**opts)
		switch = self.addSwitch('s1', listenPort = 8889)	
		host1 = self.addHost('h1', ip = '10.0.0.1')
		host2 = self.addHost('h2', ip = '10.0.0.2')
		self.addLink(host1, switch)
		self.addLink(host2, switch)

def testNet():
	net = Mininet(topo = LobaTopo(), build = False, switch = UserSwitch)
    
	# Add my remote controller
	info('*** Adding controller\n')
	net.addController('c0', RemoteController, ip = '127.0.0.1', port = 8888)
	info('c0\n')

	net.run(CLI, net)

if __name__ == '__main__':
	ensureRoot()
	setLogLevel('info')
	testNet()
