#!/bin/bash
docker build -t dmriprep:kube4 -f dockerfile-dmriprep-kube .
docker tag dmriprep:kube4 gcr.io/dmriprep/dmriprep:kube4
docker push gcr.io/dmriprep/dmriprep:kube4
