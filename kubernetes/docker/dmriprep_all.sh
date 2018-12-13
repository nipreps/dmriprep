#!/bin/bash
mkdir inputs
mkdir outputs
dmriprep-data --subject $1 $PWD/inputs/
dmriprep $PWD/inputs $PWD/outputs
dmriprep-upload --access_key $2 --secret_key $3 $PWD/outputs preafq-hbn 
