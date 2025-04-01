#!/bin/bash

# Set environment to testing to ensure we never touch production DB
export FLASK_ENV=testing

# Run the tests
pytest "$@"

# Reset environment
unset FLASK_ENV 