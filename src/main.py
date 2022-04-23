'''Module that reads labels from the node and transfers it to the pod'''
import logging
import re
from os import getenv
from copy import deepcopy
from jsonpatch import JsonPatch

from kubernetes import client, watch
from kubernetes.client.rest import ApiException

import setup


def transfer_labels_from_node_to_pod(pod):
    ''' Update pod with node labels '''
    node = KUBE_API.read_node(pod.spec.node_name)
    original = {
        'metadata': {
            'labels': pod.metadata.labels
        }
    }
    modified = deepcopy(original)
    for label in LABELS:
        logging.debug("Processing label %s...", label)
        modified['metadata']['labels'][label] = node.metadata.labels[label]
    patch = list(JsonPatch.from_diff(original, modified))

    if len(patch) > 0:
        try:
            KUBE_API.patch_namespaced_pod(
                pod.metadata.name, pod.metadata.namespace, patch)
            logging.info(
                "Labels were transfered from node %s to pod %s/%s",
                pod.spec.node_name, pod.metadata.namespace, pod.metadata.name)
        except ApiException as _api_exception:
            logging.error(_api_exception)
            return

    else:
        logging.debug("Nothing to update for pod %s/%s",
                      pod.metadata.namespace, pod.metadata.name)


def process_event(event):
    ''' Detects kubernetes events for scheduled pods and process the label patch '''
    if event.reason == 'Scheduled':
        result = re.search(
            r"^Successfully assigned (.*)\/(.*) to (.*)$", event.message)
        namespace = result.group(1)
        pod_name = result.group(2)

        if namespace not in EXCLUDED_NAMESPACES:
            logging.info("Processing: %s", event.message)
            try:
                pod = KUBE_API.read_namespaced_pod(pod_name, namespace)
            except ApiException as exception:
                logging.error('Pod %s/%s %s', namespace,
                              pod_name, exception.reason)
                return

            # Process pod
            transfer_labels_from_node_to_pod(pod)


KUBE_API = client.CoreV1Api()
KUBE_WATCH = watch.Watch()
LABELS = getenv("LABELS", "").split(",")
EXCLUDED_NAMESPACES = getenv("EXCLUDED_NAMESPACES", "").split(",")
SLEEP_DURATION = int(getenv("SLEEP", "10"))


# initial processing of all pods
logging.info("---- initial processing of pods ----")
pod_list = KUBE_API.list_pod_for_all_namespaces()
for pod in pod_list.items:
    # Process pod
    if pod.metadata.namespace not in EXCLUDED_NAMESPACES:
        transfer_labels_from_node_to_pod(pod)

while True:
    # initial processing of all events
    logging.info("---- initial processing of events ----")
    event_list = KUBE_API.list_event_for_all_namespaces()
    for event in event_list.items:
        process_event(event)

    # watch for new events
    logging.info("---- watching events with resource version: %s ----",
                 event_list.metadata.resource_version)
    while True:
        try:
            # It will listen for new events for timeout_seconds
            # and then it will resume execution
            for event in KUBE_WATCH.stream(KUBE_API.list_event_for_all_namespaces,
                                           timeout_seconds=120,
                                           resource_version=event_list.metadata.resource_version):
                event = event['object']
                process_event(event)

        except ApiException as api_exception:
            # Eventually the resource version will become outdated
            # and an ApiException will be raised with a 410 HTTP code
            logging.error("%s %s", api_exception.status,
                          api_exception.reason)
            break
