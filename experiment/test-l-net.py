#!/usr/bin/python

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, UserSwitch
from mininet.topo import Topo
from mininet.util import irange, ensureRoot

class LobaTopo(Topo):
	def __init__(self, **opts):
		super(LobaTopo, self).__init__(**opts)

		s1 = self.addSwitch('s1') # client switch
		s2 = self.addSwitch('s2', listenPort = 8890) # end point 1
		s3 = self.addSwitch('s3') # path 1
		s4 = self.addSwitch('s4') # path 2
		s5 = self.addSwitch('s5') # path 3
		s6 = self.addSwitch('s6', listenPort = 8891) # end point 2

		h1 = self.addHost('h1', ip = '10.0.0.1')
		self.addLink(h1, s1)
		
		h2 = self.addHost('h2', ip = '10.0.0.2')
		self.addLink(h2, s1)

		self.addLink(s2, s3)
		self.addLink(s2, s4)
		self.addLink(s2, s5)
		self.addLink(s1, s2)

		self.addLink(s3, s6)
		self.addLink(s4, s6)
		self.addLink(s5, s6)

		h3 = self.addHost('h3', ip = '10.0.0.254', \
			mac = '02:00:DE:AD:BE:EF')
		self.addLink(h3, s6)

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
