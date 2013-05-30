#!/usr/bin/python

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, UserSwitch
from mininet.topo import Topo
from mininet.util import irange, ensureRoot

class LobaTopo(Topo):
	'''Single switch connected to p clients and q servers.'''

	def __init__(self, p = 2, q = 3, **opts):
		super(LobaTopo, self).__init__(**opts)

		self.p = p
		self.q = q

		clientSwitch = self.addSwitch('s1')
		loadBalancer = self.addSwitch('s2', listenPort = 8889)

		self.addLink(clientSwitch, loadBalancer)

		for i in irange(1, p):
			client = self.addHost('h%d' % i, ip = '10.0.0.%d' % i)
			self.addLink(client, clientSwitch)

		for i in irange(1, q):
			server = self.addHost('m%d' % i, ip = '192.168.0.%d' % i)
			self.addLink(server, loadBalancer)

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
