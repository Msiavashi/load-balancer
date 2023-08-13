#!/usr/bin/python
#This is a python (Mininet) script that will generate a topology and run Cheetah
#Run me with "sudo python topology.py", after having installed mininet and fastclick. The best is
#to use the VM built using Vagrant available at []

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI

import sys
import time

class MyTopo(Topo):


    "Single switch connected to n hosts."
    def build(self, n=2):

        self.client = self.addHost('h1', ip="100.0.0.10")
        self.sw1 = self.addSwitch('sw1')
        self.addLink(self.client, self.sw1)

        self.lb1 = self.addHost('lb1')
        self.addLink(self.lb1, self.sw1, params1={'ip':"100.0.0.1/24"},addr1="00:00:00:00:0a:01")
        self.sw2 = self.addSwitch('sw2')
        self.addLink(self.lb1, self.sw2, params1={'ip':"10.0.0.1/24" },addr1="00:00:00:00:0b:01")

        #Control switch
        self.swc = self.addSwitch('swc1')
        self.addLink(self.lb1, self.swc, params1={'ip':"192.168.100.1/24"})

        #Add servers
        self.servers = []
        for h in range(n):
            host = self.addHost('ws%s' % (h + 1), ip="10.0.0.%s" % (40+h),  defaultRoute = "via 10.0.0.1")
            self.addLink(host, self.sw2)
            self.addLink(host, self.swc, params1={'ip':"192.168.100.%s/24" % (40+h) })
            self.servers.append(host)

    def buildConfig(self, net):
        s = open('config.click','r').read()

        dsts = ""
        for srv in self.servers:
            msrv = net.getNodeByName(srv)
            dsts = dsts + "DST " + msrv.intfList()[0].ip + ", "
        s = s.replace("DST 10.221.0.5, DST 10.221.0.6, DST 10.221.0.7, DST 10.221.0.8,", dsts)
        return s

def simpleTest():
    "Create and test a simple network"
    topo = MyTopo(n=4)
    net = Mininet(topo)
    net.start()
    print "Dumping host connections"
    dumpNodeConnections(net.hosts)

    config = topo.buildConfig(net)
    f = open('/home/vagrant/cheetah-fastclick/tmp.config.click','wb')
    f.write(config)
    f.close()
    #print("Launching Cheetah with config:")
    #print(config)
    lb = net.get(topo.lb1)
    for i in lb.intfList():
        lb.cmd( 'ethtool -K %s gro off' % i )
    cmd = "cd /home/vagrant/cheetah-fastclick && ./bin/click --dpdk -l 1-1 --vdev=eth_af_packet0,iface=" +lb.intfList()[0].name + " --vdev=eth_af_packet1,iface=" + lb.intfList()[1].name  + " -- tmp.config.click &> click.log &"
    print("Launching Cheetah with " + cmd)
    lb.cmd(cmd)


    print("Waiting for LB to set up...")
    time.sleep(3)
    for i,srv in enumerate(topo.servers):
        msrv = net.getNodeByName(srv)
        cpu = str(i + 2)
        cmd = "cd /vagrant/ && taskset -c "+cpu+"-"+cpu+" python3 httpserver.py "+srv+" --id "+str(i)+" "+ (sys.argv[1] if len(sys.argv) > 1 else "") +" &"
        print(cmd)
        msrv.cmd(cmd)

    client = net.get("h1")
    print("Waiting for everything to set up...")
    time.sleep(2)
    print("Verifying round-robin mode")
    for i,srv in enumerate(topo.servers * 2):
        client.sendCmd("wget -o /dev/null -O /dev/stdout http://100.0.0.1/?fsize=1")
        result = client.waitOutput()
        if srv in result:
            print("Query %d got to server %s" % (i, srv))
        else:
            print("Query %d did NOT go to server %s" % (i, srv))

    CLI(net)
    net.stop()

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    simpleTest()
