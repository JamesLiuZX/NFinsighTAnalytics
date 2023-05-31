#!/bin/bash
cd ./templates
for i in $(ls)
do
  kubectl delete -f $i
done