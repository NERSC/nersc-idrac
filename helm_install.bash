#!/bin/bash

echo "[>>] Need reliable helm >= 3.7.0"
if [ ! -f 'helm.tar.gz' ]; then
  curl -fsSL -o helm.tar.gz https://get.helm.sh/helm-v3.13.3-linux-amd64.tar.gz
fi
if [ ! -d 'linux-amd64' ]; then
  tar -xzvf helm.tar.gz
fi
HELM="./linux-amd64/helm"
echo "Using Helm verison: $($HELM version)"

echo "[>>] RUN: helm dependency build, to download charts"
$HELM dependency build .

echo "[--] Create namespaces"
for NS in ingress-nginx telem; do
  kubectl get namespace $NS 
  if [ $? -ne 0 ]; then
    echo "[>>] Create namespace: $NS" 
    kubectl create namespace $NS
  else
    echo "[OK] Found namespace $NS"
  fi
done

echo "[--] Check for helmfile"
if [ ! -f "helmfile" ]; then 
  echo "[>>] Download helmfile"
  curl -sLk -o helmfile  https://github.com/roboll/helmfile/releases/download/v0.144.0/helmfile_linux_amd64
  chmod +x helmfile
else
  echo "[OK] Found helmfile"
fi

read -p "Do you want to install the Charts now? [y/N]" FOO
if [ "$FOO" == 'y' ]; then
  echo "[>>] Installing charts: ./helmfile --helm-binary $HELM -f helmfile.yaml sync"
  ./helmfile --helm-binary $HELM -f helmfile.yaml sync
else
  echo "[--] Do not install charts now.
    To install charts run: ./helmfile --helm-binary $HELM -f helmfile.yaml sync"
fi
echo "[--] To Uninstall: ./helmfile --helm-binary $HELM -f helmfile.yaml delete"
echo "[OK] Done"
