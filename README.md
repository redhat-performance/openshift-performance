# OpenShift, Kubernetes and Docker: Performance, Scalability and Capacity Planning Research by Red Hat

This repository and accompanying slides detail the approach, process and procedures used by the performance engineering team at Red Hat to analyze and improve performance of integrated platform and infrastructure stacks.  It shares results, best practices and reference architectures for the Kubernetes and Docker-based OpenShift v3 Platform-as-a-Service, as well as the Red Hat Atomic Enterprise Platform  (AEP).

In addition to the slide materials, hands-on demos have been created along with a Fedora-based VM image.  Unfortunately that VM image is too large to host, so I've included instructions on how to rebuild it given a clean Fedora Installation.

Unsurprisingly, performance analysis and tuning in the container and container-orchestration space has tremendous overlap with previous generation approaches to distributed computing.  Performance still boils down to identifying and resolving bottlenecks, data- and compute-locality, and applying best-practices to software scale-out design hard-won over decades of grid- and high-performance computing research.

Several slides discuss non-determinism in public cloud computing infrastructure.  Variances caused by the nature of hardware and software design are also observed when running on bare metal or private cloud.  However, those variances tend to be larger in public cloud because of over-subscription of physical resources, the "noisy-neighbor" problem and WAN latencies etc.  Public cloud providers offer solutions such as "dedicated hypervisors", direct connections to their facilities and control over idle- and frequency (C- and P-) states, high-speed LAN connections, SR-IOV, and bandwidth/IOP SLAs on storage.

Here are the instructions to setup the workshop virtual machine, using VirtualBox.  You can also untar the ova file and use qemu-img to convert the vmdk to a qcow2 image for use with KVM and virt-manager.

```
qemu-img convert -O qcow2 devconf2016_v2-disk1.vmdk devconf2016_v2.qcow2
```

# DevConf 2016 VM
* Copy OVA file devconf2016_v2.ova from USB disk, this takes about 12 minutes.
* USB disk also contains VirtualBox packages for Fedora, Apple, Ubuntu, Debian...
* Or use rpmfusion:
* dnf install http://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-23.noarch.rpm
* dnf install kernel-devel VirtualBox
* lsmod|grep vbox
* systemctl restart system-modules-load or Reboot to load kernel modules
* Start VirtualBox
* Go to File -> Import Appliance -> Select the OVA file
* Click the checkbox to reset the MAC address
* Click Import
* Start the VM
* Username:  devconf2016 Password:  devconf2016
* User devconf2016 has sudo access

------------

## The next few steps should be baked in to the VM image, but for posterity here's what is included:

```
sudo su -
cd $HOME
cp -Rp /home/devconf2016/openshift-performance ~
# git clone https://github.com/jeremyeder/openshift-performance
# wget https://github.com/openshift/origin/releases/download/v1.1.1.1/openshift-origin-server-v1.1.1.1-940be51-linux-64bit.tar.gz
# tar xf https://github.com/openshift/origin/releases/download/v1.1.1.1/openshift-origin-server-v1.1.1.1-940be51-linux-64bit.tar.gz
sudo ln -s ~/openshift-origin-server-v1.1.1.1-940be51-linux-64bit/openshift /usr/bin
sudo ln -s ~/openshift-origin-server-v1.1.1.1-940be51-linux-64bit/oc /usr/bin
cd openshift-origin-server-v1.1.1.1-940be51-linux-64bit
systemctl stop avahi-daemon
killall dnsmasq
openshift start master
openshift start node --kubeconfig ~/openshift-origin-server-v1.1.1.1-940be51-linux-64bit/openshift.local.config/master/openshift-master.kubeconfig
mkdir ~/.kube
cp ~/openshift-origin-server-v1.1.1.1-940be51-linux-64bit/openshift.local.config/master/admin.kubeconfig ~/.kube/config
# docker pull openshift/origin-pod:v1.1.1.1
# docker pull openshift/origin-deployer:v1.1.1.1
# docker pull openshift/origin-docker-builder:v1.1.1.1
# docker pull openshift/origin-docker-registry:v1.1.1.1
# docker pull openshift/hello-openshift:v1.0.6
```

------------


## Examine docker configuration
On Red Hat-based distributions, docker is run under systemd, which is tied back to /etc/sysconfig environment files.
/etc/sysconfig/docker controls daemon options such as SELinux and registries.
/etc/sysconfig/docker-storage controls the docker graph driver setup, including which graph driver to use (devicemapper, overlay etc) as well as which storage devices to use.
/etc/sysconfig/docker-storage-setup does not exist by default, but a sample is included with the docker RPM and is used by the docker-storage-setup script to configure thin-provisioned LVM-based block storage for your containers and images. See /usr/lib/docker-storage-setup/docker-storage-setup or man docker-storage-setup for more info.

```
docker version
docker info
ls -alZ /var/lib/docker
ls -alRZ /run/docker
docker ps
docker ps -a
docker images
# docker tag jeremyeder/openshift-performance osperf
```



## Run your first container
```
docker run -d --name osperf osperf sleep infinity
docker ps
```

## Docker inspect, exec, stats and top

```
docker inspect osperf
docker exec -it osperf bash
# openshift-performance/scripts/load_test.sh
docker stats osperf
docker top osperf -o pid,psr,pcpu,nice,cmd
```


## Verify OpenShift is up and running:

```
openshift version
oc get nodes
oc describe node localhost.localdomain
```

## Create a test pod:

```
cd ~/openshift-performance/svt/content
cat pod-default.json
oc create -f pod-default.json
oc get pods -w
oc get events
oc delete pod hello-openshift
```

## Create a replication controller:
```
cd ~/openshift-performance/svt/content
cat rc-default.json
oc create -f rc-default.json
oc get rc
oc describe rc rc/frontend-1
oc get nodes -o wide
```

## Scale out a replication controller.
```
oc get pods -w
oc scale replicationcontroller --replicas=2 rc/frontend-1
oc scale replicationcontroller --replicas=10 rc/frontend-1
oc describe rc rc/frontend-1
```






------------

In this repo there is a dockerfile for an openshift-performance container.  You can docker build this, or:
docker pull jeremyeder/openshift-performance

The openshift-performance container is:

* CentOS 7
* OpenShift Origin
* Pbench
* A copy of this repo
* A LABEL that starts it as a super privileged container
