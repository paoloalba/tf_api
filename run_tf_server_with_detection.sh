#!/usr/bin/env sh

gunicorn --bind 0.0.0.0:5000 server_project:app --config gunicorn_conf.py

