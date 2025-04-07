# Makefile for BB Expense App

.PHONY: docker undocker project clean

# Build and run the project in a Docker container
docker:
	@echo "Building Docker container for BB Expense App..."
	docker build -t bb-expense-app .
	docker run -d --name bb-expense-app -p 5000:5000 bb-expense-app

# Stop and remove the Docker container
undocker:
	@echo "Removing Docker container..."
	-docker stop bb-expense-app
	-docker rm bb-expense-app

# Build the project locally
project:
	@echo "Building BB Expense App locally..."
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	mkdir -p app/static/uploads app/static/archives temp logs
	chmod +x scripts/*.sh

# Clean up build artifacts
clean:
	@echo "Cleaning up..."
	rm -rf __pycache__
	rm -rf app/__pycache__
	rm -rf app/*/__pycache__
	rm -rf .pytest_cache