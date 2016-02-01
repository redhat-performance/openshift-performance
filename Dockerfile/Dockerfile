FROM openshift/origin
MAINTAINER jeder <jeder@redhat.com>

# Setup pbench repo
RUN curl -o /etc/yum.repos.d/pbench.repo http://github.com/jeremyeder/openshift-performance/repos/pbench.repo

# Install pbench
RUN yum install -y git pbench-agent ; yum clean all

# Clone openshift-performance repo
RUN git clone http://github.com/jeremyeder/openshift-performance /root/openshift-performance

# Set a label for use with the "atomic" command
LABEL RUN="docker run -d --name origin \
        --privileged --pid=host --net=host \
        -v /:/rootfs:ro -v /var/run:/var/run:rw -v /sys:/sys -v /var/lib/docker:/var/lib/docker:rw \
        -v /var/lib/origin/openshift.local.volumes:/var/lib/origin/openshift.local.volumes \
        openshift/origin start"
