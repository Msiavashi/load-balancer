$init = <<SCRIPT
  apt update
  DEBIAN_FRONTEND=noninteractive apt install -y build-essential fakeroot debhelper autoconf automake libssl-dev graphviz python-all python-qt4 python-twisted-conch libtool git tmux vim python-pip python-paramiko python-sphinx graphviz autoconf automake bzip2 debhelper dh-autoreconf libssl-dev libtool openssl procps python-all python-qt4 python-twisted-conch python-zopeinterface module-assistant dkms make libc6-dev python-argparse uuid-runtime netbase kmod python-twisted-web iproute2 ipsec-tools openvswitch-switch libpcap-dev libnuma-dev libmicrohttpd-dev python3-pip python3-matplotlib htop wireshark-gtk python3 linux-tools-generic lynx gdb evince
  pip install alabaster
  python3 -m pip install --upgrade pip
SCRIPT

$ovs = <<SCRIPT
  wget https://www.openvswitch.org/releases/openvswitch-3.0.0.tar.gz
  tar xf openvswitch-3.0.0.tar.gz
  pushd openvswitch-3.0.0/
  DEB_BUILD_OPTIONS='parallel=8 nocheck' fakeroot debian/rules binary
  ./boot.sh
  ./configure
  ./configure --prefix=/usr --localstatedir=/var --sysconfdir=/etc
  popd
SCRIPT


$mininet = <<SCRIPT
  git clone https://github.com/mininet/mininet.git
  pushd mininet
  ./util/install.sh -fn
  popd
SCRIPT

$dpdk = <<SCRIPT
  wget http://fast.dpdk.org/rel/dpdk-19.11.1.tar.xz
  tar xf dpdk-19.11.1.tar.xz
  rm dpdk-19.11.1.tar.xz
  pushd dpdk-stable-19.11.1
  make config T=x86_64-native-linuxapp-gcc O=x86_64-native-linuxapp-gcc
  echo "export RTE_SDK=$(pwd)" >> ~/.profile
  echo "export RTE_TARGET=x86_64-native-linuxapp-gcc" >> ~/.profile
  cd x86_64-native-linuxapp-gcc
  make -j 4
  popd
SCRIPT

$huge = <<SCRIPT
  mkdir -p /mnt/huge
  (mount | grep hugetlbfs) > /dev/null || mount -t hugetlbfs nodev /mnt/huge
  echo "nodev /mnt/huge hugetlbfs       defaults        0 0" >> /etc/fstab
  echo 512 > /sys/devices/system/node/node0/hugepages/hugepages-2048kB/nr_hugepages
  echo "vm.nr_hugepages=512" >> /etc/sysctl.conf
SCRIPT

$cheetahfastclick = <<SCRIPT
  git clone https://github.com/cheetahlb/cheetah-fastclick.git
  pushd cheetah-fastclick
  source ~/.profile
  ./configure --enable-dpdk --enable-multithread --disable-linuxmodule --enable-intel-cpu --enable-user-multithread --verbose --enable-select=poll CFLAGS="-O3" CXXFLAGS="-std=c++11 -O3"  --disable-dynamic-linking --enable-poll --enable-bound-port-transfer --enable-local --enable-flow --enable-cheetah --disable-task-stats --enable-cpu-load
  make -j 4
  sudo make install
  sudo sysctl -w net.ipv4.tcp_timestamps=2
  echo "net.ipv4.tcp_timestamps=2" | sudo tee -a /etc/sysctl.conf
  popd
SCRIPT

$npf = <<SCRIPT
  git clone https://github.com/tbarbette/npf.git
  pushd npf
  python3 -m pip install --user --upgrade -r requirements.txt
  echo "addr=127.0.0.1" >> cluster/l.node
  echo "0:ip=127.0.0.1" >> cluster/l.node
  echo "" | ssh-keygen
  cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
  popd
SCRIPT

$wrk = <<SCRIPT
  git clone https://github.com/tbarbette/wrk2.git
  pushd wrk2
  ./configure
  make -j 3
  popd
SCRIPT

$deps = <<SCRIPT
  python3 -m pip install --user pandas
  mkdir ~/.vimhistory/
  echo 'set undofile' >> .vimrc
  echo 'set undodir=/home/vagrant/.vimhistory/' >> .vimrc
  echo 'filetype plugin indent on' >> .vimrc
  echo 'set smarttab' >> .vimrc
  echo 'set shiftwidth=4' >> .vimrc
  echo 'set autowrite' >> .vimrc
  sudo locale-gen en_GB.UTF-8
SCRIPT

$cleanup = <<SCRIPT
  apt clean
  rm -rf /tmp/*
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"

  config.vm.provider "virtualbox" do |v|
#      v.customize ["modifyvm", :id, "--memory", "2048"]
	v.cpus = 6
	v.memory = 4096
  end

  ## Provisioning
  config.vm.provision :shell, :inline => $init
  config.vm.provision :shell, privileged: false, :inline => $ovs
  config.vm.provision :shell, privileged: false, :inline => $mininet
  config.vm.provision :shell, privileged: false, :inline => $dpdk
  config.vm.provision :shell, :inline => $huge
  config.vm.provision :shell, privileged: false, :inline => $cheetahfastclick
  config.vm.provision :shell, privileged: false, :inline => $npf
  config.vm.provision :shell, privileged: false, :inline => $wrk
  config.vm.provision :shell, privileged: false, :inline => $deps
  config.vm.provision :shell, :inline => $cleanup
  
  config.ssh.forward_x11 = true
  
  config.vm.post_up_message = <<-HEREDOC
  Setup finished!
HEREDOC
 
end

