.PHONY: all test test-driver compat test-compat test-modem clean

all:
	python3 standalone/build.py

test-driver: all
	python3 standalone/check_uart.py

test: test-driver
	python3 standalone/test_serial.py

compat:
	$(MAKE) -C reconstruction build

test-compat:
	$(MAKE) -C reconstruction test

test-modem:
	$(MAKE) -C reconstruction test-modem

clean:
	rm -rf build/standalone
