#!/bin/sh

stop-tools
kill-tools
clear-tools

NODES="localhost"

register-tool-set
register-tool --name=oc
register-tool --name=pprof -- --profile=cpu --osecomponent=master

# setup pbench on nodes
for NODE in $NODES
  do
    register-tool-set --remote=$NODE
    register-tool --name=pprof --remote=$NODE -- --profile=cpu --osecomponent=node
done

list-tools
