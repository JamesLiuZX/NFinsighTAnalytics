#!/bin/bash
cd ./templates
for i in $(ls)
do
  kubectl apply -f $i
done