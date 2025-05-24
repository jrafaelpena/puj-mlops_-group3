```
.
├── apps/                              # Application source code (no manifests here)
│   ├── inference-api/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── ...
│   ├── streamlit/
│   │   ├── streamlit_app.py
│   │   └── ...
│   └── locust/
│       └── ...
│
├── k8s/                               # All Kubernetes manifests (GitOps-compatible)
│   ├── base/                          # Cluster-wide resources
│   │   ├── namespace.yaml
│   │   └── project-kustomization.yaml (if needed for initial bootstrap)
│
│   ├── airflow/                       # Special case: deployed via Helm
│   │   ├── helm-release.yaml         # Argo CD HelmRelease or Helm values.yaml
│   │   └── values.yaml
│
│   ├── inference-api/                # Each folder contains manifests per app
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   └── kustomization.yaml
│
│   ├── streamlit/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── kustomization.yaml
│
│   ├── observability/
│   │   ├── prometheus/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── servicemonitor.yaml
│   │   ├── grafana/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── dashboards/
│   │   └── kustomization.yaml
│
│   ├── storage/
│   │   ├── postgres-pvc.yaml
│   │   ├── minio-pvc.yaml
│   │   └── kustomization.yaml
│
│   ├── databases/
│   │   ├── postgres/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── configmap.yaml
│   │   ├── mysql/
│   │   │   └── ...
│   │   └── kustomization.yaml
│
│   └── project-kustomization.yaml    # Top-level aggregator for Argo CD apps
│
├── manifests/                        # Optional: shared templates or base YAMLs
│   └── (Not used by Argo CD directly)
│
├── charts/                           # Optional: Helm charts (Airflow)
│   └── airflow/ (or use upstream chart via repo)
│
├── images/                           # Architecture diagrams and documentation
│   └── *.png
│
├── .argocd-apps/                     # Argo CD Application YAMLs (App of Apps)
│   ├── inference-api-app.yaml
│   ├── streamlit-app.yaml
│   ├── airflow-app.yaml
│   └── apps-of-apps.yaml             # Optional: manage all from a single file
│
├── README.md
└── Makefile / deploy.sh              # Optional: for local testing, linting
```