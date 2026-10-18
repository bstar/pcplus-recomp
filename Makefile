MODULES := escape attributes screen text reports erase cursor_state cursor_shape scroll modes render input_dispatch csi ui_windows modem_commands modem_responses modem_send directory_dial directory_accounting keyboard_mapping keyboard_detection line_edit meta_keys character_edit program_exec terminal_reset transfer_blocks transfer_receive transfer_send transfer_files transfer_session transfer_uart
.PHONY: all serial parser keyboard config-dos $(MODULES) $(addprefix test-,$(MODULES)) test test-driver test-parser test-keyboard test-config test-config-dos test-parser-compat test-csi-relocation test-modes-relocation test-input-relocation test-terminal-services compat test-compat test-modem clean

all: serial parser keyboard $(MODULES) config-dos config-replace config-abi directory-browser directory-editor process download-file upload-file transfer-metadata batch-header transfer-session-composite transfer-storage terminal

.PHONY: config-abi test-config-abi test-directory test-ui-flow directory-browser test-directory-browser directory-editor test-directory-editor test-directory-replace test-directory-dos
.PHONY: test-keymap test-keymap-dos test-key-actions-dos test-keyboard-mapping-raw

test-keymap:
	python3 -m unittest discover -s src/key_mapping -p 'test_*.py' -v

test-key-actions-dos:
	python3 standalone/check_key_actions_dos.py

test-keymap-dos:
	python3 standalone/check_keymap_dos.py

test-keyboard-mapping-raw: keyboard_mapping
	python3 standalone/check_keyboard_mapping_raw.py

directory-editor:
	python3 standalone/build_directory_editor.py

test-directory-editor: directory-editor
	python3 standalone/check_directory_editor.py
	python3 standalone/test_directory_editor_dos.py

test-directory-replace:
	python3 standalone/check_directory_replace.py

directory-browser:
	python3 standalone/build_directory_browser.py

test-directory-browser: directory-browser
	python3 standalone/check_directory_browser.py
	python3 standalone/test_directory_browser_dos.py

test-directory-dos:
	python3 standalone/check_directory_dos.py
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

.PHONY: terminal test-terminal test-bbs-modem test-modem-import
terminal:
	python3 standalone/build_terminal.py

test-terminal: terminal
	python3 standalone/check_terminal_capture_live.py
	python3 standalone/check_far_storage_live.py
	python3 standalone/test_far_storage_dos.py
	python3 standalone/check_terminal_transfer_live.py
	python3 standalone/check_terminal_upload_live.py
	python3 standalone/check_program_actions_live.py
	python3 standalone/check_terminal_reset_live.py
	python3 standalone/test_program_actions_dos.py
	python3 standalone/test_terminal_reset_live_dos.py
	python3 standalone/check_transport.py
	python3 standalone/check_key_output.py
	python3 standalone/check_key_live.py
	python3 standalone/check_meta_actions_live.py
	python3 standalone/check_character_edit_live.py
	python3 standalone/test_meta_actions_dos.py
	python3 standalone/check_line_edit_live.py
	python3 standalone/check_terminal_options.py --binary build/terminal/TERMINAL.EXE --map build/terminal/terminal.map
	python3 lab/bbs/check_formfeed.py
	python3 lab/bbs/check_enigma_controls.py
	python3 standalone/check_terminal_ui.py
	python3 standalone/test_terminal.py
	python3 standalone/test_terminal_keys.py
	python3 standalone/check_terminal_config.py
	python3 standalone/check_startup_import.py --check-invalid-abi
	python3 standalone/check_connection.py
	python3 standalone/check_directory_live.py
	python3 standalone/check_directory_actions.py
	python3 standalone/test_terminal_config.py
	python3 standalone/test_connection_dos.py
	python3 standalone/test_directory_terminal.py

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

test-modem-import:
	python3 standalone/check_modem_import.py

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

test: test-capture-file test-capture-session test-transfer-metadata test-batch-header test-batch-download test-batch-upload test-upload-file test-transfer-session-composite test-transfer-storage test-download-file test-process test-driver test-parser test-keyboard $(addprefix test-,$(MODULES)) test-keyboard-mapping-raw test-keymap test-keymap-dos test-key-actions-dos test-csi-relocation test-modes-relocation test-input-relocation test-terminal-services test-config test-modem-import test-config-dos test-config-replace test-config-abi test-directory test-directory-dos test-directory-browser test-directory-editor test-directory-replace test-ui-flow test-terminal test-terminal-ymodem-live test-bbs-modem
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
	rm -rf build/standalone build/ansi build/keyboard build/keyboard-mapping build/keyboard-detection build/keyboard-detection-dos build/line-edit build/keymap-dos build/terminal-keys build/csi-relocation build/cursor-state build/cursor-shape build/config-dos build/config-replace build/config-abi build/ui-windows build/ui-windows-dos build/modem-commands build/modem-commands-dos build/modem-responses build/modem-responses-dos build/modem-send build/modem-send-dos build/modem-import build/connection-dos build/directory-dial build/directory-dial-dos build/directory-accounting build/directory-accounting-dos build/directory-browser build/directory-browser-dos build/directory-editor build/directory-replace build/directory-dos build/directory-terminal build/terminal build/terminal-tests build/terminal-options build/process build/download-file build/transfer-send build/transfer-metadata build/transfer-metadata-dos build/batch-header build/batch-download build/batch-upload build/transfer-files build/transfer-session build/transfer-session-composite build/transfer-storage build/transfer-uart $(addprefix build/,$(MODULES))

.PHONY: process test-process
process:
	python3 standalone/build_process.py

test-process: process
	python3 standalone/check_process.py
	python3 standalone/check_program_process.py
	python3 standalone/test_process_dos.py
	python3 standalone/test_program_process_dos.py

.PHONY: download-file test-download-file
download-file:
	python3 standalone/build_download_file.py

test-download-file: download-file
	python3 standalone/test_download_file_dos.py

.PHONY: transfer-session-composite test-transfer-session-composite transfer-storage test-transfer-storage
transfer-session-composite:
	python3 standalone/build_transfer_session_composite.py

test-transfer-session-composite: transfer-session-composite
	python3 standalone/check_transfer_session_composite.py
	python3 standalone/test_transfer_session_composite_dos.py

transfer-storage:
	python3 standalone/build_transfer_storage.py

test-transfer-storage: transfer-storage
	python3 standalone/test_transfer_storage_dos.py

.PHONY: upload-file test-upload-file
upload-file:
	python3 standalone/build_upload_file.py

test-upload-file: upload-file
	python3 standalone/check_upload_file.py
	python3 standalone/test_upload_file_dos.py

.PHONY: transfer-metadata test-transfer-metadata batch-header test-batch-header
transfer-metadata:
	python3 standalone/build_transfer_metadata.py

test-transfer-metadata: transfer-metadata
	python3 standalone/check_transfer_metadata.py
	python3 standalone/test_transfer_metadata_dos.py

batch-header:
	python3 standalone/build_batch_header.py

test-batch-header: batch-header
	python3 standalone/check_batch_header.py

.PHONY: test-batch-download test-batch-upload test-terminal-ymodem-live
.PHONY: test-capture-file test-capture-session
test-capture-file:
	python3 standalone/check_capture_file.py
test-capture-session:
	python3 standalone/check_capture_session.py
test-batch-download:
	python3 standalone/check_batch_download.py

test-batch-upload:
	python3 standalone/check_batch_upload.py

test-terminal-ymodem-live: terminal
	python3 standalone/check_terminal_ymodem_live.py
