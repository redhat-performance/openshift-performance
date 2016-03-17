#!/bin/sh

pbench-stop-tools
pbench-kill-tools
pbench-clear-tools

# Intended to run on the master and list nodes here:
#NODES="dell-r730-01.perf.lab.eng.rdu.redhat.com dell-r730-02.perf.lab.eng.rdu.redhat.com"
NODES=""

pbench-register-tool-set --interval=10
pbench-register-tool --name=oc
pbench-register-tool --name=pprof -- --profile=cpu --osecomponent=master

# setup pbench on nodes
for NODE in $NODES
  do
    pbench-register-tool-set --remote=$NODE --interval=10
    pbench-register-tool --name=pprof --remote=$NODE -- --profile=cpu --osecomponent=node
done

pbench-list-tools
