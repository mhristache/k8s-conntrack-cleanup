#!/usr/bin/python

import subprocess
import os
from kubernetes import client, config, watch
from threading import Thread


def get_pod_ips(namespace):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    try:
        pods = v1.list_namespaced_pod(namespace, watch=False)
        return [x.status.pod_ip for x in pods.items]
    except BaseException as e:
        print("Error getting the pods for namespace {0}: {1}"
              .format(namespace, e))


def run(namespace):
    """Monitor kubernetes pod events and cleanup conntrack table
    when a pod is removed"""
    config.load_kube_config()
    v1 = client.CoreV1Api()
    w = watch.Watch()

    # cache  the pod IPs as the delete event might not include the pod ip
    pod_ips = {}

    for event in w.stream(v1.list_namespaced_pod, namespace=namespace):
        pod_ip = event['object'].status.pod_ip
        pod_name = event['object'].metadata.name
        print("Event:\t{}\t{}\t{}".format(event['type'], pod_name, pod_ip))
        if pod_ip:
            pod_ips[pod_name] = pod_ip

        if event['type'] == 'DELETED':
            ip = pod_ip or pod_ips.get(pod_name)
            pod_ips.pop(pod_name, None)
            if ip:
                print('Action:\ttriggering conntrack cleanup for {}'
                      .format(pod_ip))
                cleanup_conntrack(pod_ip)
            else:
                print("Error:\tpod ip not present, cannot cleanup!")


def cleanup_conntrack(pod_ip):
    cmd_params = ['--reply-src', '--reply-dst', '--dst', '--src']
    for param in cmd_params:
        cmd = "/usr/sbin/conntrack -D {} {}".format(param, pod_ip)
        t = Thread(target=run_cmd, args=(cmd, ))
        t.start()


def run_cmd(cmd):
    with open(os.devnull, 'w') as DEVNULL:
        try:
            subprocess.check_output(cmd, stderr=DEVNULL, shell=True)
        except subprocess.CalledProcessError as e:
            # conntrack returns 1 if there was no entry in the table
            # matching the request, which is not an error
            if e.returncode != 1:
                print("Err:\t{}".format(e.output.strip()))
            else:
                print("Info:\tcmd '{}' returned code 1 (which is probably ok)"
                      .format(cmd))
        else:
            print("Info:\tcmd '{}' was executed successfully".format(cmd))


if __name__ == "__main__":
    run('epg')
