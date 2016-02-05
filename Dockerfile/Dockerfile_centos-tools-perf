FROM centos/tools
MAINTAINER jeder <jeder@redhat.com>

# Setup pbench repo
RUN curl -o /etc/yum.repos.d/pbench.repo https://raw.githubusercontent.com/jeremyeder/openshift-performance/master/repos/pbench.repo

# Install pbench
RUN yum --enablerepo=pbench --enablerepo=pbench-test install -y pbench-agent ; yum clean all

# Clone openshift-performance repo
RUN git clone http://github.com/jeremyeder/openshift-performance
