.PHONY: help test run install uninstall clean

PYTHON ?= python3

help:
	@echo "Lumen Development & Build Targets:"
	@echo "  make test      Run unit and integration test suite (headless)"
	@echo "  make run       Run Lumen launcher locally"
	@echo "  make install   Install Lumen locally for current user"
	@echo "  make uninstall Remove local installation"
	@echo "  make clean     Clean temporary files and caches"

test:
	QT_QPA_PLATFORM=offscreen $(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

run:
	$(PYTHON) -m lumen

install:
	./install.sh

uninstall:
	./uninstall.sh

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	rm -rf build dist *.egg-info .pytest_cache .coverage htmlcov
