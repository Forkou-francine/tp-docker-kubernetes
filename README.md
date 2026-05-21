# TP Docker & Kubernetes

**Auteur :** Ange PENE FORKOU

---

## Objectif

Containeriser une application web minimaliste (Python / Flask), puis la déployer
sur un cluster Kubernetes local (Minikube) en couvrant :

| Partie | Sujet                                  | Points |
| ------ | -------------------------------------- | :----: |
| 1      | Docker (Dockerfile, build, run)        |   5    |
| 2      | Ressources Kubernetes (Pod, Deployment, Services) | 9 |
| 3      | Configuration & stockage (CM, Secret, PVC) |  4   |
| —      | Livrables (YAML, README, capture)      |   2    |

---

## Arborescence du repo

```
tp-docker-kubernetes/
├── README.md
├── app/
│   ├── app.py              # application Flask "Hello World"
│   ├── requirements.txt
│   └── Dockerfile
└── k8s/
    ├── 01-pod.yaml
    ├── 02-deployment.yaml
    ├── 03-service-clusterip.yaml
    ├── 04-service-nodeport.yaml
    ├── 05-configmap.yaml
    ├── 06-secret.yaml
    ├── 07-pvc.yaml
    └── 08-pod-with-config.yaml
```

---

## Prérequis

- Docker Desktop (ou Docker Engine)
- `kubectl`
- Minikube (testé en v1.33+)
- `curl`

```bash
winget install Kubernetes.minikube
minikube start
minikube status
kubectl version --short
```

---

## Partie 1 - Docker

### Build et run

```bash
cd app/

# Build avec un tag propre (nom:version)
docker build -t hello-app:1.0.0 .

# Vérification de la présence de l'image
docker images | grep hello-app

# Lancement d'un conteneur (port hôte 8080 → port conteneur 5000)
docker run -d --name hello-app-container -p 8080:5000 hello-app:1.0.0

# Vérification
docker ps
curl http://localhost:8080/
curl http://localhost:8080/healthz
docker logs hello-app-container
```

### Résultat attendu

```json
{
  "env": "docker",
  "hostname": "<container-id>",
  "message": "Hello World",
  "secret_ok": false,
  "user": "anonymous"
}
```

### Nettoyage

```bash
docker stop hello-app-container && docker rm hello-app-container
```

---

## Partie 2 - Ressources Kubernetes

### Charger l'image locale dans Minikube

> Minikube tourne dans sa propre VM/conteneur : il ne voit pas les images
> Docker de l'hôte. Il faut donc les y charger explicitement.

```bash
minikube image load hello-app:1.0.0
```

### Déploiement du Pod simple

```bash
kubectl apply -f k8s/01-pod.yaml
kubectl get pods -o wide
kubectl describe pod hello-pod
```

### Deployment (2 réplicas)

```bash
kubectl apply -f k8s/02-deployment.yaml
kubectl get deployments
kubectl get rs
kubectl get pods -l app=hello -o wide
```

### Scaling manuel (2 → 3 réplicas)

```bash
kubectl scale deployment hello-deployment --replicas=3
kubectl get pods -l app=hello -w
```

### Service ClusterIP (interne)

```bash
kubectl apply -f k8s/03-service-clusterip.yaml
kubectl get svc hello-clusterip

# Test depuis un Pod éphémère dans le cluster
kubectl run tmp-curl --rm -it --image=curlimages/curl --restart=Never -- \
  curl http://hello-clusterip.default.svc.cluster.local/
```

### Service NodePort (externe)

```bash
kubectl apply -f k8s/04-service-nodeport.yaml
kubectl get svc hello-nodeport

# Récupérer l'URL exposée par Minikube
minikube service hello-nodeport --url

# Test depuis l'hôte (navigateur ou curl)
curl $(minikube service hello-nodeport --url)/
```

---

## Partie 3 - Configuration & stockage

### Apply de toutes les ressources

```bash
kubectl apply -f k8s/05-configmap.yaml
kubectl apply -f k8s/06-secret.yaml
kubectl apply -f k8s/07-pvc.yaml
kubectl apply -f k8s/08-pod-with-config.yaml
```

### Vérifications

```bash
# ConfigMap & Secret
kubectl get configmap hello-config -o yaml
kubectl get secret hello-secret -o yaml
kubectl describe configmap hello-config

# PVC (doit passer à STATUS=Bound)
kubectl get pvc hello-pvc
kubectl get pv

# Variables d'env bien injectées dans le Pod
kubectl exec hello-pod-full -- env | grep APP_

# Fichier monté depuis le ConfigMap
kubectl exec hello-pod-full -- cat /etc/hello/app.properties

# Test de persistance sur le volume
kubectl exec hello-pod-full -- sh -c "echo 'hello persistance' > /data/test.txt"
kubectl exec hello-pod-full -- cat /data/test.txt

# Test de l'API : doit retourner env=production, user=ange.admin, secret_ok=true
kubectl port-forward pod/hello-pod-full 8081:5000 &
curl http://localhost:8081/
```

---

## Capture d'état final du cluster

```bash
kubectl get all -A > cluster-state.txt
# OU pour une capture d'écran : ouvrir un terminal et faire un screenshot de
# la sortie de la commande ci-dessous.
kubectl get all -A
```

Sortie attendue (extrait sur le namespace `default`) :

```
NAME                                    READY   STATUS    RESTARTS   AGE
pod/hello-deployment-xxxxxxxxxx-aaaaa   1/1     Running   0          5m
pod/hello-deployment-xxxxxxxxxx-bbbbb   1/1     Running   0          5m
pod/hello-deployment-xxxxxxxxxx-ccccc   1/1     Running   0          2m
pod/hello-pod                           1/1     Running   0          7m
pod/hello-pod-full                      1/1     Running   0          3m

NAME                       TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/hello-clusterip    ClusterIP   10.96.x.x       <none>        80/TCP         4m
service/hello-nodeport     NodePort    10.96.x.x       <none>        80:30080/TCP   4m
service/kubernetes         ClusterIP   10.96.0.1       <none>        443/TCP        1h

NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/hello-deployment   3/3     3            3           5m
```

---

## Nettoyage complet

```bash
kubectl delete -f k8s/
minikube stop
# Si tu veux tout supprimer (cluster + données) :
minikube delete
docker rmi hello-app:1.0.0
```

---

## Notes pédagogiques

| Concept           | Implémentation dans ce TP                                         |
| ----------------- | ----------------------------------------------------------------- |
| Image immutable   | `Dockerfile` multi-stage léger (`python:3.12-slim`), utilisateur non-root |
| Pod               | `01-pod.yaml` - unité atomique de déploiement                     |
| Deployment        | `02-deployment.yaml` - réplication & rolling update via ReplicaSet|
| Scaling           | `kubectl scale deployment ... --replicas=3`           |
| ClusterIP         | Service interne, résolution DNS via `hello-clusterip.default.svc.cluster.local` |
| NodePort          | Exposition externe sur la plage 30000-32767                       |
| ConfigMap         | Configuration non sensible (env + fichier monté)                  |
| Secret            | Identifiants sensibles, encodage base64                           |
| PVC               | Provisioning dynamique via la StorageClass par défaut             |
| Sondes            | `readinessProbe` + `livenessProbe` sur `/healthz`                 |
