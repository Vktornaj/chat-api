#! /bin/bash

set -e

docker compose down

docker compose build

source ./config/.env

docker compose up -d

docker compose logs -f

# docker exec chat-api-web-1 pytest
