#!/bin/bash
docker build -t dmriprep:kube3 -f dockerfile-dmriprep-kube .
docker tag dmriprep:kube3 gcr.io/dmriprep/dmriprep:kube3
docker push gcr.io/dmriprep/dmriprep:kube3
