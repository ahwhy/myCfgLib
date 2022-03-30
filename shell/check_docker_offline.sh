#!/bin/bash

## release 20220119
## 1. dockerd only.
## 2. containerd only, without dockerd.
## 3. containerd wraped by dockerd.

OK=0
NONOK=1
UNKNOWN=2

# check docker offline

# check dockerd containerd service exist
systemctl list-units --type=service -a | grep -E -q 'docker|containerd'
if [ $? -ne 0 ]; then
    echo "node not install docker or containerd"
    exit ${UNKNOWN}
fi

# 1. docker runtime. docker.service.
# check docker.service loaded
systemctl status docker | grep -q 'Loaded: loaded'
if [ $? -eq 0 ]; then
    echo "node have loaded docker.service"
    # if no containerd, docker.service must active.
    if [[ `systemctl is-active docker`x == activex ]]; then
    # check docker.sock
    curl --connect-timeout 20 -m 20 --unix-socket /var/hostrun/docker.sock http://x/containers/json >/dev/null 2>&1
    if [[ $? -ne 0 ]]; then
        echo "docker ps check error"
        exit ${NONOK}
    fi
    else
    echo "node docker.service is loaded, but inactive."
    exit ${NONOK}
    fi
else
echo "node have no docker service loaded, maybe containerd."
# 2. containerd runtime.
# check containerd status
systemctl list-units --type=service -a | grep -q containerd
if [ $? -eq 0 ]; then
    echo "node have containerd service"
    CONTAINERD_STATUS=`systemctl is-active containerd`
    echo $CONTAINERD_STATUS
    if [[ "$CONTAINERD_STATUS"x != "activex" ]]; then
        echo "containerd ps check error"
        exit ${NONOK}
    fi
fi
fi
exit ${OK}
