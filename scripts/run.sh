#!/bin/bash
set -euxo pipefail

docker compose --file docker-compose.yaml up --build "$@"