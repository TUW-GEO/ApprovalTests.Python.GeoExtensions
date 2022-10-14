.PHONY: help clean setup test

help:
	@echo "make clean"
	@echo " clean all python build/compilation files and directories"
	@echo "make setup"
	@echo " install dependencies in active python environment"
	@echo "make test"
	@echo " run all tests and coverage"
	@echo "make version"
	@echo " update _version.py with current version tag"
	@echo "make dist"
	@echo " build the package ready for distribution and update the version tag"

clean:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force {} +
	rm --force .coverage
	rm --force --recursive .pytest_cache
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info
	rm --force .install.done
	rm --force .install.test.done

.install.done:
	pip install --upgrade pip setuptools
	pip install -e .
	touch .install.done

setup: .install.done

.install.test.done:
	pip install --upgrade pip setuptools
	pip install -e .[test]
	touch .install.test.done

test: .install.test.done
	coverage run -m pytest --doctest-modules && coverage report -m

version:
	echo "__version__ = \"$(shell git describe --always --tags --abbrev=0)\"" > src/pytest_approvaltests_geo/_version.py

dist: version
	pip3 install build twine
	python3 -m build

version-nightly:
	echo "__version__ = \"$(shell python git_version_to_pep440.py $(shell git describe --always))\"" > src/pytest_approvaltests_geo/_version.py

dist-nightly: version-nightly
	pip3 install build twine
	python3 -m build
