MODULES := escape attributes screen text reports erase cursor_state cursor_shape scroll modes render input_dispatch csi ui_windows modem_commands modem_responses modem_send directory_dial directory_accounting keyboard_mapping keyboard_detection line_edit meta_keys character_edit program_exec terminal_reset transfer_blocks transfer_receive transfer_send transfer_files transfer_session transfer_uart
.PHONY: all serial parser keyboard config-dos $(MODULES) $(addprefix test-,$(MODULES)) test test-driver test-parser test-keyboard test-config test-config-dos test-parser-compat test-csi-relocation test-modes-relocation test-input-relocation test-terminal-services compat test-compat test-modem clean

all: serial parser keyboard $(MODULES) config-dos config-replace config-abi directory-browser directory-editor process download-file upload-file transfer-metadata batch-header transfer-session-composite transfer-storage terminal


.PHONY: aspect-string-services test-aspect-string-services test-aspect-string-services-compat aspect-string-commands test-aspect-string-commands test-aspect-string-commands-compat
all: aspect-string-services aspect-string-commands
test: test-aspect-string-services test-aspect-string-commands
aspect-string-services:
	python3 standalone/build_aspect_string_services.py
test-aspect-string-services: aspect-string-services
	python3 standalone/check_aspect_string_services.py
test-aspect-string-services-compat: aspect-string-services
	python3 standalone/check_aspect_string_services.py --original
aspect-string-commands:
	python3 standalone/build_aspect_string_commands.py
test-aspect-string-commands:
	python3 standalone/check_aspect_string_commands.py
test-aspect-string-commands-compat:
	python3 standalone/check_aspect_string_commands.py --original analysis/pcplus-install/PCPLUS.EXE

.PHONY: aspect-parameters test-aspect-parameters test-aspect-parameters-compat aspect-strings test-aspect-strings test-aspect-strings-compat
all: aspect-parameters aspect-strings
test: test-aspect-parameters test-aspect-strings
aspect-parameters:
	python3 standalone/build_aspect_parameters.py
test-aspect-parameters:
	python3 standalone/check_aspect_parameters.py
test-aspect-parameters-compat:
	python3 standalone/check_aspect_parameters.py --original analysis/pcplus-install/PCPLUS.EXE
aspect-strings:
	python3 standalone/build_aspect_strings.py
test-aspect-strings:
	python3 standalone/check_aspect_strings.py
test-aspect-strings-compat:
	python3 standalone/check_aspect_strings.py --original analysis/pcplus-install/PCPLUS.EXE

.PHONY: aspect-long test-aspect-long test-aspect-long-compat aspect-arithmetic test-aspect-arithmetic test-aspect-arithmetic-compat
all: aspect-long aspect-arithmetic
test: test-aspect-long test-aspect-arithmetic
aspect-long:
	python3 standalone/build_aspect_long.py
test-aspect-long:
	python3 standalone/check_aspect_long.py
test-aspect-long-compat:
	python3 standalone/check_aspect_long.py --original analysis/pcplus-install/PCPLUS.EXE
aspect-arithmetic:
	python3 standalone/build_aspect_arithmetic.py
test-aspect-arithmetic:
	python3 standalone/check_aspect_arithmetic.py
test-aspect-arithmetic-compat:
	python3 standalone/check_aspect_arithmetic.py --original analysis/pcplus-install/PCPLUS.EXE

.PHONY: aspect-literal test-aspect-literal test-aspect-compat
.PHONY: aspect-operands test-aspect-operands test-aspect-operands-compat aspect-operations test-aspect-operations test-aspect-operations-compat aspect-runtime test-aspect-runtime test-aspect-runtime-compat
all: aspect-operands aspect-operations aspect-runtime
test: test-aspect-operands test-aspect-operations test-aspect-runtime
aspect-operands:
	python3 standalone/build_aspect_operands.py
test-aspect-operands:
	python3 standalone/check_aspect_operands.py
test-aspect-operands-compat:
	python3 standalone/check_aspect_operands.py --original analysis/pcplus-install/PCPLUS.EXE
aspect-operations:
	python3 standalone/build_aspect_operations.py
test-aspect-operations:
	python3 standalone/check_aspect_operations.py
test-aspect-operations-compat:
	python3 standalone/check_aspect_operations.py --original analysis/pcplus-install/PCPLUS.EXE
aspect-runtime:
	python3 standalone/build_aspect_runtime.py
test-aspect-runtime:
	python3 standalone/check_aspect_runtime.py
test-aspect-runtime-compat:
	python3 standalone/check_aspect_runtime.py --original analysis/pcplus-install/PCPLUS.EXE
.PHONY: aspect-flow test-aspect-flow test-aspect-flow-compat aspect-file test-aspect-file
all: aspect-flow aspect-file
test: test-aspect-flow test-aspect-file
aspect-flow:
	python3 standalone/build_aspect_flow.py
test-aspect-flow:
	python3 standalone/check_aspect_flow.py
test-aspect-flow-compat:
	python3 standalone/check_aspect_flow.py --original analysis/pcplus-install/PCPLUS.EXE
aspect-file:
	python3 standalone/build_aspect_file.py
test-aspect-file:
	python3 standalone/check_aspect_file.py
.PHONY: aspect-stack test-aspect-stack test-aspect-stack-compat aspect-unwind test-aspect-unwind test-aspect-unwind-compat
all: aspect-stack aspect-unwind
test: test-aspect-stack test-aspect-unwind
aspect-stack:
	python3 standalone/build_aspect_stack.py
test-aspect-stack:
	python3 standalone/check_aspect_stack.py
test-aspect-stack-compat:
	python3 standalone/check_aspect_stack.py --original analysis/pcplus-install/PCPLUS.EXE
aspect-unwind:
	python3 standalone/build_aspect_unwind.py
test-aspect-unwind:
	python3 standalone/check_aspect_unwind.py
test-aspect-unwind-compat:
	python3 standalone/check_aspect_unwind.py --original analysis/pcplus-install/PCPLUS.EXE
.PHONY: aspect-dispatch test-aspect-dispatch test-aspect-dispatch-compat
all: aspect-dispatch
test: test-aspect-dispatch
aspect-dispatch:
	python3 standalone/build_aspect_dispatch.py
test-aspect-dispatch:
	python3 standalone/check_aspect_dispatch.py
test-aspect-dispatch-compat:
	python3 standalone/check_aspect_dispatch.py --original analysis/pcplus-install/PCPLUS.EXE
.PHONY: aspect-globals test-aspect-globals test-aspect-globals-compat
all: aspect-globals
test: test-aspect-globals
aspect-globals:
	python3 standalone/build_aspect_globals.py
test-aspect-globals:
	python3 standalone/check_aspect_globals.py
test-aspect-globals-compat:
	python3 standalone/check_aspect_globals.py --original analysis/pcplus-install/PCPLUS.EXE
all: aspect-literal
test: test-aspect-literal
aspect-literal:
	python3 standalone/build_aspect_literal.py
test-aspect-literal:
	python3 standalone/check_aspect_literal.py
test-aspect-compat: test-aspect-literal
	python3 standalone/check_aspect_literal_native.py --require-host --output analysis/aspect-compiler/native-make-$$(date +%s%N)

.PHONY: config-abi test-config-abi test-directory test-ui-flow directory-browser test-directory-browser directory-editor test-directory-editor test-directory-replace test-directory-dos
.PHONY: test-keymap test-keymap-dos test-key-actions-dos test-keyboard-mapping-raw translation test-translation test-translation-dos

translation:
	python3 standalone/build_translation.py

.PHONY: xlt-editor test-xlt-editor
all: xlt-editor
test: test-xlt-editor
xlt-editor:
	python3 standalone/build_xlt_editor.py
test-xlt-editor: xlt-editor
	python3 standalone/test_xlt_editor_dos.py

.PHONY: keyboard-profiles test-keyboard-profiles
keyboard-profiles:
	python3 standalone/build_keyboard_profiles.py
test-keyboard-profiles: keyboard-profiles terminal
	python3 standalone/check_keyboard_profiles.py

.PHONY: test-resource-lookup
test-resource-lookup: terminal
	python3 standalone/test_resource_path_dos.py
	python3 standalone/check_resource_lookup.py
	python3 standalone/test_resource_lookup_dos.py

.PHONY: test-live-translation
test-live-translation: terminal setup
	python3 standalone/check_live_translation.py
	python3 standalone/test_live_translation_dos.py

.PHONY: test-redisplay
test-redisplay: terminal
	python3 standalone/check_redisplay_live.py
	python3 standalone/test_redisplay_dos.py
	python3 standalone/check_history_export_live.py
	python3 standalone/test_history_export_dos.py

test-translation: translation
	python3 standalone/check_translation.py

test-translation-dos:
	python3 standalone/check_xlt_dos.py

test: test-translation test-translation-dos

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

test-terminal: setup live-configuration

test-terminal: terminal
	python3 standalone/check_transfer_preferences_live.py
	python3 standalone/check_autostart_live.py
	python3 standalone/test_resource_path_dos.py
	python3 standalone/check_resource_lookup.py
	python3 standalone/test_resource_lookup_dos.py
	python3 standalone/check_translation_live.py
	python3 standalone/check_translation_modes.py
	python3 standalone/test_translation_live_dos.py
	python3 standalone/check_live_translation.py
	python3 standalone/test_live_translation_dos.py
	python3 standalone/check_setup_startup.py
	python3 standalone/test_setup_startup_dos.py
	python3 standalone/check_setup_live.py
	python3 standalone/check_live_setup_owner.py
	python3 standalone/check_live_setup_policy.py
	python3 standalone/check_live_setup_link.py
	python3 standalone/check_live_setup_profile.py
	python3 standalone/check_port_handoff.py
	python3 standalone/check_live_setup_port.py
	python3 standalone/test_setup_port_dos.py
	python3 standalone/check_live_setup_apply.py
	python3 standalone/test_setup_live_dos.py
	python3 standalone/check_config_far_live.py
	python3 standalone/check_live_configuration.py --terminal
	python3 standalone/check_modem_far_live.py
	python3 standalone/check_terminal_break_live.py
	python3 standalone/check_ui_screen_far.py
	python3 standalone/check_far_code_live.py
	python3 standalone/check_terminal_print_controller_live.py
	python3 standalone/check_terminal_screen_print_live.py
	python3 standalone/check_terminal_printer_live.py
	python3 standalone/check_terminal_monitor_live.py
	python3 standalone/check_terminal_snapshot_live.py
	python3 standalone/check_terminal_capture_live.py
	python3 standalone/check_redisplay_live.py
	python3 standalone/test_redisplay_dos.py
	python3 standalone/check_history_export_live.py
	python3 standalone/test_history_export_dos.py
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
	python3 standalone/check_directory_context.py
	python3 standalone/test_directory_context_terminal.py
	python3 standalone/check_directory_actions.py
	python3 standalone/test_terminal_config.py
	python3 standalone/test_connection_dos.py
	python3 standalone/test_directory_terminal.py
	python3 standalone/check_clipboard.py
	python3 standalone/test_clipboard_dos.py
	python3 standalone/check_clipboard_live.py
	python3 standalone/test_clipboard_live_dos.py
	python3 standalone/check_clipboard_settings.py
	python3 standalone/test_clipboard_settings_dos.py

test-bbs-modem:
	python3 lab/bbs/check_editor_recipes.py
	python3 lab/bbs/check_modem.py
	python3 lab/bbs/check_packetization.py

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
	rm -rf build/directory-context build/live-configuration build/setup-startup build/setup build/setup-model build/standalone build/ansi build/keyboard build/keyboard-mapping build/keyboard-detection build/keyboard-detection-dos build/line-edit build/keymap-dos build/terminal-keys build/csi-relocation build/cursor-state build/cursor-shape build/config-dos build/config-replace build/config-abi build/ui-windows build/ui-windows-dos build/modem-commands build/modem-commands-dos build/modem-responses build/modem-responses-dos build/modem-send build/modem-send-dos build/modem-import build/connection-dos build/directory-dial build/directory-dial-dos build/directory-accounting build/directory-accounting-dos build/directory-browser build/directory-browser-dos build/directory-editor build/directory-replace build/directory-dos build/directory-terminal build/terminal build/terminal-tests build/terminal-options build/process build/download-file build/transfer-send build/transfer-metadata build/transfer-metadata-dos build/batch-header build/batch-download build/batch-upload build/transfer-files build/transfer-session build/transfer-session-composite build/transfer-storage build/transfer-uart $(addprefix build/,$(MODULES))

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
.PHONY: test-capture-owners snapshot test-snapshot
.PHONY: printer test-printer
.PHONY: print-screen test-print-screen test-printer-device
.PHONY: print-controller test-print-controller
all: print-controller
test: test-print-controller
print-controller:
	python3 standalone/build_print_controller.py
test-print-controller: print-controller
	python3 standalone/check_print_controller.py
	python3 standalone/test_print_controller_dos.py
all: print-screen
test: test-print-screen test-printer-device
print-screen:
	python3 standalone/build_print_screen.py
test-print-screen: print-screen
	python3 standalone/check_print_screen.py
test-printer-device:
	python3 standalone/check_printer_device.py
.PHONY: monitor test-monitor test-monitor-file
all: monitor
test: test-monitor test-monitor-file
monitor:
	python3 standalone/build_monitor.py
test-monitor: monitor
	python3 standalone/check_monitor.py
	python3 standalone/test_monitor_dos.py
test-monitor-file:
	python3 standalone/check_monitor_file.py
all: printer
test: test-printer
printer:
	python3 standalone/build_printer.py
test-printer: printer
	python3 standalone/check_printer.py
	python3 standalone/test_printer_dos.py
all: snapshot
test: test-capture-owners test-snapshot
snapshot:
	python3 standalone/build_snapshot.py
test-snapshot: snapshot
	python3 standalone/check_snapshot.py
	python3 standalone/test_snapshot_dos.py
test-capture-owners:
	python3 standalone/check_capture_owners.py
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

.PHONY: test-ymodem-far
test-ymodem-far: terminal
	python3 standalone/check_config_far_live.py
	python3 standalone/check_ymodem_far_live.py

.PHONY: test-zmodem-wire
test: test-zmodem-wire
test-zmodem-wire:
	python3 standalone/check_zmodem_wire.py

.PHONY: test-zmodem-autostart
test: test-zmodem-autostart
test-zmodem-autostart:
	python3 standalone/check_zmodem_autostart.py

.PHONY: test-zmodem
test: test-zmodem
test-zmodem: test-zmodem-wire test-zmodem-autostart
	python3 standalone/check_zmodem_window.py
	python3 standalone/check_zmodem.py
	python3 standalone/test_zmodem_dos.py

.PHONY: test-terminal-zmodem-live
test-terminal: test-terminal-zmodem-live
test-terminal-zmodem-live: terminal
	python3 standalone/check_terminal_zmodem_live.py

.PHONY: test-zmodem-owners-live
test: test-zmodem-owners-live
test-zmodem-owners-live: terminal
	python3 standalone/check_zmodem_owners_live.py

.PHONY: setup test-setup
all: setup
test: test-setup
setup:
	python3 standalone/build_setup.py
test-setup: setup
	python3 standalone/check_setup_model.py
	python3 standalone/test_setup_dos.py
	python3 standalone/test_transfer_settings_dos.py

.PHONY: test-setup-startup
test-setup-startup: terminal setup
	python3 standalone/check_setup_startup.py
	python3 standalone/test_setup_startup_dos.py

.PHONY: live-configuration test-live-configuration
all: live-configuration
test: test-live-configuration
live-configuration:
	python3 standalone/build_live_configuration.py
test-live-configuration: live-configuration terminal
	python3 standalone/check_live_configuration.py
	python3 standalone/check_live_configuration.py --terminal

.PHONY: directory-context test-directory-context
all: directory-context
test: test-directory-context
directory-context:
	python3 standalone/build_directory_context.py
test-directory-context: terminal directory-context
	python3 standalone/check_directory_context.py
	python3 standalone/test_directory_context_dos.py
	python3 standalone/test_directory_context_terminal.py

.PHONY: clipboard test-clipboard test-clipboard-original
clipboard:
	python3 standalone/build_clipboard.py
test-clipboard: clipboard
	python3 standalone/check_clipboard.py
	python3 standalone/test_clipboard_dos.py
test-clipboard-original: clipboard
	python3 standalone/check_clipboard.py --original
all: clipboard
test: test-clipboard
test-terminal: clipboard

.PHONY: test-clipboard-settings
test-clipboard-settings: terminal setup
	python3 standalone/check_clipboard_settings.py
	python3 standalone/test_clipboard_settings_dos.py

# Run against the explicitly frozen existing terminal; each run owns fresh files.
.PHONY: test-clipboard-transfers
test-clipboard-transfers:
	python3 standalone/test_clipboard_transfer_dos.py --label "prompts-$$(date -u +%Y%m%dT%H%M%S%N)" --sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)"

.PHONY: test-command-menu
test-command-menu: terminal setup
	python3 standalone/check_command_menu_live.py
	python3 standalone/check_menu_pending_live.py
	python3 standalone/test_command_menu_dos.py --label "menu-$$(date -u +%Y%m%dT%H%M%S%N)" --sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)"

.PHONY: test-translation-reload
test-translation-reload: terminal setup
	python3 standalone/check_translation_reload_live.py
	python3 standalone/test_translation_reload_dos.py --label "reload-$$(date -u +%Y%m%dT%H%M%S%N)" --sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)"

.PHONY: test-translation-edit
test: test-translation-edit
test-translation-edit: terminal xlt-editor setup
	python3 standalone/check_translation_edit_live.py
	python3 standalone/test_translation_edit_dos.py --label "edit-$$(date -u +%Y%m%dT%H%M%S%N)" --sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)"
