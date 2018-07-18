#!/usr/bin/env bash

if [ "$TRAVIS_PYTHON_VERSION" == "3.6" ]; then
	echo "Building Docker image from the present sources..."
	echo "Starting image build..."
	docker build -f deploy/Dockerfile-development -t smbackend .
	echo "Testing image..."
	docker run --rm smbackend npm run build
fi
