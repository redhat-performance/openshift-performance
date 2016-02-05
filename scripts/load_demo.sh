#!/bin/sh

cat << EOF > job_file
; -- start job file --
[global]
rw=write
size=4096m

[job1]
EOF


function load {
echo CPU:  Loading CPU for 5 seconds.
stress -q -t 10 -c 1
echo DISK:  Writing 4GB
fio job_file > /dev/null
echo NETWORK:  Sending TCP traffic
netperf -H 10.12.20.141 > /dev/null
echo MEMORY:  Allocating 4GB RAM
stress -q -t 10 --vm 1 --vm-bytes 4G
echo ---
}

while true
	do
		load
		echo 3 > /proc/sys/vm/drop_caches
done
