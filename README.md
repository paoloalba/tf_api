# TF web API

In the repository you will find an example of web app for the deployment of an object detection TF model.
In the specific I implement a card detector for sicilian cards (https://it.wikipedia.org/wiki/Carte_da_gioco_italiane), and I implement an application for storage and tracking of sicilian card games (scopa, briscola and tivitti).

The user can login with given credentials, then start a game and submit all the game steps to a database.

![alt text](https://github.com/paoloalba/tf_api/blob/master/readme_imgs/home_page.jpg?raw=true)

Images are stored in order to perform a regular reinforcment learning for the card detector model, and in the future to train a recommendation engine for the next move to play on a game.

The whole application is implemented within the Flask framework, with the addition of gunicorn and an Nginx reverse proxying for improved security and use of SSL protocols.
The Nginx is configured to work both with a local run of the docker instances, or to run on a K8s cluster.
For a deployment on a K8s cluster please refer to https://github.com/paoloalba/deployer_k8s.

The application can also be used to perform some light-learning, in order to easily extend your training data set (see https://github.com/paoloalba/dev_tf_model/blob/master/app/helpers/prediction_handler.py)

### Train your model

To reproduce the steps to generate the card detector model, or to train your own, please refer to https://github.com/paoloalba/dev_tf_model

### Build and run

Modify the ```tf_build_run_server.bat``` file for your needs.
This will run two containers, respectively for the main flask app and for the Nginx reverse proxying.
On your local host you will be able to access the app directly on port 5000, or on port 80 through the Nginx proxy (this will result in better logins).
To generate the needed credentials see the "credential_creator" section.

### Build and push

Modify the ```tf_build_push_server.bat``` file for your needs.
This will first build the training and evaluation Docker images, and then push them to your specified Docker Registry.
The script is already set for the use of Azure Container Registry, but any other technology can be employed.

### Analyse your logs

In analyse_logs I provide a convenience class to analyse the outcoming server logs, e.g. to inspect malicious connections attempts (there are more than one could expect!)

### Motivation

After I started to play sicilian card games with my wife, I started wondering if a machine learning approach would have been faster than her in learning the meaning of the cards (indeed the pattern on cards are quite peculiar and will surely confuse a first time player).
In the end she was pretty much faster in learning the cards, but I am still happy to have had a chance to bring some of my roots to the machine learning world!

