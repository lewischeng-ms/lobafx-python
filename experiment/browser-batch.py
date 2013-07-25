#!/usr/bin/python

import httplib

hostname = '10.0.0.254'
#hostname = '127.0.0.1'

if __name__ == '__main__':
	conn = httplib.HTTPConnection(hostname)
	count = 1000
	print 'Requesting \'http://%s/index.htm\' for %d times...' % (hostname, count)
	for i in range(0, count):
		conn.request('GET', '/index.htm')
		res = conn.getresponse()
		conn.close()
		if i % 100 == 0:
			print '%d requests sent' % i
	print 'Requests completed'

