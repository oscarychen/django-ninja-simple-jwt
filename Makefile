SHELL := /bin/bash

#!make
ifneq (,$(wildcard ./.env))
    include .env
    export
endif
.PHONY: python-requirements setup test run setup-env makemigrations migrate manage check fmt run-docker run-docker-db stop-docker

CONDA=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate

setup-conda-python:
	conda remove --name py312-django-ninja-simple-jwt --all
	conda create -n py312-django-ninja-simple-jwt python=3.12

setup-venv:
	rm -rf environment
	$(CONDA) py312-django-ninja-simple-jwt ; python -m venv environment

python-requirements:
	. environment/bin/activate && \
	pip install --upgrade pip && \
	pip install -r requirements.txt && \
	pre-commit install

conda-setup: setup-conda-python setup-venv python-requirements
system-setup: python-requirements

test:
	. environment/bin/activate && tox

check:
	. environment/bin/activate && \
	pre-commit run --all-files

fmt:
	. environment/bin/activate && \
	python -m isort .
	python -m black .
