# Node to pod labeler

This container will monitor pods in the system and based on an environment variable `LABELS` containing node labels separaded by comma, it will read the labels from the node and will copy them to te pod.

## Environment Variables

- `LABELS`: "eks.amazonaws.com/capacityType,node.kubernetes.io/instance-type" (default: "")
- `EXCLUDED_NAMESPACES`: "kube-system,prometheus,etc" (default "")
- `LOG_LEVEL`: "DEBUG" (default: "INFO")

# Motivation

The inspiration for this was to develop a cost report that could work toghether with the container in the project https://github.com/empathyco/kubernetes-cost-report.
[empathyco-container](https://github.com/empathyco/kubernetes-cost-report) would extract price per instance type, and later a prometheus rule would join metrics using node.kubernetes.io/instance-type and eks.amazonaws.com/capacityType.
