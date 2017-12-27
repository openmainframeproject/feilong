#!/bin/sh

#---------------------------------------------------------------------------------------------
# This script takes four arguments:
# 1. The prefix for the instances you boot. For example, scaletest_0606
# 2. The thread number you want to use. The same number will be used for both boot and delete
# 3. The number of VMs create per thread.
#    For example, if you want to create 500 VMs, and you use 5 thread, you should specify 100
# 4. The number of VMs delete per thread. Same as above, but this number has be to less than
#    the create number for obvious reason.
#
# Note: There are also a few hard codeded values you need to change in the script before start.
# 1. The line: boot_command="   "
#    change to the boot command you would use except skip the vm name
# 2. The time to wait between each create in a thread is set to 120 seconds
#    The time to wait between each delete in a thread is set to 60 seconds
#    Change the above to a value that is appropriate for your system.
# 3. The time to wait before delete kicks in is set to 5 minutes.
#    You definitely want to change this if you have a large number of create/delete,
#    since delete is faster than create, it will soon catch up and have nothing to delete
#    For a scale to 500 run, you might want to wait for a couple hours before delete start
#---------------------------------------------------------------------------------------------


if [ $# -lt 3 ]
then
    echo "Invalid Argument Count"
    echo "Syntax: $0 thread_number create_number delete_number"
    exit
fi

#kill the process and all its children
echo $$
trap 'echo "ctrl-c detected"; kill -9 -$$' SIGINT SIGTERM

vm_name_prefix="SC"
create_thread=$1
create_number=$2
delete_number=$3

boot_sleep=1
delete_sleep=1
interval_sleep=1

# Change this manually before run the script


# As we only have 8 chars for vm name, this test expect to run < 100 threads
# and < 1000 instances
# so the name will be SCTyzzzz
# SC is prefix for scale test
# T is prefix, y is thread number
# zzzz is the instance to be created

function start_create() {
    echo "starting create"

    for (( i=1; i<=$create_thread; i++ ))
    do
        create_thread &
        sleep 1
    done
}

function create_thread() {
    for (( j=1; j<=$create_number; j++ ))
    do
        var=$(printf '%sT%x%04x' $vm_name_prefix $i $j) 
        echo "create $var"
        # $boot_command$vm_name_prefix-thread$i-vm$j
        # echo "in create_thread $i, sleeping $boot_sleep"
        sleep $boot_sleep
    done
}

function start_delete() {
    echo "starting delete"

    for (( k=1; k<=$create_thread; k++))
    do
        delete_thread &
        sleep 1
    done
}


function delete_thread() {
    for (( l=1; l<=$delete_number; l++ ))
    do
        var=$(printf '%sT%x%04x' $vm_name_prefix $k $l)
        echo "delete $var"
        # nova delete $vm_name_prefix-thread$k-vm$l
        # echo "in delete_thread $k, sleeping $delete_sleep"
        sleep $delete_sleep
    done
}

start_create

# change this to an appropriate time to wait until we have enough vm to delete
echo "sleep for $interval_sleep seconds to create enough vm to be deleted"
sleep $interval_sleep
start_delete




