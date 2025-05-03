
```bash
docker tag airflow-uv:latest jrpenagu/airflow-uv-ml:latest
docker push jrpenagu/airflow-uv-ml:latest 
```

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: project-3-mlops
```

To create or update resources defined in a YAML file:
```bash
kubectl apply -f project-namespace.yaml
```

- `apply` is declarative: it compares the YAML to the current cluster state and updates only what's different.
- `-f` stands for "filename": This tells kubectl to read the resource definition from a file.

```text
namespace/project-3-mlops created
```