.PHONY: all test compat test-compat test-modem clean

all:
	python3 standalone/build.py

test: all
	python3 standalone/test_serial.py

compat:
	$(MAKE) -C reconstruction build

test-compat:
	$(MAKE) -C reconstruction test

test-modem:
	$(MAKE) -C reconstruction test-modem

clean:
	rm -rf build/standalone
