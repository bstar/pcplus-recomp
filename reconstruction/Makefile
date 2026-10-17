.PHONY: build test test-modem

build:
	python3 build_compat.py

test: build
	python3 dos_lab.py

test-modem: build
	python3 dos_lab.py --variant candidate --baud 38400 --transport modem
