#!/usr/bin/python

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, UserSwitch
from mininet.topo import Topo
from mininet.util import irange, ensureRoot

class LobaTopo(Topo):
	'''Single switch connected to 2 clients and 3 servers.'''

	def __init__(self, **opts):
		super(LobaTopo, self).__init__(**opts)

		s1 = self.addSwitch('s1')
		s2 = self.addSwitch('s2', listenPort = 8889)

		self.addLink(s1, s2)

		h1 = self.addHost('h1', ip = '10.0.0.1')
		self.addLink(h1, s1)
		
		h2 = self.addHost('h2', ip = '10.0.0.2')
		self.addLink(h2, s1)

		m1 = self.addHost('m1', ip = '10.0.0.101', \
			mac = 'D6:F6:C3:05:CA:B9')
		self.addLink(m1, s2)

		m2 = self.addHost('m2', ip = '10.0.0.102', \
			mac = '76:4F:72:F3:10:59')
		self.addLink(m2, s2)

		m3 = self.addHost('m3', ip = '10.0.0.103', \
			mac = '36:8A:3B:4D:EF:2E')
		self.addLink(m3, s2)

def testNet():
	net = Mininet(topo = LobaTopo(), build = False, switch = UserSwitch)
    
	# Add my remote controller
	info('*** Adding controller\n')
	net.addController('c0', RemoteController, ip = '10.37.129.2', port = 8888)
	info('c0\n')

	net.run(CLI, net)

if __name__ == '__main__':
	ensureRoot()
	setLogLevel('info')
	testNet()
