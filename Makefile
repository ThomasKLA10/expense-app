# Makefile for local development and testing with BBDeployor

# Include bbdeployor.conf
include bbdeployor.conf

# Default target
.PHONY: all
all: help

# Help message
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  docker      - Build and run the project in a Docker container"
	@echo "  undocker    - Remove the Docker container"
	@echo "  project     - Build the project locally"
	@echo "  clean       - Clean up build artifacts"

# Docker targets
.PHONY: docker
docker:
	@echo "Building Docker container for $(HOSTNAME)..."
	docker run --rm -it -p 8080:80 -v "$(PWD):/var/www/$(SHORTNAME)" \
		--name "$(SHORTNAME)" bbdeployor-base:latest \
		/bin/bash -c "cd /var/www/$(SHORTNAME) && \
		bbdeployor/configure_container && \
		bbdeployor/make_project && \
		bbdeployor/install_project && \
		echo 'Container is running. Press Ctrl+C to stop.' && \
		tail -f /dev/null"

.PHONY: undocker
undocker:
	@echo "Removing Docker container for $(HOSTNAME)..."
	-docker stop "$(SHORTNAME)"
	-docker rm "$(SHORTNAME)"

# Local build target
.PHONY: project
project:
	@echo "Building project locally..."
	mkdir -p app/uploads app/static/uploads app/archive temp logs
	pip install -r requirements.txt
	if [ ! -f .env ]; then cp config/.env.example .env; fi
	chmod +x scripts/*.sh

# Clean target
.PHONY: clean
clean:
	@echo "Cleaning up..."
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	find . -name ".pytest_cache" -type d -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "htmlcov" -type d -exec rm -rf {} + 