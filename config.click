//Configuration
define( $verbose 0,             //Verbosity of Cheetah
	    $threads 1,             //Number of threads/cores to use
        $left 0,                //Index of the interface facing clients
        $leftip  100.0.0.1,    //IP of the left interface, it is also the VIP
        $rightip 10.0.0.1,    //IP of the right interface
        $right 1,         		//Index of the interface facing servers
        $mode "rr",      		//Load-balancing mode (rr is round robin)
	    $resettime 5,     		//Time to reset statistics counted on the LB
	    $leastmode "cpu", 		//Metric used for pow2, least loaded and AWRR
		$macleft 00:00:00:00:0a:01,
		$macright 00:00:00:00:0a:0b,
		$print 0, 
)

KernelFilter(drop dev lb1-eth0);
KernelFilter(drop dev lb1-eth1);

//Spawn an HTTP server to read and write handlers
HTTPServer()

fd0 :: FromDPDKDevice(  $left, VERBOSE 2, MAXTHREADS $threads, RSS_AGGREGATE true, PREFETCH_SECOND 1,
                        SCALE parallel
                         )
    -> Print(LEFT,-1,ACTIVE $print)
    -> c :: Classifier(
        12/0806 20/0001, //ARP request
        12/0806 20/0002, //ARP replies
        12/0800,         //IP packets
        -);

c[2]
    -> Strip(14)
    -> CheckIPHeader(CHECKSUM false)
    //Filter non-TCP traffic
    -> tcl ::  IPClassifier(tcp, -)

/*    -> [0] cheetah :: CheetahStateless(VIP $leftip,
			DST 10.221.0.5, DST 10.221.0.6, DST 10.221.0.7, DST 10.221.0.8,
			BUCKETS 256, FIX_TS_ECR true, SET_TS_VAL true, FIX_IP true,
			LB_MODE $mode, RESET_TIME $resettime, FORCE_TRACK_LOAD true,
			LST_MODE $leastmode, VERBOSE $verbose)[0]*/
			
	-> FlowIPManagerIMP
    -> cheetah :: FlowIPLoadBalancer(VIP $leftip,
                        DST 10.0.0.40, DST 10.0.0.41, DST 10.0.0.42, DST 10.0.0.43,
                        LB_MODE $mode, LST_MODE $leastmode, FORCE_TRACK_LOAD true)

    //One could use ResetIPChecksum, here we fix it in software (just for fun)
    -> SetIPChecksum
    -> SetTCPChecksum
    -> arpright :: ARPQuerier(IP $rightip, ETH $macright)
    -> td1 :: ToDPDKDevice($right, TCO false); //no TCO as we fix checksums in software

tcl[1] -> Print("NOT TCP") -> Discard;

arprespleft :: ARPResponder($leftip $macleft)

c[0] -> arprespleft;

c[3] -> Print("Unknown packet type") -> Discard;


fd1 :: FromDPDKDevice($right, VERBOSE 2, MAXTHREADS $threads,
                      RSS_AGGREGATE true, PREFETCH_SECOND 1,
                      SCALE parallel)
    -> Print(RIGHT,-1, ACTIVE $print)
    -> cr :: Classifier(
        12/0806 20/0001,
        12/0806 20/0002,
        12/0800,
        -);
cr[2]
    -> Strip(14)
    -> CheckIPHeader(CHECKSUM false)
    -> tcr ::  IPClassifier(tcp, -)
    //-> [1]cheetah[1]
	-> FlowIPLoadBalancerReverse(cheetah) 
    -> SetIPChecksum
    -> SetTCPChecksum
    -> arpleft :: ARPQuerier(IP $leftip, ETH $macleft)
    -> td0 :: ToDPDKDevice($left, TCO false);

arprespright :: ARPResponder($rightip $macright);

cr[0] -> arprespright;


cr[3] -> Print("Unknown packet type") -> Discard;

arprespleft[0] -> td0;
arprespright[0] -> td1;

c[1] -> [1]arpleft;
cr[1] -> [1]arpright;

tcr[1] -> Print("NOT TCP") -> Discard;

Script(TYPE ACTIVE,
       label g,
       set t $(now),
       print "SRVLOAD-$t-RESULT-SRV1 $(cheetah.load 0)",
       print "SRVLOAD-$t-RESULT-SRV2 $(cheetah.load 1)",
       print "SRVLOAD-$t-RESULT-SRV3 $(cheetah.load 2)",
       print "SRVLOAD-$t-RESULT-SRV4 $(cheetah.load 3)",
       wait 0.1s,
       goto g
)
