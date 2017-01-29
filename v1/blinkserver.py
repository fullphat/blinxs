print ''
print 'Blink(1) Server Beta 1 (R0.4)'
''' Copyright (c) full phat products
    Usage: python blinkserver.py [port]
    [port] will default to 8888 if not supplied

    Credit to binary tides for python threaded socket code '''

import commands
import socket
import sys
from thread import *
from subprocess import call
from urlparse import urlparse, parse_qs
import os
 
HOST = ''
PORT = 8888

print 'Copyright (c) full phat products'

if len(sys.argv) > 1:
    if sys.argv[1] == '-?' or sys.argv[1] == '--help':
        print 'Usage: python blinkserver.py [port]'
        sys.exit()

    try:
        PORT = int(sys.argv[1])

    except:
        print '[Error] Invalid port specified: ' + sys.argv[1]
        sys.exit()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#print 'Socket created'
 
#Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    #print '  [Error] Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    print '[Error] Bind failed: you most likely already have something listening on port ' + str(PORT) 
    sys.exit()
     
#Start listening on socket
s.listen(10)
print '[Info] Now listening for incoming requests on port ' + str(PORT)
 
#Function for handling connections. This will be used to create threads
def clientthread(conn):
    #print 'Thread started...'
    #wait for data
    request = conn.recv(2048)
    #print 'Received: ' + request
    #print 'Received request'

    uri = ''
    entries = request.split('\r\n', 1)
    if len(entries) > 0:
        header = entries[0]
        chunks = header.split(' ')
        if len(chunks) == 3:
            uri = chunks[1]

    response = 'ERROR'
    #uri = uri.strip('/')

    # set defaults
    _device = '0'
    _mode = 'off'
    _rgb = 'ffffff'
    _count = '6'
    _sync = False

    cmd = ''

    print '[Info] Request is: "' + uri + '"'

    try:
        o = urlparse(uri.strip('/'))
        #print 'query: ' + o.query
        #print 'path: ' + o.path

    except:
        print "[Error] Couldn't parse the URL"
        uri = ''

    if uri != '':
        # check api version (path)
        if o.path == 'v1':
            # turn the query part into args
            d = parse_qs(o.query)
            #print 'args...'
            #print d

            if 'device' in d:
                _device = d['device'][0]

            if 'mode' in d:
                _mode = d['mode'][0]

            if 'rgb' in d:
                _rgb = d['rgb'][0]

            if 'count' in d:
                _count = d['count'][0]


            #print 'mode: ' + _mode

            if _device == 'all' or _device == '*':
                cmd = '--id=all '

            else:
                cmd = '--id=' + _device + ' '


            if _mode == 'on':
                cmd = cmd + '--rgb ' + _rgb;

            elif _mode == 'off':
                cmd = cmd + '--off'

            elif _mode == 'glimmer':
                cmd = cmd + '--rgb ' + _rgb + ' --glimmer=' + _count

            elif _mode == 'blink':
                cmd = cmd + '--rgb ' + _rgb + ' --blink=' + _count

            elif _mode == 'status':
                cmd = cmd + '--rgbread'
                _sync = True

        else:
            print "[Error] invalid api version specified"
            uri = ''

    if uri != '':
        #went ok
        response = 'OK'
        #print "[Info] command is: " + cmd

        if _sync:
            # run command synchronously and capture STDOUT
            output = commands.getoutput('sudo ./blink1-tool -q ' + cmd)
            print '[Info] Ran synchronously: output was "' + output + '"'
            # only mode that does this is 'status'...
            if output == '0x00,0x00,0x00':
                response = '0'

            else:
                response = '1'

        else:
            # run asynchronously
            os.system('sudo ./blink1-tool -q ' + cmd + ' &')
        #os.system('sudo ./blink1-tool -q --rgb ' + args[1] + ' --glimmer 6')
        #call(["sudo", "./blink1-tool -q " + cmd])


    # build the http reply
    #body = '<html><body>' + response + '</body></html>'
    body = response
    reply = 'HTTP/1.1 200 OK\r\nContent-Length: ' + str(len(body)) + '\r\n\r\n' + body

    print '[Info] Sending reply "' + body + '"...'
    conn.sendall(reply)
    conn.close()


 
#now keep talking with the client
while 1:
    #wait to accept a connection - blocking call
    try:
        conn, addr = s.accept()
        print '[Info] Connection made from ' + addr[0] + ':' + str(addr[1])
     
        #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the 
        #function.
        start_new_thread(clientthread ,(conn,))
 
    except (KeyboardInterrupt):
        print ''
        print 'SIGINT received: ending...'
        s.close()
        sys.exit()
