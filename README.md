# openshift-performance
OpenShift, Kubernetes and Docker Performance Research

# DevConf 2016 VM
* Download OVA file (or copy from USB disk)
* Install VirtualBox and kernel-devel RPM that matches your running kernel
* systemctl restart system-modules-load or Reboot to load kernel modules
* Start VirtualBox
** Go to File -> Import Appliance -> Select the OVA file
** Click the checkbox to reset the MAC address
** Click Import
** Start the VM
** Username:  devconf2016 Password:  devconf2016
** User devconf2016 has sudo access

------------

The next few steps should be baked in to the VM image, but for posterity here's what is included:

```
cd $HOME
git clone https://github.com/jeremyeder/openshift-performance
wget https://github.com/openshift/origin/releases/download/v1.1.1.1/openshift-origin-server-v1.1.1.1-940be51-linux-64bit.tar.gz
tar xf https://github.com/openshift/origin/releases/download/v1.1.1.1/openshift-origin-server-v1.1.1.1-940be51-linux-64bit.tar.gz
sudo ln -s ~/openshift-origin-server-v1.1.1.1-940be51-linux-64bit/openshift /usr/bin
sudo ln -s ~/openshift-origin-server-v1.1.1.1-940be51-linux-64bit/oc /usr/bin
cd openshift-origin-server-v1.1.1.1-940be51-linux-64bit
sudo openshift start master
sudo openshift start node --kubeconfig ~/openshift-origin-server-v1.1.1.1-940be51-linux-64bit/openshift.local.config/master/openshift-master.kubeconfig
cp openshift-origin-server-v1.1.1.1-940be51-linux-64bit/openshift.local.config/master/admin.kubeconfig ~/.kube/config
sudo docker pull openshift/origin-pod
sudo docker pull openshift/origin-deployer
sudo docker pull openshift/origin-docker-builder
sudo docker pull openshift/origin-docker-registry
setenforce 0
```

------------

Verify OpenShift is up and running:

```
openshift version
oc get nodes
```

Create a test pod:
```
oc create -f ~/openshift-performance/svt/content/pod-default.json
oc get pods
```

------------

In this repo there is a dockerfile for an openshift-performance container.  You can docker build this, or:
docker pull jeremyeder/openshift-performance

The openshift-performance container is:

* CentOS 7
* OpenShift Origin
* Pbench
* A copy of this repo
* A LABEL that starts it as a super privileged container [1]
