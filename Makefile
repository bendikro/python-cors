##TWINE_REPOSITORY:  The pypi repository. Should be a section in the config file (default: pypi)
export TWINE_REPOSITORY?=pypi

.DEFAULT_GOAL=help

build: ## Build source tar ball
	python setup.py build

sdist: ## Build source tar ball
	python setup.py sdist

wheel: ## Build wheel
	python setup.py bdist_wheel

upload:
	twine upload --verbose  dist/*

clean: ## Cleanup
	$(RM) -r build dist cors.egg-info testcoverage

help: ## Show this help
	@echo "==================================="
	@echo "    Available targets"
	@echo "==================================="
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -rn "s/(\S+)\s*:+?\s##\s?\s(.+)/\1 \"\2\"/p" | xargs printf " %-10s : %5s\n"
	@echo
	@echo "-----------------------------------------------------------------"
	@echo "  Available environment configurations to set with 'make [VARIABLE=value] <target>'"
	@echo "-----------------------------------------------------------------"
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -rn "s/^##\s*(\S+)\s*:\s*(.+)/\1 \"\2\"/p" | xargs printf " %-20s    : %5s\n"
	@echo
	@echo -e "Example:\n make TWINE_REPOSITORY=pypitest"
	@echo
