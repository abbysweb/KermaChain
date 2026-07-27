.PHONY: run test clean docker-build docker-up docker-down

run:
	python -m kerma.main

test:
	python -m pytest tests/ -v

clean:
	rm -f db.db
	rm -f peers.json
	rm -rf __pycache__ kerma/__pycache__ kerma/network/__pycache__ kerma/storage/__pycache__ tests/__pycache__

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
