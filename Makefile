.DEFAULT_GOAL := all
.PHONY: attribute-repair test-attribute-repair
.PHONY: test-zmodem-names
test-zmodem-names:
	python3 standalone/check_zmodem_names.py
test: test-zmodem-names
attribute-repair:
	python3 standalone/build_attribute_repair.py
test-attribute-repair: attribute-repair
	python3 standalone/check_attribute_repair.py
all: attribute-repair
test: test-attribute-repair
.PHONY: test-attribute-repair-live
test-attribute-repair-live: terminal attribute-repair
	python3 standalone/check_attribute_repair_live.py
test: test-attribute-repair-live

.PHONY: attribute-boundary test-attribute-boundary
attribute-boundary:
	python3 standalone/build_attribute_boundary.py
test-attribute-boundary: attribute-boundary
	python3 standalone/check_attribute_boundary.py
all: attribute-boundary
test: test-attribute-boundary
.PHONY: keyboard-reverse-tab test-keyboard-reverse-tab
keyboard-reverse-tab:
	python3 standalone/build_keyboard_reverse_tab.py
test-keyboard-reverse-tab: keyboard-reverse-tab
	python3 standalone/check_keyboard_reverse_tab.py
all: keyboard-reverse-tab
test: test-keyboard-reverse-tab
.PHONY: status-helpers test-status-helpers test-status-helpers-compat status-renderer test-status-renderer
all: status-helpers status-renderer
status-helpers:
	python3 standalone/build_status_helpers.py
test-status-helpers: status-helpers
	python3 standalone/check_status_helpers.py
test-status-helpers-compat: status-helpers
	python3 standalone/check_status_helpers.py --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
status-renderer:
	python3 standalone/build_status_renderer.py
test-status-renderer: status-renderer
	python3 standalone/check_status_renderer.py
test: test-status-helpers test-status-renderer
.PHONY: test-status-live
test-status-live: terminal
	python3 standalone/check_status_live.py
.PHONY: aspect-set test-aspect-set test-aspect-set-compat
.PHONY: aspect-paths test-aspect-paths test-aspect-path-compiler
.PHONY: aspect-script-files test-aspect-script-files
.PHONY: test-aspect-script-file-compiler
test: test-aspect-script-file-compiler
test-aspect-script-file-compiler:
	python3 standalone/check_aspect_script_file_compiler.py
.PHONY: aspect-script-file-backend test-aspect-script-file-backend
all: aspect-script-file-backend
test: test-aspect-script-file-backend
aspect-script-file-backend:
	python3 standalone/build_aspect_script_file_backend.py
test-aspect-script-file-backend:
	python3 standalone/check_aspect_script_file_backend.py
all: aspect-script-files
test: test-aspect-script-files
aspect-script-files:
	python3 standalone/build_aspect_script_files.py
test-aspect-script-files: aspect-script-files
	python3 standalone/check_aspect_script_files.py
all: aspect-paths
test: test-aspect-paths test-aspect-path-compiler
aspect-paths:
	python3 standalone/build_aspect_paths.py
test-aspect-paths: aspect-paths
	python3 standalone/check_aspect_paths.py
test-aspect-path-compiler:
	python3 standalone/check_aspect_path_compiler.py
all: aspect-set
aspect-set:
	python3 standalone/build_aspect_set.py
test-aspect-set: aspect-set
	python3 standalone/check_aspect_set.py
test-aspect-set-compat: aspect-set
	python3 standalone/check_aspect_set.py --original analysis/pcplus-originals/PCPLUS-main-2.01.EXE
test: test-aspect-set
.PHONY: aspect-txpace test-aspect-txpace
aspect-txpace:
	python3 standalone/build_aspect_txpace.py
test-aspect-txpace: aspect-txpace
	python3 standalone/check_aspect_txpace.py
all: aspect-txpace
test: test-aspect-txpace
.PHONY: aspect-find-case test-aspect-find-case
aspect-find-case:
	python3 standalone/build_aspect_find_case.py
test-aspect-find-case: aspect-find-case
	python3 standalone/check_aspect_find_case.py
all: aspect-find-case
test: test-aspect-find-case
.PHONY: aspect-find-owner test-aspect-find-owner test-aspect-find-case-compiler
aspect-find-owner:
	python3 standalone/build_aspect_find_owner.py
test-aspect-find-owner: aspect-find-owner
	python3 standalone/check_aspect_find_owner.py
test-aspect-find-case-compiler:
	python3 standalone/test_aspect_find_case_compiler.py
all: aspect-find-owner
test: test-aspect-find-owner test-aspect-find-case-compiler
.PHONY: aspect-when test-aspect-when aspect-renderer-policy test-aspect-renderer-policy
aspect-when:
	python3 standalone/build_aspect_when.py
test-aspect-when: aspect-when
	python3 standalone/check_aspect_when.py
.PHONY: test-aspect-local-window
test-aspect-local-window:
	python3 standalone/check_aspect_local_window.py
test: test-aspect-local-window
.PHONY: test-aspect-abort-confirm test-aspect-abort-confirm-original
test-aspect-abort-confirm:
	python3 standalone/check_aspect_abort_confirm.py
test-aspect-abort-confirm-original:
	python3 standalone/check_aspect_abort_confirm.py --original
test: test-aspect-abort-confirm
.PHONY: test-aspect-when-compiler
test-aspect-when-compiler: aspect-when
	python3 standalone/test_aspect_when_compiler.py --native
aspect-renderer-policy:
	python3 standalone/build_aspect_renderer_policy.py
test-aspect-renderer-policy: aspect-renderer-policy
	python3 standalone/check_aspect_renderer_policy.py
MODULES := escape attributes screen text reports erase cursor_state cursor_shape scroll modes render input_dispatch csi ui_windows modem_commands modem_responses modem_send directory_dial directory_accounting keyboard_mapping keyboard_detection line_edit meta_keys character_edit program_exec terminal_reset transfer_blocks transfer_receive transfer_send transfer_files transfer_session transfer_uart
.PHONY: aspect-resident-service test-aspect-resident-service test-aspect-resident-service-dos aspect-resident-bridge test-aspect-resident-bridge test-aspect-resident-bridge-dos test-aspect-serial-unread-dos
aspect-resident-service:
	python3 standalone/build_aspect_resident_service.py
test-aspect-resident-service: aspect-resident-service
	python3 standalone/check_aspect_resident_service.py
test-aspect-resident-service-dos: aspect-resident-service
	python3 standalone/test_aspect_resident_service_dos.py
aspect-resident-bridge:
	python3 standalone/build_aspect_resident_bridge.py
test-aspect-resident-bridge: aspect-resident-bridge
	python3 standalone/check_aspect_resident_bridge.py
test-aspect-resident-bridge-dos: aspect-resident-bridge
	python3 standalone/test_aspect_resident_bridge_dos.py
test-aspect-serial-unread-dos: aspect-serial
	python3 standalone/test_aspect_serial_unread_dos.py
.PHONY: all serial parser keyboard config-dos $(MODULES) $(addprefix test-,$(MODULES)) test test-driver test-parser test-keyboard test-config test-config-dos test-parser-compat test-csi-relocation test-modes-relocation test-input-relocation test-terminal-services compat test-compat test-modem clean

all: serial parser keyboard $(MODULES) config-dos config-replace config-abi directory-browser directory-editor process download-file upload-file transfer-metadata batch-header transfer-session-composite transfer-storage terminal


.PHONY: test-script-launch test-script-launch-dos
test: test-script-launch
test-script-launch: terminal
	python3 standalone/check_script_launch_live.py
test-script-launch-dos: terminal aspect-runner
	python3 standalone/test_script_launch_dos.py

.PHONY: aspect-runner test-aspect-runner aspect-console test-aspect-console test-aspect-console-compat package
all: aspect-runner aspect-console
test: test-aspect-runner test-aspect-console
aspect-runner:
	python3 standalone/build_aspect_runner.py
test-aspect-runner:
	python3 standalone/check_aspect_runner.py
aspect-console:
	python3 standalone/build_aspect_console.py
test-aspect-console:
	python3 standalone/check_aspect_console.py
test-aspect-console-compat:
	python3 standalone/check_aspect_console.py --original analysis/pcplus-install/PCPLUS.EXE
package:
	python3 standalone/package_dos.py

.PHONY: test-aspect-compiler
test: test-aspect-compiler test-aspect-set-compiler
test-aspect-compiler:
	python3 standalone/test_aspect_compiler.py
.PHONY: test-aspect-set-compiler
test-aspect-set-compiler:
	python3 standalone/test_aspect_set_compiler.py

.PHONY: aspect-conversions test-aspect-conversions test-aspect-conversions-compat aspect-conversion-services test-aspect-conversion-services test-aspect-conversion-services-compat
all: aspect-conversions aspect-conversion-services
test: test-aspect-conversions test-aspect-conversion-services
aspect-conversions:
	python3 standalone/build_aspect_conversions.py
test-aspect-conversions:
	python3 standalone/check_aspect_conversions.py
test-aspect-conversions-compat:
	python3 standalone/check_aspect_conversions.py --original analysis/pcplus-install/PCPLUS.EXE
aspect-conversion-services:
	python3 standalone/build_aspect_conversion_services.py
test-aspect-conversion-services: aspect-conversion-services
	python3 standalone/check_aspect_conversion_services.py
test-aspect-conversion-services-compat: aspect-conversion-services
	python3 standalone/check_aspect_conversion_services.py --original

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
	python3 standalone/check_recording_foreground_live.py
	python3 standalone/check_recording_tx_live.py
	python3 standalone/check_recording_rx_live.py
	python3 standalone/check_recording_ui_live.py
	python3 standalone/check_redisplay_live.py
	python3 standalone/test_redisplay_dos.py
	python3 standalone/check_history_export_live.py
	python3 standalone/test_history_export_dos.py
	python3 standalone/check_far_storage_live.py
	python3 standalone/test_far_storage_dos.py
	python3 standalone/check_terminal_transfer_live.py
	python3 standalone/check_terminal_upload_live.py
	python3 standalone/check_terminal_upload_cancel_boundary.py
	python3 standalone/check_terminal_upload_startup.py
	python3 standalone/check_transfer_ui_bank.py
	python3 standalone/check_upload_startup_restart.py --output build/terminal/terminal-upload-startup-restart.json
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
	python3 standalone/check_line_callbacks_live.py
	python3 standalone/check_line_controller_layout.py
	python3 standalone/check_line_attributes_live.py
	python3 standalone/check_terminal_options.py --binary build/terminal/TERMINAL.EXE --map build/terminal/terminal.map
	python3 lab/bbs/check_formfeed.py
	python3 lab/bbs/check_enigma_controls.py
	python3 standalone/check_terminal_ui.py
	python3 standalone/test_terminal.py
	python3 standalone/test_terminal_keys.py
	python3 standalone/check_terminal_config.py
	python3 standalone/check_startup_import.py --check-invalid-abi
	python3 standalone/check_connection.py
	python3 standalone/check_online_exit.py
	python3 standalone/check_analog_modem.py
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
.PHONY: test-capture-reservation
test: test-capture-reservation
test-capture-reservation:
	python3 standalone/check_capture_reservation.py --output build/aspect-recorder/reservation-make-$(shell date +%s%N)
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
	python3 standalone/check_zmodem_active_replay.py --output build/zmodem-active-replay/make-$$(date +%s%N)
	python3 standalone/test_download_compare_dos.py --output build/download-compare/make-$$(date +%s%N)
	python3 standalone/check_zmodem_completion_bounds.py
	python3 standalone/check_zmodem_link_policy.py
	python3 standalone/check_zmodem_receive_credit.py --output build/zmodem-receive-credit/make-$$(date +%s%N)
	python3 standalone/check_zmodem_window.py
	python3 standalone/check_zmodem.py
	python3 standalone/test_zmodem_dos.py

.PHONY: test-terminal-zmodem-live
test-terminal: test-terminal-zmodem-live
test-terminal-zmodem-live: terminal
	python3 standalone/check_terminal_zmodem_live.py
	python3 standalone/check_terminal_zmodem_receive_credit.py
	python3 standalone/check_terminal_zmodem_active_replay.py --output build/zmodem-active-replay/linked-make-$$(date +%s%N).json
	python3 standalone/check_zmodem_upload_timing.py
	python3 standalone/check_carrier_transfer_deadline.py
	python3 standalone/check_zmodem_completed_replay.py
	python3 standalone/check_terminal_zmodem_cancel.py
	python3 standalone/check_zmodem_name_ui.py

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

# Native serial commands and the source-owned DOS UART lease are distinct proofs.
.PHONY: aspect-serial-commands test-aspect-serial-commands test-aspect-serial-commands-compat aspect-serial test-aspect-serial test-aspect-serial-dos test-aspect-script-serial-dos test-aspect-serial-bbs
all: aspect-serial-commands aspect-serial
test: test-aspect-serial-commands test-aspect-serial
aspect-serial-commands:
	python3 standalone/build_aspect_serial_commands.py
test-aspect-serial-commands:
	python3 standalone/check_aspect_serial_commands.py
test-aspect-serial-commands-compat:
	python3 standalone/check_aspect_serial_commands.py --original analysis/pcplus-install/PCPLUS.EXE
aspect-serial:
	python3 standalone/build_aspect_serial.py
test-aspect-serial: aspect-serial
	python3 standalone/check_aspect_serial.py
test-aspect-serial-dos:
	python3 standalone/test_aspect_serial_dos.py
test-aspect-script-serial-dos:
	python3 standalone/test_aspect_script_serial_dos.py
test-aspect-serial-bbs:
	python3 standalone/test_aspect_serial_bbs.py

.PHONY: aspect-receive-commands test-aspect-receive-commands test-aspect-receive-commands-compat
all: aspect-receive-commands
test: test-aspect-receive-commands
aspect-receive-commands:
	python3 standalone/build_aspect_receive_commands.py
test-aspect-receive-commands:
	python3 standalone/check_aspect_receive_commands.py
test-aspect-receive-commands-compat:
	python3 standalone/check_aspect_receive_commands.py --original analysis/pcplus-install/PCPLUS.EXE

.PHONY: test-aspect-script-receive-dos
test-aspect-script-receive-dos:
	python3 standalone/test_aspect_script_receive_dos.py

.PHONY: aspect-receive-policy test-aspect-receive-policy test-aspect-receive-policy-compat test-aspect-script-translation-dos
all: aspect-receive-policy
test: test-aspect-receive-policy
aspect-receive-policy:
	python3 standalone/build_aspect_receive_policy.py
test-aspect-receive-policy:
	python3 standalone/check_aspect_receive_policy.py
test-aspect-receive-policy-compat:
	python3 standalone/check_aspect_receive_policy.py --original analysis/pcplus-install/PCPLUS.EXE
test-aspect-script-translation-dos:
	python3 standalone/test_aspect_script_translation_dos.py

.PHONY: aspect-directory test-aspect-directory test-aspect-directory-compat test-aspect-serial-preload-dos test-aspect-script-directory-dos
all: aspect-directory
test: test-aspect-directory
aspect-directory:
	python3 standalone/build_aspect_directory.py
test-aspect-directory: aspect-directory
	python3 standalone/check_aspect_directory.py
test-aspect-directory-compat:
	python3 standalone/check_aspect_directory.py --original analysis/pcplus-install/PCPLUS.EXE
test-aspect-serial-preload-dos:
	python3 standalone/test_aspect_serial_preload_dos.py
test-aspect-script-directory-dos:
	python3 standalone/test_aspect_script_directory_dos.py

.PHONY: test-aspect-txpace-linked
test-aspect-txpace-linked: aspect-runner
	python3 standalone/check_aspect_txpace_linked.py

# Recovered BREAK units remain separate from the maintained UART owner and UI.
.PHONY: aspect-break-native test-aspect-break-native test-aspect-break-compiler test-aspect-break-owner test-aspect-break-linked
all: aspect-break-native
test: test-aspect-break-native test-aspect-break-compiler test-aspect-break-owner
aspect-break-native:
	python3 standalone/build_aspect_break_native.py
test-aspect-break-native: aspect-break-native
	python3 standalone/check_aspect_break_native.py
test-aspect-break-compiler:
	python3 standalone/test_aspect_break_compiler.py
test-aspect-break-owner: aspect-serial
	python3 standalone/check_aspect_break_owner.py
test-aspect-break-linked: aspect-runner
	python3 standalone/check_aspect_break_linked.py

.PHONY: aspect-fetch-native test-aspect-fetch-native test-aspect-break-policy test-aspect-break-ui test-aspect-break-dos
all: aspect-fetch-native
test: test-aspect-fetch-native
aspect-fetch-native:
	python3 standalone/build_aspect_fetch_native.py
test-aspect-fetch-native: aspect-fetch-native
	python3 standalone/check_aspect_fetch_native.py
test-aspect-break-policy: aspect-runner
	python3 standalone/check_aspect_break_policy.py
test-aspect-break-ui: terminal
	python3 standalone/check_aspect_break_ui.py
test-aspect-break-dos: terminal aspect-runner
	python3 standalone/test_aspect_break_dos.py --label "break-$$(date -u +%Y%m%dT%H%M%S%N)" --terminal-sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)" --runner-sha256 "$$(sha256sum build/aspect-runner/ASPECT.EXE | cut -d' ' -f1)"

.PHONY: aspect-chain-native test-aspect-chain-native test-aspect-chain-compiler aspect-end-wait-native test-aspect-end-wait-native test-aspect-script-path test-aspect-chain-runtime test-aspect-chain-serial-dos
all: aspect-chain-native aspect-end-wait-native
test: test-aspect-chain-native test-aspect-chain-compiler test-aspect-end-wait-native test-aspect-script-path
aspect-chain-native:
	python3 standalone/build_aspect_chain_native.py
test-aspect-chain-native: aspect-chain-native
	python3 standalone/check_aspect_chain_native.py
test-aspect-chain-compiler:
	python3 standalone/test_aspect_chain_compiler.py
aspect-end-wait-native:
	python3 standalone/build_aspect_end_wait_native.py
test-aspect-end-wait-native: aspect-end-wait-native
	python3 standalone/check_aspect_end_wait_native.py
test-aspect-script-path:
	python3 standalone/test_aspect_script_path.py
test-aspect-chain-runtime:
	python3 standalone/check_aspect_chain_runtime.py
test-aspect-chain-serial-dos: aspect-runner
	python3 standalone/check_aspect_chain_serial_dos.py

.PHONY: test-aspect-chain-status-dos
test-aspect-chain-status-dos: terminal aspect-runner
	python3 standalone/test_aspect_chain_status_dos.py --label "chain-$$(date -u +%Y%m%dT%H%M%S%N)" --terminal-sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)" --runner-sha256 "$$(sha256sum build/aspect-runner/ASPECT.EXE | cut -d' ' -f1)"

.PHONY: test-aspect-script-label-client test-aspect-script-label-parent
test: test-aspect-script-label-client test-aspect-script-label-parent
test-aspect-script-label-client: aspect-runner
	python3 standalone/check_aspect_script_label_client.py
test-aspect-script-label-parent: terminal
	python3 standalone/check_aspect_script_label_parent.py

.PHONY: aspect-compiler-lexer test-aspect-compiler-lexer aspect-compiler-unit test-aspect-compiler-unit aspect-compiler-expression test-aspect-compiler-expression
all: aspect-compiler-lexer aspect-compiler-unit aspect-compiler-expression
test: test-aspect-compiler-lexer test-aspect-compiler-unit test-aspect-compiler-expression
aspect-compiler-lexer:
	python3 standalone/build_aspect_compiler_lexer.py
test-aspect-compiler-lexer: aspect-compiler-lexer
	python3 standalone/check_aspect_compiler_lexer.py
aspect-compiler-unit:
	python3 standalone/build_aspect_compiler_unit.py
test-aspect-compiler-unit: aspect-compiler-unit
	python3 standalone/check_aspect_compiler_unit.py
aspect-compiler-expression:
	python3 standalone/build_aspect_compiler_expression.py
test-aspect-compiler-expression: aspect-compiler-expression
	python3 standalone/check_aspect_compiler_expression.py

.PHONY: aspect-compiler-dos test-aspect-compiler-dos
all: aspect-compiler-dos
test: test-aspect-compiler-dos
aspect-compiler-dos:
	python3 standalone/build_aspect_compiler_dos.py
test-aspect-compiler-dos: aspect-compiler-dos aspect-runner
	python3 standalone/check_aspect_compiler_dos.py


.PHONY: test-aspect-compiler-stack
test-aspect-compiler-stack: aspect-compiler-dos aspect-runner
	python3 standalone/check_aspect_compiler_stack.py --output "build/aspect-compiler-stack/guard-$$(date -u +%Y%m%dT%H%M%S%N)"

.PHONY: test-aspect-source-compile test-aspect-source-serial-dos test-aspect-compile-flow-dos
test-aspect-source-compile: aspect-runner aspect-compiler-dos
	python3 standalone/check_aspect_source_compile.py
test-aspect-source-serial-dos: aspect-runner aspect-compiler-dos
	python3 standalone/check_aspect_source_serial_dos.py
test-aspect-compile-flow-dos:
	python3 standalone/test_aspect_compile_flow_dos.py
test: test-aspect-source-compile test-aspect-source-serial-dos test-aspect-compile-flow-dos

.PHONY: test-aspect-keyboard test-aspect-keyboard-policy
test-aspect-keyboard: aspect-runner
	python3 standalone/check_aspect_keyboard.py
test: test-aspect-keyboard
test-aspect-keyboard-policy: aspect-runner
	python3 standalone/check_aspect_keyboard_policy.py
test: test-aspect-keyboard-policy

.PHONY: test-terminal-key-output test-aspect-key-client test-keyboard-echo-native
.PHONY: test-terminal-script-window test-aspect-script-window-dos
test-terminal-script-window: terminal terminal-mouse
	python3 standalone/check_terminal_script_window.py
	python3 standalone/check_terminal_script_window.py --mouse
	python3 standalone/check_terminal_cooperative_window.py
	python3 standalone/check_terminal_cooperative_window.py --mouse
test-aspect-script-window-dos: terminal aspect-runner
	python3 standalone/test_aspect_script_window_dos.py --label "window-$$(date -u +%Y%m%dT%H%M%S%N)" --terminal-sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)" --runner-sha256 "$$(sha256sum build/aspect-runner/ASPECT.EXE | cut -d' ' -f1)"
test: test-terminal-script-window
test-terminal-key-output: terminal
	python3 standalone/check_terminal_key_output.py
	python3 standalone/check_terminal_key_edit.py
	python3 standalone/check_terminal_reverse_tab.py
test-aspect-key-client: aspect-runner
	python3 standalone/check_aspect_key_client.py
.PHONY: test-aspect-foreground-delay test-aspect-pause-dos
test-aspect-foreground-delay: aspect-runner
	python3 standalone/check_aspect_foreground_delay.py
.PHONY: test-aspect-abort-owner test-terminal-abort-owner test-aspect-abort-dos
test-aspect-abort-owner: aspect-runner
	python3 standalone/check_aspect_abort_owner.py
test-terminal-abort-owner: terminal terminal-mouse
	python3 standalone/check_terminal_abort_confirm.py
	python3 standalone/check_terminal_abort_confirm.py --mouse
test: test-aspect-abort-owner test-terminal-abort-owner
test-aspect-abort-dos: terminal aspect-runner
	python3 standalone/test_aspect_abort_confirm_dos.py --label "confirm-$$(date -u +%Y%m%dT%H%M%S%N)" --terminal-sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)" --runner-sha256 "$$(sha256sum build/aspect-runner/ASPECT.EXE | cut -d' ' -f1)"
	python3 standalone/test_aspect_abort_yes_dos.py --label "confirm-yes-$$(date -u +%Y%m%dT%H%M%S%N)" --terminal-sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)" --runner-sha256 "$$(sha256sum build/aspect-runner/ASPECT.EXE | cut -d' ' -f1)"
	python3 standalone/test_aspect_abort_events_dos.py --label "confirm-events-$$(date -u +%Y%m%dT%H%M%S%N)" --terminal-sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)" --runner-sha256 "$$(sha256sum build/aspect-runner/ASPECT.EXE | cut -d' ' -f1)"
	python3 standalone/test_aspect_abort_pressure_dos.py --label "confirm-load-$$(date -u +%Y%m%dT%H%M%S%N)" --terminal-sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)" --runner-sha256 "$$(sha256sum build/aspect-runner/ASPECT.EXE | cut -d' ' -f1)"
test: test-aspect-foreground-delay
test-aspect-pause-dos: terminal aspect-runner
	python3 standalone/test_aspect_window_pause_query_dos.py --label "pause-$$(date -u +%Y%m%dT%H%M%S%N)" --terminal-sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)" --runner-sha256 "$$(sha256sum build/aspect-runner/ASPECT.EXE | cut -d' ' -f1)"
	python3 standalone/test_aspect_pause_when_dos.py --label "pause-when-$$(date -u +%Y%m%dT%H%M%S%N)" --terminal-sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)" --runner-sha256 "$$(sha256sum build/aspect-runner/ASPECT.EXE | cut -d' ' -f1)"
	python3 standalone/test_aspect_pause_cancel_dos.py --label "pause-cancel-$$(date -u +%Y%m%dT%H%M%S%N)" --terminal-sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)" --runner-sha256 "$$(sha256sum build/aspect-runner/ASPECT.EXE | cut -d' ' -f1)"
	python3 standalone/test_aspect_window_pressure_dos.py --during-pause --label "pause-load-$$(date -u +%Y%m%dT%H%M%S%N)" --terminal-sha256 "$$(sha256sum build/terminal/TERMINAL.EXE | cut -d' ' -f1)" --runner-sha256 "$$(sha256sum build/aspect-runner/ASPECT.EXE | cut -d' ' -f1)"
test-keyboard-echo-native: keyboard_mapping
	python3 standalone/check_keyboard_echo_native.py
test: test-terminal-key-output test-aspect-key-client test-keyboard-echo-native

.PHONY: aspect-file-info test-aspect-file-info test-aspect-file-info-compiler
aspect-file-info:
	python3 standalone/build_aspect_file_info.py
test-aspect-file-info: aspect-file-info
	python3 standalone/check_aspect_file_info.py
test-aspect-file-info-compiler:
	python3 standalone/check_aspect_file_info_compiler.py
all: aspect-file-info
test: test-aspect-file-info test-aspect-file-info-compiler

.PHONY: aspect-enumeration test-aspect-enumeration test-aspect-enumeration-compiler
aspect-enumeration:
	python3 standalone/build_aspect_enumeration.py
test-aspect-enumeration: aspect-enumeration
	python3 standalone/check_aspect_enumeration.py
test-aspect-enumeration-compiler:
	python3 standalone/check_aspect_enumeration_compiler.py
all: aspect-enumeration
test: test-aspect-enumeration test-aspect-enumeration-compiler

.PHONY: aspect-file-attributes test-aspect-file-attributes test-aspect-file-attributes-compiler
aspect-file-attributes:
	python3 standalone/build_aspect_file_attributes.py
test-aspect-file-attributes: aspect-file-attributes
	python3 standalone/check_aspect_file_attributes.py
test-aspect-file-attributes-compiler:
	python3 standalone/check_aspect_file_attributes_compiler.py
all: aspect-file-attributes
test: test-aspect-file-attributes test-aspect-file-attributes-compiler

.PHONY: aspect-file-times test-aspect-file-times test-aspect-file-times-compiler
aspect-file-times:
	python3 standalone/build_aspect_file_times.py
test-aspect-file-times: aspect-file-times
	python3 standalone/check_aspect_file_times.py
test-aspect-file-times-compiler:
	python3 standalone/check_aspect_file_times_compiler.py
all: aspect-file-times
test: test-aspect-file-times test-aspect-file-times-compiler

.PHONY: aspect-system-query test-aspect-system-query test-aspect-system-query-compiler
aspect-system-query:
	python3 standalone/build_aspect_system_query.py
test-aspect-system-query: aspect-system-query
	python3 standalone/check_aspect_system_query.py
test-aspect-system-query-compiler:
	python3 standalone/check_aspect_system_query_compiler.py
all: aspect-system-query
test: test-aspect-system-query test-aspect-system-query-compiler

.PHONY: aspect-environment test-aspect-environment test-aspect-environment-compiler
aspect-environment:
	python3 standalone/build_aspect_environment.py
test-aspect-environment: aspect-environment
	python3 standalone/check_aspect_environment.py
test-aspect-environment-compiler:
	python3 standalone/check_aspect_environment_compiler.py
all: aspect-environment
test: test-aspect-environment test-aspect-environment-compiler

.PHONY: aspect-external test-aspect-external test-aspect-external-compiler
aspect-external:
	python3 standalone/build_aspect_external.py
test-aspect-external: aspect-external
	python3 standalone/check_aspect_external.py
test-aspect-external-compiler:
	python3 standalone/check_aspect_external_compiler.py
all: aspect-external
test: test-aspect-external test-aspect-external-compiler

# Component-only process foundation; no ASPECT runtime slots are published.
.PHONY: native-process test-native-process
native-process:
	python3 standalone/build_native_process.py
test-native-process: native-process
	python3 standalone/test_native_process_dos.py
	python3 standalone/test_native_process_dos.py --namespace

.PHONY: native-display test-native-display program-break test-program-break test-program-break-source test-program-break-original
program-break:
	python3 standalone/build_program_break.py
test-program-break: program-break
	python3 standalone/check_program_break.py
	python3 standalone/test_program_break_dos.py
test-program-break-source: program-break
	python3 standalone/check_program_break_source.py
test-program-break-original: program-break
	python3 standalone/check_program_break.py --original

.PHONY: break-owner test-break-owner test-break-owner-source
break-owner:
	python3 standalone/build_break_owner.py
test-break-owner: break-owner
	python3 standalone/check_break_owner.py
	python3 standalone/test_break_owner_dos.py
test-break-owner-source: break-owner
	python3 standalone/check_break_owner_source.py

.PHONY: break-owner-far test-break-owner-far test-break-owner-far-source
break-owner-far:
	python3 standalone/build_break_owner.py --banked
test-break-owner-far: break-owner-far
	python3 standalone/check_break_owner.py --banked
	python3 standalone/test_break_owner_dos.py --banked
test-break-owner-far-source: break-owner-far
	python3 standalone/check_break_owner_source.py --banked

.PHONY: aspect-banked test-aspect-banked test-aspect-banked-source
aspect-banked:
	python3 standalone/build_aspect_process.py --fault-diagnostic --break-owner
	python3 standalone/build_terminal.py --external-render
test-aspect-banked: aspect-banked
	python3 standalone/check_process_banks.py
	python3 standalone/test_aspect_unwind_dos.py --break-owner --kind D --kind A --kind F --kind L --control
	python3 standalone/test_aspect_unwind_dos.py --break-owner --phase 9 --phase 21 --kind D --port 2 --flow B
	python3 standalone/test_aspect_unwind_dos.py --break-owner --phase 6 --kind D --port 1 --flow S
	python3 standalone/test_aspect_unwind_dos.py --break-owner --phase 10 --kind D --port 2 --flow N
test-aspect-banked-source: aspect-banked
	python3 standalone/check_aspect_banked_source.py

.PHONY: native-program-far test-native-program-far test-native-program-far-source
native-program-far:
	python3 standalone/build_program_far.py
test-native-program-far: native-program-far
	python3 standalone/test_native_program_dos.py --break-owner --banked
test-native-program-far-source: native-program-far
	python3 standalone/check_native_program_source.py --break-owner --banked

.PHONY: exit-owner test-exit-owner aspect-exit-probe test-aspect-exit-probe aspect-banked-cli test-aspect-banked-cli test-exit-source
exit-owner:
	python3 standalone/build_exit_owner.py
test-exit-owner: exit-owner
	python3 standalone/check_exit_owner.py
	python3 standalone/test_exit_owner_dos.py
aspect-exit-probe:
	python3 standalone/build_aspect_exit_probe.py
test-aspect-exit-probe: exit-owner aspect-exit-probe
	python3 standalone/test_exit_owner_dos.py --aspect
aspect-banked-cli:
	python3 standalone/build_aspect_process.py --parent-render --break-owner
	python3 standalone/build_terminal.py --external-render
test-aspect-banked-cli: aspect-banked-cli aspect-compiler-dos
	python3 standalone/test_aspect_parent_process_dos.py --break-owner
test-exit-source: exit-owner aspect-exit-probe aspect-banked-cli aspect-banked aspect-compiler-dos
	python3 standalone/check_exit_source.py

.PHONY: aspect-parent-exit test-aspect-parent-exit test-aspect-parent-exit-source
aspect-parent-exit:
	python3 standalone/build_aspect_exit_probe.py --attached
	python3 standalone/build_terminal.py --external-render
test-aspect-parent-exit: aspect-parent-exit
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --exit-probe
test-aspect-parent-exit-source: aspect-parent-exit exit-owner aspect-exit-probe aspect-banked-cli aspect-banked aspect-compiler-dos terminal
	python3 standalone/check_exit_source.py --attached

.PHONY: test-aspect-parent-exit-mouse test-aspect-parent-exit-mouse-normal test-aspect-parent-exit-mouse-source
test-aspect-parent-exit-mouse: aspect-parent-exit terminal-mouse-process aspect-compiler-dos
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --exit-probe --mouse
test-aspect-parent-exit-mouse-normal: terminal-mouse-process aspect-banked-cli aspect-compiler-dos
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --mouse
test-aspect-parent-exit-mouse-source: aspect-parent-exit exit-owner aspect-exit-probe aspect-banked-cli aspect-banked aspect-compiler-dos terminal terminal-mouse terminal-mouse-process
	python3 standalone/check_exit_source.py --attached --mouse

.PHONY: aspect-parent-retry test-aspect-parent-retry test-aspect-parent-retry-mouse test-aspect-parent-retry-source
aspect-parent-retry:
	python3 standalone/build_aspect_exit_probe.py --attached --retry
test-aspect-parent-retry: aspect-parent-retry aspect-banked-cli aspect-compiler-dos
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --exit-probe --retry
test-aspect-parent-retry-mouse: aspect-parent-retry terminal-mouse-process aspect-compiler-dos
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --exit-probe --retry --mouse
test-aspect-parent-retry-source: aspect-parent-retry aspect-parent-exit exit-owner aspect-exit-probe aspect-banked-cli aspect-banked aspect-compiler-dos terminal terminal-mouse terminal-mouse-process
	python3 standalone/check_exit_source.py --attached --mouse --retry

.PHONY: terminal-exit test-terminal-exit test-terminal-exit-process test-terminal-exit-source
terminal-exit:
	python3 standalone/build_terminal_exit.py
test-terminal-exit: terminal-exit
	python3 standalone/check_terminal_exit.py
	python3 standalone/test_terminal_exit_dos.py
	python3 standalone/test_terminal_exit_dos.py --mouse
test-terminal-exit-process: terminal-exit aspect-banked-cli aspect-compiler-dos
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --terminal-exit-guard
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --terminal-exit-guard --mouse
test-terminal-exit-source: terminal-exit terminal terminal-mouse terminal-mouse-process
	python3 standalone/build_terminal.py --external-render
	python3 standalone/check_terminal_exit_source.py

.PHONY: terminal-process-bank test-terminal-process-bank test-terminal-process-bank-ui test-terminal-process-bank-exit test-terminal-process-bank-source
terminal-process-bank:
	python3 standalone/build_terminal_process_bank.py
test-terminal-process-bank: terminal-process-bank terminal-exit
	python3 standalone/check_terminal_process_bank.py
	python3 standalone/check_process.py --banked
	python3 standalone/test_process_dos.py --banked
	python3 standalone/test_program_process_dos.py --banked
test-terminal-process-bank-ui: terminal-process-bank aspect-banked-cli aspect-compiler-dos setup-mouse
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --terminal-exit-guard --process-bank
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --terminal-exit-guard --process-bank --mouse
	python3 standalone/test_terminal_mouse_dos.py --process-bank --case program --case quarantine --case startup-repair --case live-save
test-terminal-process-bank-exit: terminal-process-bank terminal-exit
	python3 standalone/check_terminal_exit.py
	python3 standalone/test_terminal_exit_dos.py --process-bank
	python3 standalone/test_terminal_exit_dos.py --process-bank --mouse
test-terminal-process-bank-source: terminal-process-bank terminal-exit terminal terminal-mouse terminal-mouse-process process
	python3 standalone/build_terminal.py --external-render
	python3 standalone/check_terminal_process_source.py

.PHONY: terminal-traps test-terminal-traps test-terminal-traps-ui test-terminal-traps-source test-terminal-traps-retry test-terminal-cancel
terminal-traps:
	python3 standalone/build_terminal_traps.py
test-terminal-traps: terminal-traps
	python3 standalone/check_terminal_traps.py
	python3 standalone/test_terminal_traps_dos.py
	python3 standalone/test_terminal_traps_dos.py --mouse
test-terminal-traps-ui: terminal-traps aspect-banked-cli aspect-compiler-dos setup-mouse
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --terminal-exit-guard --process-bank --traps
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --terminal-exit-guard --process-bank --traps --mouse
	python3 standalone/test_terminal_mouse_dos.py --process-bank --traps --case program --case quarantine --case startup-repair --case live-save
test-terminal-traps-source: terminal-traps terminal-process-bank terminal terminal-mouse terminal-mouse-process
	python3 standalone/build_terminal.py --external-render
	python3 standalone/check_terminal_traps_source.py
test-terminal-traps-retry: terminal-traps aspect-parent-retry aspect-compiler-dos
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --exit-probe --retry --terminal-exit-guard --process-bank --traps
	python3 standalone/test_aspect_parent_process_dos.py --break-owner --exit-probe --retry --terminal-exit-guard --process-bank --traps --mouse
test-terminal-cancel: terminal-traps
	python3 standalone/check_terminal_traps.py
	python3 standalone/test_terminal_cancel_dos.py
	python3 standalone/test_terminal_cancel_dos.py --mouse
	python3 standalone/test_terminal_cancel_script_wait.py
	python3 standalone/test_terminal_cancel_script_wait.py --mouse

.PHONY: test-kernel-critical
# Optional runtime lab: downloads a checksum-pinned FreeDOS distribution.
# No DOS image is an input to the ordinary application build or default tests.
test-kernel-critical: terminal-traps
	python3 standalone/test_kernel_critical_dos.py --operation create
	python3 standalone/test_kernel_critical_dos.py --operation append

.PHONY: native-program-break test-native-program-break test-native-program-break-source
native-program-break:
	python3 standalone/build_native_program.py --break-owner
test-native-program-break: native-program-break
	python3 standalone/test_native_program_dos.py --break-owner
test-native-program-break-source: native-program-break
	python3 standalone/check_native_program_source.py --break-owner

native-display:
	python3 standalone/build_native_display.py
test-native-display: native-display
	python3 standalone/check_native_display.py
	python3 standalone/test_native_display_dos.py

.PHONY: process-serial test-process-serial
process-serial:
	python3 standalone/build_process_serial.py
test-process-serial: process-serial
	python3 standalone/check_process_serial.py
	python3 standalone/check_process_serial_variants.py
	python3 standalone/test_process_serial_dos.py

# Composed component; application VM/renderer ownership is not published yet.
.PHONY: native-program test-native-program test-native-program-source
native-program:
	python3 standalone/build_native_program.py
test-native-program: native-program
	python3 standalone/check_native_program_admission.py
	python3 standalone/test_native_program_dos.py
test-native-program-source: native-program
	python3 standalone/check_native_program_source.py

# Experimental VM binding only; normal ASPECT remains105 slots.
.PHONY: aspect-process test-aspect-process test-aspect-process-source
aspect-process:
	python3 standalone/build_aspect_process.py
test-aspect-process:
	python3 standalone/test_aspect_process_dos.py
	python3 standalone/check_process_handles.py
	python3 standalone/check_aspect_process_policy.py
test-aspect-process-source:
	python3 standalone/check_aspect_process_source.py

.PHONY: aspect-parent-process test-aspect-parent-process test-aspect-parent-process-source
aspect-parent-process:
	python3 standalone/build_aspect_process.py --parent-render
	python3 standalone/build_terminal.py --external-render
test-aspect-parent-process: aspect-parent-process aspect-compiler-dos
	python3 standalone/test_aspect_parent_process_dos.py
	python3 standalone/check_aspect_parent_process.py
	python3 standalone/check_aspect_program_client.py
test-aspect-parent-process-source: aspect-parent-process aspect-runner aspect-compiler-dos terminal
	python3 standalone/check_aspect_parent_process_source.py

# Explicit experimental foreground recovery; never replaces normal products.
.PHONY: aspect-external-unwind test-aspect-external-unwind test-aspect-external-unwind-policy test-aspect-external-unwind-source
aspect-external-unwind: aspect-parent-process
	python3 standalone/build_aspect_process.py --fault-diagnostic
test-aspect-external-unwind: aspect-external-unwind
	python3 standalone/test_aspect_unwind_dos.py --kind D --kind A --kind F --kind L --control
	python3 standalone/test_aspect_unwind_dos.py --phase 9 --kind D --port 2 --flow B
	python3 standalone/test_aspect_unwind_dos.py --phase 6 --kind D --port 1 --flow S
	python3 standalone/test_aspect_unwind_dos.py --phase 10 --kind D --port 2 --flow N
test-aspect-external-unwind-policy:
	python3 -c 'import sys; sys.path.insert(0,"standalone"); import build_aspect_process as p; p.main(p.ROOT/"standalone/aspect_process_diagnostic.c")'
	python3 standalone/check_aspect_unwind_policy.py
	python3 standalone/check_process_handles.py
	python3 standalone/check_aspect_process_policy.py
test-aspect-external-unwind-source: aspect-external-unwind aspect-runner aspect-compiler-dos terminal
	python3 -c 'import sys; sys.path.insert(0,"standalone"); import build_aspect_process as p; p.main(p.ROOT/"standalone/aspect_process_diagnostic.c")'
	python3 standalone/check_aspect_unwind_source.py

.PHONY: native-mouse test-native-mouse test-native-mouse-source
native-mouse:
	python3 standalone/build_native_mouse.py
test-native-mouse: native-mouse
	python3 standalone/check_native_mouse.py
	python3 standalone/test_native_mouse_dos.py
test-native-mouse-source: native-mouse
	python3 standalone/check_native_mouse_source.py

.PHONY: mouse-keyboard test-mouse-keyboard test-mouse-keyboard-source
mouse-keyboard:
	python3 standalone/build_mouse_keyboard.py
test-mouse-keyboard: mouse-keyboard
	python3 standalone/check_mouse_keyboard.py
	python3 standalone/test_mouse_keyboard_dos.py
test-mouse-keyboard-source: mouse-keyboard
	python3 standalone/check_mouse_keyboard_source.py

.PHONY: mouse-keyboard-dos test-mouse-keyboard-dos test-mouse-keyboard-dos-source
mouse-keyboard-dos:
	python3 standalone/build_mouse_keyboard.py --dos-memory
test-mouse-keyboard-dos: mouse-keyboard-dos
	python3 standalone/check_mouse_keyboard.py --dos-memory
	python3 standalone/test_mouse_keyboard_dos.py --dos-memory
test-mouse-keyboard-dos-source: mouse-keyboard-dos
	python3 standalone/check_mouse_keyboard_source.py --dos-memory

.PHONY: mouse-bank test-mouse-bank test-mouse-bank-source
mouse-bank:
	python3 standalone/build_mouse_bank.py
test-mouse-bank: mouse-bank
	python3 standalone/check_mouse_keyboard.py --bank
	python3 standalone/test_mouse_keyboard_dos.py --bank
test-mouse-bank-source: mouse-bank
	python3 standalone/check_mouse_keyboard_source.py --bank

# Selectable terminal integration; preserve the normal application products.
.PHONY: setup-mouse test-setup-mouse terminal-mouse terminal-mouse-process test-terminal-mouse test-terminal-mouse-source test-terminal-mouse-unwind
setup-mouse:
	python3 standalone/build_setup.py --mouse
.PHONY: package-mouse test-package-mouse
package-mouse:
	python3 standalone/package_dos.py --mouse
test-package-mouse: package-mouse
	python3 standalone/test_package_mouse.py
test-setup-mouse: setup-mouse
	python3 standalone/check_setup_model.py --mouse
terminal-mouse: setup-mouse
	python3 standalone/build_terminal.py --mouse
	cp build/setup-mouse/PRMEDIT.EXE build/terminal-mouse/PRMEDIT.EXE
terminal-mouse-process: setup-mouse
	python3 standalone/build_terminal.py --mouse --external-render
	cp build/setup-mouse/PRMEDIT.EXE build/terminal-mouse-process/PRMEDIT.EXE
test-terminal-mouse: terminal-mouse
	python3 standalone/check_terminal_mouse.py
	python3 standalone/test_terminal_mouse_dos.py
test-terminal-mouse-source: terminal-mouse terminal-mouse-process setup aspect-external-unwind aspect-process aspect-runner aspect-compiler-dos terminal
	python3 -c 'import sys; sys.path.insert(0,"standalone"); import build_aspect_process as p; p.main(p.ROOT/"standalone/aspect_process_diagnostic.c")'
	python3 standalone/check_aspect_unwind_source.py --mouse
test-terminal-mouse-unwind: terminal-mouse-process aspect-external-unwind
	python3 standalone/test_aspect_unwind_dos.py --mouse --kind D --kind A --kind F --kind L --control
	python3 standalone/test_aspect_unwind_dos.py --mouse --phase 9 --kind D --port 2 --flow B
	python3 standalone/test_aspect_unwind_dos.py --mouse --phase 6 --kind D --port 1 --flow S
	python3 standalone/test_aspect_unwind_dos.py --mouse --phase 10 --kind D --port 2 --flow N

.PHONY: test-aspect-recorder
.PHONY: test-recording-file
test: test-recording-file
test-recording-file: aspect-runner aspect-compiler-dos
	python3 standalone/check_recording_file.py --output build/recording-file/host-make-$(shell date +%s%N)
	python3 standalone/test_recording_file_dos.py --output build/recording-file/DOS-make-$(shell date +%s%N)
	python3 standalone/test_recording_file_dos.py --banked --output build/recording-file/banked-DOS-make-$(shell date +%s%N)
	python3 standalone/test_recording_file_dos.py --banked --foreground --output build/recording-file/foreground-DOS-make-$(shell date +%s%N)
test: test-aspect-recorder
test-aspect-recorder: aspect-runner aspect-compiler-dos aspect-serial-commands
	python3 standalone/check_recorder_prompt_native.py --output build/aspect-recorder/prompt-native-make-$(shell date +%s%N)
	python3 standalone/check_aspect_recorder.py --output build/aspect-recorder/host-make-$(shell date +%s%N)
	python3 standalone/test_aspect_raw_output_dos.py --output build/aspect-recorder/raw-make-$(shell date +%s%N)
	python3 standalone/test_aspect_recorder_dos.py --output build/aspect-recorder/recorder-make-$(shell date +%s%N)
