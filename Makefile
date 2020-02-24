SHELL := /bin/bash

install: .installed

test: .installed
	source milestone1/bin/activate && python test.py

build: .installed
	@echo To watch the bot play, go to https://play.pokemonshowdown.com/
	@echo and log in as the user \"harijo\" with password \"battlebot\"
	@echo Otherwise, you can just watch the bot play from the terminal.
	@echo -e "\n"
	@read -n1 -r -p "Press any key to continue running the bot..."
	source milestone1/bin/activate && python run.py

clean:
	rm -rf milestone1

.installed:
	python3 -m venv milestone1
	source milestone1/bin/activate && pip install -r requirements.txt
	@echo "installed" > .installed

.PHONY: install test build clean