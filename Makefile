MODULES := escape attributes screen text reports erase cursor_state csi
.PHONY: all serial parser keyboard $(MODULES) $(addprefix test-,$(MODULES)) test test-driver test-parser test-keyboard test-parser-compat test-csi-relocation compat test-compat test-modem clean

all: serial parser keyboard $(MODULES)

$(MODULES):
	python3 standalone/build_$@.py

$(addprefix test-,$(MODULES)): test-%: %
	python3 standalone/check_$*.py
	python3 standalone/test_$*_dos.py

test-csi-relocation: csi
	python3 standalone/check_csi_relocation.py

serial:
	python3 standalone/build.py

parser:
	python3 standalone/build_ansi.py

keyboard:
	python3 standalone/build_keyboard.py

test-keyboard: keyboard
	python3 standalone/check_keyboard.py
	python3 standalone/test_keyboard_dos.py

test-driver: serial
	python3 standalone/check_uart.py

test-parser: parser
	python3 standalone/check_ansi.py
	python3 standalone/test_parser_dos.py

test: test-driver test-parser test-keyboard $(addprefix test-,$(MODULES)) test-csi-relocation
	python3 standalone/test_serial.py

test-parser-compat: parser compat
	python3 reconstruction/compare_ansi_parameters.py

compat:
	$(MAKE) -C reconstruction build

test-compat:
	$(MAKE) -C reconstruction test

test-modem:
	$(MAKE) -C reconstruction test-modem

clean:
	rm -rf build/standalone build/ansi build/keyboard build/csi-relocation build/cursor-state $(addprefix build/,$(MODULES))
