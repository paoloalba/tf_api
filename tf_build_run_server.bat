@REM GLOBAL @SETTINGS
@set registry=<docker_registry_address>
@set registryName=<docker_registry_name>

@set dockerfile=docker-compose.yml
@set dockerfile_src=<docker_file_path>

@set repositoryName=tf_server_with_detection
@set versionNumber=1.0.0

@set IS_DOCKER=y
@set permanent_storage=<host/pmt/storage>

@REM GENERATE DOCKER COMPOSE FILE
call docker-compose -f %dockerfile% build

call docker-compose -f %dockerfile% up
call docker-compose -f %dockerfile% down
