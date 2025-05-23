#!/bin/bash
set -euxo pipefail

docker compose --file docker-compose.yaml --file docker-compose-dev.yaml up --build "$@"