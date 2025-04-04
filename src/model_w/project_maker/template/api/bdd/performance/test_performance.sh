#!/bin/bash

docker compose -p ___project_name__snake___ -f ./bdd/_infrastructure/docker-compose-run.yaml up --force-recreate --abort-on-container-exit --remove-orphans --build

docker compose -p ___project_name__snake___ -f ./bdd/_infrastructure/docker-compose-run.yaml logs > performance_test.log

