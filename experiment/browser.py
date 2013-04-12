#!/usr/bin/python

import httplib

hostname = '10.0.0.254'
#hostname = '127.0.0.1'

if __name__ == '__main__':
	conn = httplib.HTTPConnection(hostname)
	print 'Requesting \'http://%s/index.htm\'...' % hostname
	conn.request('GET', '/index.htm')
	res = conn.getresponse()
	print res.status, res.reason
	if res.status == 200:
		print res.read()
	conn.close()
