#!/usr/bin/env sh

export registry=myregistry.com
export registryName=myregistry

export dockerfile=docker-compose.yml
export dockerfile_src=Dockerfile_tf_server_with_detection

export repositoryName=tf_server_with_detection
export versionNumber=1.0.0

export IS_DOCKER=y
export permanent_storage=/host/permanent_storage

docker-compose -f ${dockerfile} build

docker-compose -f ${dockerfile} up
docker-compose -f ${dockerfile} down
