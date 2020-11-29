@REM GLOBAL @SETTINGS
@set registry=<docker_registry_address>
@set registryName=<docker_registry_name>

@set dockerfile=docker-compose.yml
@set dockerfile_src=

@set repositoryName=tf_server
@set versionNumber=1.1.1

call docker-compose -f %dockerfile% build

@set repositoryBaseName=%registry%/%repositoryName%
@set serverTag=%repositoryBaseName%:%versionNumber%
@set nginxTag=%repositoryBaseName%:nginx

call az acr login --name %registryName%

call docker push %serverTag%
call docker push %nginxTag%
