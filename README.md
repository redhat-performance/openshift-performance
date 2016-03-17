# OpenShift, Kubernetes and Docker: Performance, Scalability and Capacity Planning Research by Red Hat

[OpenShift v3 Scaling, Performance and Capacity Planning Whitepaper](https://access.redhat.com/articles/2191731 "OpenShift v3 Scaling, Performance and Capacity Planning Whitepaper")

This repository and accompanying slides detail the approach, process and procedures used by the performance engineering team at Red Hat to analyze and improve performance of integrated platform and infrastructure stacks.  It shares results, best practices and reference architectures for the Kubernetes and Docker-based OpenShift v3 Platform-as-a-Service, as well as the Red Hat Atomic Enterprise Platform  (AEP).

In addition to the slide materials, hands-on demos have been created along with a Fedora-based VM image.  Unfortunately that VM image is too large to host, so I've included instructions on how to rebuild it given a clean Fedora Installation.

Unsurprisingly, performance analysis and tuning in the container and container-orchestration space has tremendous overlap with previous generation approaches to distributed computing.  Performance still boils down to identifying and resolving bottlenecks, data- and compute-locality, and applying best-practices to software scale-out design hard-won over decades of grid- and high-performance computing research.

Several slides discuss non-determinism in public cloud computing infrastructure.  Variances caused by the nature of hardware and software design are also observed when running on bare metal or private cloud.  However, those variances tend to be larger in public cloud because of over-subscription of physical resources, the "noisy-neighbor" problem and WAN latencies etc.  Public cloud providers offer solutions such as "dedicated hypervisors", direct connections to their facilities and control over idle- and frequency (C- and P-) states, high-speed LAN connections, SR-IOV, and bandwidth/IOP SLAs on storage.

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
docker tag jeremyeder/openshift-performance osperf
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
