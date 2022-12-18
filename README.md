# API Example App
#### Do not install this in a production cluster
This is a demo application and may use namespaces you already have in use.

### Requirements
* Terraform
* docker

### Ways this could be improved
* Unit tests
* Database for central config
* Pull tokens from secrets management API
* WAF, service mesh or other ingress that supports L7 rate limiting
* Handle IP source addresses behind proxies if needed for prod
* Prometheus flask exporter could be improved to allow direct access to metrics 
  from code and use them as the source of truth 
* Load testing
* Alerts
* Hook up Terraform with cloud provider
* Add CI jobs with terraform validate/linting/fmt
* Don't put python testing libraries in final docker image

### Testing
```shell
$ terraform init && terraform apply

$ curl -v http://localhost:8080/healthcheck
< HTTP/1.1 200 OK

$ curl http://localhost:8080/stats
< HTTP/1.1 200 OK
{"cidrs":0,"blocked_requests":0,"accepted_requests":0}

$ curl -X POST -d '{"cidr":"172.10.10.0/24","ttl": 3600}' http://localhost:8080/block
< HTTP/1.1 401

$ curl -X POST -H 'Authorization: Bearer xxxxxxxx' -d '{"cidr":"172.10.10.0/24","ttl": 3600}' http://localhost:8080/block
< HTTP/1.1 200

$ curl http://localhost:8080/metrics
# Prometheus style metrics

$ terraform destroy
```


## Bonus - Taking this to k8s
Let's add a k8s deployment with prometheus monitoring and deploy with ArgoCD

### Additional Requirements
* A fresh development kubernetes cluster of some type, like [minikube](https://minikube.sigs.k8s.io/docs/start/)
* [kubectl](https://kubernetes.io/docs/tasks/tools/)
* [kustomize](https://kubectl.docs.kubernetes.io/installation/kustomize/) 

### Minikube setup
```shell
# set memory to be within the resources set for docker daemon
$ minikube delete && minikube start --kubernetes-version=v1.24.0 --memory=5900M --bootstrapper=kubeadm --extra-config=kubelet.authentication-token-webhook=true --extra-config=kubelet.authorization-mode=Webhook --extra-config=scheduler.bind-address=0.0.0.0 --extra-config=controller-manager.bind-address=0.0.0.0

```

### Initial Bootstrapping
ArgoCD will manage itself. The setup is fully declarative from code.

1) Create namespace and run initial kustomize apply
```shell
kubectl create namespace argocd
cd k8s-deploy/argocd
# Apply CRDs first to avoid errors with missing APIs
kubectl apply -k https://github.com/argoproj/argo-cd/manifests/crds\?ref\=stable
kustomize build . | kubectl apply -f -
```
2) ArgoCD comes online and now resyncs from this same repo 
3) Any updates may now be simply committed and Argo deals with the updates



### View ArgoCD web UI with default creds
```shell
# Get initial generated admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 --decode
# Start port forwarding
kubectl port-forward -n argocd service/argocd-server 8081:80 
```
Open in web browser:

Username: admin

Password: (see above)

http://localhost:8081


### Connect to example app and inspect endpoints
```shell
kubectl port-forward -n api-example service/api-example 8080:80
curl localhost:8080
curl localhost:8080/stats
curl localhost:8080/metrics
curl localhost:8080/healthcheck
curl -X POST -d '{"cidr":"172.10.10.0/24","ttl": 3600}' http://localhost:8080/block
curl -X POST -H 'Authorization: Bearer xxxxxxxx' -d '{"cidr":"172.10.10.0/24","ttl": 3600}' http://localhost:8080/block
```

### See dashboard for example app
![Example Dashboard](https://github.com/bizrad/simple-rest-example/blob/main/Example-Dashboard.png?raw=true)

```shell
kubectl port-forward -n observe service/kube-prometheus-stack-grafana 8082:80
```
Open dashboard in web browser:

Username: admin

Password: prom-operator

http://localhost:8082/d/_example/api-example-app?orgId=1&refresh=5s

### See prometheus dashboard and scraping config
```shell
kubectl port-forward -n observe service/kube-prometheus-stack-prometheus 8083:80
```
Open in web browser: http://localhost:8083

### Teardown
```shell
minikube delete
```

### Ways this k8s deployment could be improved
* Adjust HPA for autoscaling when backed with DB
* Autoscale based on metrics
* Profile usage and properly set cpu/memory requests/limits based on real use


