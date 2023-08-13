from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver  import ThreadingMixIn
import threading
from urllib import parse
import time
import random
import math
import argparse
import queue
import time
import threading
import _thread
from functools import reduce
import bisect
import numpy as np
import pandas
import requests

class ZipfGenerator:
    def __init__(self, n, alpha):
        # Calculate Zeta values from 1 to n:
        tmp = [1. / (math.pow(float(i), alpha)) for i in range(1, n+1)]
        zeta = reduce(lambda sums, x: sums + [sums[-1] + x], tmp, [0])
        # Store the translation map:
        self.distMap = [x / zeta[-1] for x in zeta]
    def next(self):
        # Take a uniform 0-1 pseudo-random value:
        u = random.random()
        # Translate the Zipf variable:
        return bisect.bisect(self.distMap, u) - 1

class Request:

    def __init__(self, blocks, delay):
        self.blocks = blocks
        self.delay = delay
        self.sem = threading.Semaphore()

cpuQ = queue.Queue()

cpustat = [0] * 4

def start_cpu(i):
    while True:
        r = cpuQ.get()
        cpustat[i] = 1
        for b in range(r.blocks):
            #print("sleep",r.delay / 1000)
            time.sleep(r.delay / 1000)
            r.sem.release()
        cpuQ.task_done()
        cpustat[i] = 0

def stats():
    global serverid
    t = 0
    i = 0
    a = 0.995
    while True:
        time.sleep(0.001)
        n = float(np.sum(cpustat)) / len(cpustat)
        t = (a)*t + (1.0-a)*n
        if i == 99:
            i=0
#            print("CPU-%d-RESULT-t))
            data = []
            try:
                data.append('%d:%d' % (serverid, int(t * 100)))
                r = requests.post(url, data = ','.join(data), timeout=1)
            except Exception as e:
                print("Could not connect:", e)
                continue
        else:
            i = i + 1


class Handler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Connection", "close")
        self.end_headers()

        q = parse.urlsplit(self.path).query
        args = parse.parse_qs(q)
        fsize = 1024 #kb following 1.2 poisson
        delay = 10 #ms

        if "fsize" in args:
            fsize = float(args["fsize"][0])
        if "delay" in args:
            delay = float(args["delay"][0])

        blocks = fsize * 8
        if not fixed:
            blocks = ZipfGenerator(int(blocks), 1.1).next()
            if blocks == 0:
                blocks = 1

            delay = np.random.poisson(delay, 1)[0]
        else:
            blocks = int(blocks / 16) #Compensate non zipf


        start = time.monotonic()


        delay = delay / blocks
        r = Request(blocks, delay)
        cpuQ.put(r)
        done = 0
        while done < blocks:
            r.sem.acquire()
            self.wfile.write(content)
            done = done + 1
        return

    def log_message(self, format, *args):
        return

class BigServer(HTTPServer):
    def __init__(self, server_address, rhc=Handler):
        self.request_queue_size=16
        HTTPServer.__init__(self, server_address, rhc)


def repeat_to_length(string_to_expand, length):
    return (string_to_expand * (int(length/len(string_to_expand))+1))[:length]


class ThreadedHTTPServer(ThreadingMixIn, BigServer):
    """Handle requests in a separate thread."""


if __name__ == '__main__':
    global content,url,serverid,fixed
    parser = argparse.ArgumentParser(description='HTTP Server simulating processing time')
    parser.add_argument('content', metavar='string', type=str, nargs='?', default='ABCD1234',
                    help='Content of the served file')
    parser.add_argument("--lb", dest="lb", type=str, default="192.168.100.1")
    parser.add_argument("--id", dest="serverid", type=int, default=-1)
    parser.add_argument("--fixed", dest="fixed", action='store_true', default=False)
    args = parser.parse_args()
    serverid=args.serverid
    fixed=args.fixed
    url = "http://" + args.lb + "/cheetah/load"

    for i in range(4):
        _thread.start_new_thread( start_cpu, tuple([i]) )
    _thread.start_new_thread( stats, tuple() )

    content = bytes(repeat_to_length(args.content, 128),"ascii")
    server = ThreadedHTTPServer(('0.0.0.0', 80), Handler)
    print('Starting server, use <Ctrl-C> to stop')
    try:
        server.serve_forever()
    except BrokenPipeError:
        pass
