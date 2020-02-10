SHELL := /bin/bash

install:
	python3 -m venv milestone1
	source milestone1/bin/activate && pip install -r requirements.txt

test:
	python run.py

clean:
	rm -rf milestone1