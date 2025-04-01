#!/bin/bash

docker build -t stage1-api .
docker run -d -p 8080:8080 \
    -v $(pwd)/instance:/app/instance \
    stage1-api