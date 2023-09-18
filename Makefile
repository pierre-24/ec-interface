install:
	pip install -e .[dev]

lint:
	flake8 ec_interface --max-line-length=120 --ignore=N802

test:
	pytest tests