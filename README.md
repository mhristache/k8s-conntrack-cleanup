# k8s-conntrack-cleanup

The `k8s_conntrack_cleanup.py` is providing a workaround for https://github.com/kubernetes/kubernetes/issues/59368.

## Install dependencies

```bash
pip install -r requirements.txt
```

## Run

```bash
./k8s_conntrack_cleanup.py -n <namespace>
```
