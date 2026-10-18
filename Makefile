MODULES := escape attributes screen text reports erase cursor_state cursor_shape scroll modes render input_dispatch csi ui_windows modem_commands
.PHONY: all serial parser keyboard config-dos $(MODULES) $(addprefix test-,$(MODULES)) test test-driver test-parser test-keyboard test-config test-config-dos test-parser-compat test-csi-relocation test-modes-relocation test-input-relocation test-terminal-services compat test-compat test-modem clean

all: serial parser keyboard $(MODULES) config-dos config-replace config-abi terminal

.PHONY: config-abi test-config-abi test-directory test-ui-flow
config-abi:
	python3 standalone/build_config_abi.py

test-config-abi: config-abi
	python3 standalone/test_config_abi.py

test-directory:
	python3 -m unittest discover -s src/directory -p 'test_*.py' -v

test-ui-flow: ui_windows
	python3 standalone/check_ui_flow.py

.PHONY: config-replace test-config-replace
config-replace:
	python3 standalone/build_config_replace.py

test-config-replace: config-replace
	python3 standalone/test_config_replace.py

.PHONY: terminal test-terminal test-bbs-modem
terminal:
	python3 standalone/build_terminal.py

test-terminal: terminal
	python3 standalone/check_transport.py
	python3 standalone/check_terminal_options.py --binary build/terminal/TERMINAL.EXE --map build/terminal/terminal.map
	python3 lab/bbs/check_formfeed.py
	python3 lab/bbs/check_enigma_controls.py
	python3 standalone/check_terminal_ui.py
	python3 standalone/test_terminal.py

test-bbs-modem:
	python3 lab/bbs/check_modem.py

$(MODULES):
	python3 standalone/build_$@.py

$(addprefix test-,$(MODULES)): test-%: %
	python3 standalone/check_$*.py
	python3 standalone/test_$*_dos.py

test-csi-relocation: csi
	python3 standalone/check_csi_relocation.py

test-modes-relocation: modes
	python3 standalone/check_modes_relocation.py

test-input-relocation: input_dispatch
	python3 standalone/check_input_dispatch_relocation.py

test-terminal-services: csi
	python3 standalone/check_terminal_services.py

test-config:
	python3 -m unittest discover -s src/config -p 'test_*.py' -v

config-dos:
	python3 standalone/build_config_dos.py

test-config-dos: config-dos
	python3 standalone/test_config_dos.py

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

test: test-driver test-parser test-keyboard $(addprefix test-,$(MODULES)) test-csi-relocation test-modes-relocation test-input-relocation test-terminal-services test-config test-config-dos test-config-replace test-config-abi test-directory test-ui-flow test-terminal test-bbs-modem
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
	rm -rf build/standalone build/ansi build/keyboard build/csi-relocation build/cursor-state build/cursor-shape build/config-dos build/config-replace build/config-abi build/ui-windows build/ui-windows-dos build/modem-commands build/modem-commands-dos build/terminal build/terminal-tests build/terminal-options $(addprefix build/,$(MODULES))
