#!/usr/bin/python

import sys
import SimpleHTTPServer

program = sys.argv[0]

# Tell Simple HTTP Server to use port 80
# Note: this requires root permission
sys.argc = 2
sys.argv = [program, '80']

SimpleHTTPServer.test()
