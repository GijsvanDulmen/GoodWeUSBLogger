#!/bin/bash
docker build -t goodweusblogger:v1 --build-arg ARCH=arm64v8/ .
docker push goodweusblogger:v1

# kubectl apply -f ./deployment.yml