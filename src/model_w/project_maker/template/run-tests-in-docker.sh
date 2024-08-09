#!/bin/bash

# Run tests in docker and pass through any arguments
docker compose -f docker-compose-e2e.yaml up --build --abort-on-container-exit --remove-orphans

# Open the test report
xdg-open api/bdd/report/results/report.html &> /dev/null