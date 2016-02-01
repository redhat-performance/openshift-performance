# openshift-performance
OpenShift, Kubernetes and Docker Performance Research

# To get a test environment up and running using a single Docker container:
* https://docs.openshift.org/latest/getting_started/administrators.html#running-in-a-docker-container

```
$ sudo docker run -d --name "origin" \
        --privileged --pid=host --net=host \
        -v /:/rootfs:ro -v /var/run:/var/run:rw -v /sys:/sys -v /var/lib/docker:/var/lib/docker:rw \
        -v /var/lib/origin/openshift.local.volumes:/var/lib/origin/openshift.local.volumes \
        openshift/origin start
```

```
$ sudo docker exec -it origin bash
```


