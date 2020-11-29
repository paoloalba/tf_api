# Credential creator

This repository contains all the necessary to build and run a docker image to generate a self signed certificate for SSL transactions.

### Build and run

On your windows host modify the the ```build_run.bat``` file for your needs, and then run it.

This will build a linux docker image and then run the corresponding container, which will make use of linux built-in openssl package to generate all the needed certificates, and then export them on your host´s shared storage for further use
