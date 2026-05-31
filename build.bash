#!/usr/bin/env bash
set -euo pipefail

image_name=ardusub_sim
image_tag=humble

if [ ! -f "docker/Dockerfile" ]; then
    echo "Err: docker/Dockerfile not found. Run from the ardusub_sim repo root."
    exit 1
fi

image_plus_tag=$image_name:$(export LC_ALL=C; date +%Y_%m_%d_%H%M)
docker build --rm -t "$image_plus_tag" -f docker/Dockerfile docker
docker tag "$image_plus_tag" "$image_name:$image_tag"

echo "Built $image_plus_tag and tagged as $image_name:$image_tag"
