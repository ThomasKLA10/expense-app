#!/bin/bash

# Set environment to testing to ensure we never touch production DB
export FLASK_ENV=testing

# Run the tests without warnings
pytest "$@" -p no:warnings

# Reset environment
unset FLASK_ENV 