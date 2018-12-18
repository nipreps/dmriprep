#!/bin/bash

# login
gcloud auth login anishakeshavan@gmail.com

# set the project to dmriprep
gcloud config set project dmriprep

# some variables
ZONE=us-west1-a
MAX_NODES=4
CLUSTERNAME=dmriprep

# set the default compute zone
gcloud config set compute/zone $ZONE

# start the cluster!
gcloud beta container clusters create $CLUSTERNAME --machine-type n1-highmem-4 --enable-autoscaling --max-nodes=$MAX_NODES --num-nodes 1 --cluster-version latest --node-labels dmriprep/node-purpose=core
