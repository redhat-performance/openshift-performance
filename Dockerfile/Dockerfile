FROM openshift/origin
MAINTAINER jeder <jeder@redhat.com>

# Setup pbench repo
RUN curl -o /etc/yum.repos.d/pbench.repo http://github.com/jeremyeder/openshift-performance/repos/pbench.repo

# Install pbench
RUN yum install -y git pbench-agent ; yum clean all

# Clone openshift-performance repo
RUN git clone http://github.com/jeremyeder/openshift-performance /root/openshift-performance
