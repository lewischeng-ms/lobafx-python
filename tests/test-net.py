#!/usr/bin/python

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, UserSwitch, OVSKernelSwitch
from mininet.topo import Topo
from mininet.util import irange, ensureRoot

class LobalTopo(Topo):
	'''Single switch connected to p clients and q servers.'''

	def __init__(self, p = 2, q = 3, **opts):
		super(LobalTopo, self).__init__(**opts)

		self.p = p
		self.q = q

		l2SwitchClients = self.addSwitch('s1')
		loadBalancer = self.addSwitch('s2')
		l2SwitchServers = self.addSwitch('s3')

		self.addLink(l2SwitchClients, loadBalancer)
		self.addLink(loadBalancer, l2SwitchServers)

		for i in irange(1, p):
			client = self.addHost('p%d' % i, ip = '10.0.0.%d' % i)
			self.addLink(client, l2SwitchClients)

		for i in irange(1, q):
			server = self.addHost('q%d' % i, ip = '10.0.0.%d' % (100 + i))
			self.addLink(server, l2SwitchServers)

def testNet():
	net = Mininet(topo = LobalTopo(), build = False, switch = OVSKernelSwitch)
    
	# Add my remote controller
	info('*** Adding controller\n')
	net.addController('c0', RemoteController, ip = '127.0.0.1', port = 8888)
	info('c0\n')

	net.run(CLI, net)

if __name__ == '__main__':
	ensureRoot()
	setLogLevel('info')
	testNet()
