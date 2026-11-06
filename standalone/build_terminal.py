#!/usr/bin/env python3
"""Build interactive DOS terminal from maintained and recovered source only."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from transfer.native_link import build_native_receiver
from transfer.native_sender_link import build_native_sender
from terminal_memory import inspect_terminal_memory
from omf_imports import rename_imports
ROOT=Path(__file__).resolve().parents[1]
import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,help='New isolated build directory under build/');parser.add_argument('--external-render',action='store_true');parser.add_argument('--mouse',action='store_true')
parser.add_argument('--file-directory',action='store_true',help='Serviced original-style Alt-F file listing; implies path control')
parser.add_argument('--external-viewer',action='store_true',help='Configured native-style external Alt-V parameter dialog and guarded COMSPEC handoff; requires session baseline')
parser.add_argument('--external-editor',action='store_true',help='Original Alt-A external editor using its separate PRM command; implies external viewer')
parser.add_argument('--packed-command-ui',action='store_true',help='Lossless bounded packing of authored command-browser text')
parser.add_argument('--optimize-size',action='store_true',help='Experimental reviewed per-source C size profile; stacks and capacities unchanged')
parser.add_argument('--code-label-offsets',action='store_true',help='Store same-bank command-label offsets and compact item metadata; requires packed original reference')
parser.add_argument('--chat-loader',action='store_true',help='Link the checked source-built Chat overlay loader; no foreground Chat binding yet')
parser.add_argument('--chat-storage',action='store_true',help='Exclusive frozen-storage lease for Chat; requires loader, reference and large frames; no foreground binding')
parser.add_argument('--chat-presentation',action='store_true',help='Select API0101 physical Chat module and matching checked loader; requires Chat storage; no foreground binding')
parser.add_argument('--chat-adapters',action='store_true',help='Link real TX/log/history Chat sink; requires presentation; entry/input hooks remain unbound')
parser.add_argument('--chat-text-transport',action='store_true',help='Link optional physical-completion TEXT TX sink; requires adapters; foreground TEXT remains unbound')
parser.add_argument('--chat-timing',action='store_true',help='Select matching API0103 loader/module with serviced TEXT timing; requires physical-TX adapter; shortcuts remain unbound')
parser.add_argument('--chat-echo',action='store_true',help='Experimental native echo scope/input service; requires timing/frontend; TEXT scheduling remains unbound')
parser.add_argument('--chat-redisplay',action='store_true',help='Opt-in Chat Alt-F6 storage lease and serviced Redisplay return; requires foreground TEXT')
parser.add_argument('--chat-foreground-text',action='store_true',help='Bind all ten direct Chat TEXT keys through module-owned scheduling; requires echo and compact labels')
parser.add_argument('--chat-frontend',action='store_true',help='Experimental Alt-O core and keyboard/RX/idle ownership; Help/direct TEXT remain refused; requires adapters')
parser.add_argument('--command-ui-pairs',type=int,choices=[0,64,128],default=64,help='Zero selects an uncompressed decoder control; requires packed UI')
parser.add_argument('--aspect-snapshot-lease',action='store_true',help='Opt-in capability17 retained screen storage for nested ASPECT PROGRAM')
parser.add_argument('--file-viewer',action='store_true',help='Serviced internal Alt-V viewer; requires the composed Gateway/large-frame parent')
parser.add_argument('--session-projection',action='store_true')
parser.add_argument('--projection-probe',action='store_true')
parser.add_argument('--session-baseline',action='store_true')
parser.add_argument('--register-handoff',action='store_true')
parser.add_argument('--session-controls',action='store_true')
parser.add_argument('--hook-return',action='store_true')
parser.add_argument('--hook-execute',action='store_true')
parser.add_argument('--hook-modem',action='store_true')
parser.add_argument('--hook-input',action='store_true')
parser.add_argument('--hook-apply',action='store_true')
parser.add_argument('--hook-lookup',action='store_true')
parser.add_argument('--custom-irq',action='store_true')
parser.add_argument('--special-edition',action='store_true',help='Show the magenta LoC Special Edition startup screen')
parser.add_argument('--status-geometry',action='store_true',help='Reserve physical row25 for status and advertise a coherent24-row terminal')
parser.add_argument('--reset-row-owner',action='store_true',help='Link staged RIS row-default component; no status/line key binding')
parser.add_argument('--status-owner',action='store_true',help='Link offline live status transaction; no key/menu binding or online size negotiation')
parser.add_argument('--row-notices',action='store_true',help='Bind connection notices to coherent dynamic status rows')
parser.add_argument('--session-rows-probe',type=int,choices=(25,28,43,50),help='Diagnostic only: establish canonical rows then run the normal serial session')
parser.add_argument('--aspect-admission-probe',action='store_true',help='Diagnostic only: ASPECT admission at each BIOS text height')
parser.add_argument('--aspect-row-owner',action='store_true',help='Admit coherent full-height narrow ASPECT renderer frames')
parser.add_argument('--xlt-display-probe',action='store_true',help='Diagnostic only: real XLTEDIT changes at each text height')
parser.add_argument('--profile-display-probe',action='store_true',help='Diagnostic only: real PRMEDIT profile changes at each text height')
parser.add_argument('--program-display-owner',action='store_true',help='Save and verify full-height PROGRAM display restoration around DOS children')
parser.add_argument('--large-view-frames',action='store_true',help='Retain50-row shared view frames and admit verified25/28/43/50-row geometry')
parser.add_argument('--status-control',action='store_true',help='Enable guarded offline Ctrl-] and menu status toggle at physical25 rows')
parser.add_argument('--status-probe',action='store_true',help='Diagnostic only: run offline status transactions at foreground startup, then exit')
parser.add_argument('--display-row-owner',action='store_true',help='Link namespaced low-level BIOS row bank; no canonical geometry or key binding')
parser.add_argument('--display-row-probe',action='store_true',help='Diagnostic only: exercise BIOS row bank at startup before UART enable, then exit')
parser.add_argument('--row-geometry-owner',action='store_true',help='Link offline BIOS/canonical/RIS commit and rollback owner; no key/menu binding')
parser.add_argument('--display-preferences',action='store_true',help='Capture raw saved display words after successful startup import; no BIOS or key binding')
parser.add_argument('--display-startup',action='store_true',help='Apply imported display preferences through the checked owner before UART enable')
parser.add_argument('--line-control',action='store_true',help='Enable guarded original Ctrl-minus/Toggle Lines using the accepted display selector')
parser.add_argument('--window-size-report',action='store_true',help='Reply to ordinary CSI18t with accepted logical text dimensions; no bridge deployment')
parser.add_argument('--keyboard-bank',action='store_true',help='Move the unchanged foreground keyboard dispatcher into a retained code bank')
parser.add_argument('--input-tables-data',action='store_true',help='Move two near input dispatch pointer tables from resident code into DGROUP')
parser.add_argument('--cwd-identities',action='store_true',help='Freeze startup selectors and XLT defaults; resolve PRMEDIT absolutely; no directory-change key')
parser.add_argument('--path-control',action='store_true',help='Serviced original Alt-F7 dialog and verified startup-directory restoration; implies cwd identities/reference')
parser.add_argument('--gateway-lookup',action='store_true',help='Link direct empty-tail COMSPEC policy; requires hook lookup, no Gateway key/menu binding')
parser.add_argument('--gateway-handles',action='store_true',help='Link retained private-JFT bracket; implies Gateway lookup/path-control, no foreground binding')
parser.add_argument('--gateway-files',action='store_true',help='Compose direct COMSPEC with private sink leases; no foreground key or serial policy')
parser.add_argument('--gateway-uart',action='store_true',help='Link retained live Gateway IRQ and IF0 return gate; no normal foreground binding')
parser.add_argument('--gateway',action='store_true',help='Enable guarded live DOS Gateway through Alt-F4 and command menu')
parser.add_argument('--gateway-uart-probe',action='store_true',help='Diagnostic only: application file probe with UART active and live IRQ across DOS EXEC')
parser.add_argument('--gateway-files-probe',choices=['normal','hold'],help='Diagnostic only: four open application files across direct COMSPEC before UART startup')
parser.add_argument('--gateway-probe',action='store_true',help='Diagnostic only: invoke direct COMSPEC before UART startup, record result, then exit')
parser.add_argument('--local-controls',action='store_true',help='Enable original Clear/Reset/Duplex through a guarded foreground owner')
parser.add_argument('--manual-init',action='store_true',help='Integrate guarded manual Init key/menu and exclusive foreground UART scheduling')
parser.add_argument('--manual-init-owner',action='store_true',help='Link isolated bounded send-only Init Modem owner; no keyboard/menu binding')
parser.add_argument('--auto-answer',action='store_true',help='Enable guarded Alt-Y/reference/browser with configured answer-on, notice and sound')
parser.add_argument('--auto-answer-owner',action='store_true',help='Link typed answer-on and acceptance-qualified echo component; no Alt-Y/UI binding')
parser.add_argument('--elapsed-view',action='store_true',help='Enable serviced original Alt-T/Alt-Z elapsed-time window; requires call timer and local controls')
parser.add_argument('--call-timer',action='store_true',help='Bind the recovered call timer to confirmed connection transitions; Alt-T view remains separate')
parser.add_argument('--screen-pause',action='store_true',help='Enable guarded original Alt-N Screen Pause semantics')
parser.add_argument('--original-keys',action='store_true',help='Restore original recorder/setup/history shortcuts and unmapped page-key transfers')
parser.add_argument('--original-reference',action='store_true',help='Original 39-command Alt-Z reference and guarded command refusals; implies --original-keys')
parser.add_argument('--directory-view',action='store_true',help='Serviced read-only Alt-D view; implies --original-reference; dialing adoption remains pending')
parser.add_argument('--directory-preview',action='store_true',help='Validate and preview an Alt-D selection; implies --directory-view; adoption remains pending')
parser.add_argument('--directory-storage',action='store_true',help='Shared directory persistence claims and EXEC recovery gate; implies --directory-preview')
parser.add_argument('--directory-resource-cli',action='store_true',help='Bind original CLI keyboard resource identities before directory startup; implies --directory-storage')
parser.add_argument('--directory-adopt',action='store_true',help='Preview A applies a staged selection through the foreground PROGRAM owner; implies --directory-compile')
parser.add_argument('--directory-compile',action='store_true',help='Explicit preview C compiles ASP without executing the script; implies --directory-scripts')
parser.add_argument('--directory-scripts',action='store_true',help='Resolve and fingerprint directory ASX/ASP resources; implies --directory-translation')
parser.add_argument('--directory-translation',action='store_true',help='Stage translation with KEY/KBD before selection adoption; implies --directory-retirement')
parser.add_argument('--directory-retirement',action='store_true',help='Save pending statistics through a quiesced PROGRAM owner after disconnect; implies --directory-resource-owner')
parser.add_argument('--directory-resource-owner',action='store_true',help='Quiesced KEY/KBD preflight from directory preview R; implies --directory-resource-cli')
parser.add_argument('--phone-log-bank',action='store_true',help='Link the checked logger code bank; event/startup integration remains disabled')
parser.add_argument('--phone-log-controls',action='store_true',help='Alt-Z File call-log status and confirmed safe retry; implies disk')
parser.add_argument('--phone-log-disk',action='store_true',help='Experimental guarded foreground append and shutdown drain; implies events')
parser.add_argument('--phone-log-events',action='store_true',help='Experimental RAM session hooks; implies lifecycle; no live disk scheduler yet')
parser.add_argument('--phone-log-lifecycle',action='store_true',help='Link the retained-event producer; implies startup/claims, transition hooks remain disabled')
parser.add_argument('--phone-log-startup',action='store_true',help='Configure the call-log queue from accepted settings before UART startup; requires --session-baseline')
parser.add_argument('--phone-log-reservations',action='store_true',help='Experimental logger queue with fixed file claims; implies --phone-log-bank')
parser.add_argument('--native-reset-bank',action='store_true',help='Link the experimental namespaced native bank; peer width ownership remains disabled')
parser.add_argument('--native-reset-static',action='store_true',help='Retain the larger static bank as a memory regression control')
parser.add_argument('--native-reset-transaction',action='store_true',help='Experimental checked live display transaction; peer requests remain disabled')
parser.add_argument('--input-probe',action='store_true')
parser.add_argument('--hook-probe',action='store_true')
parser.add_argument('--session-capture',action='store_true');parser.add_argument('--directory-keys',action='store_true');parser.add_argument('--aspect-keys',action='store_true');parser.add_argument('--notice-input',action='store_true');parser.add_argument('--notice-sound',action='store_true');parser.add_argument('--exit-guard',action='store_true');parser.add_argument('--exit-probe',type=int,choices=[0,1,2,3]);parser.add_argument('--process-bank',action='store_true');parser.add_argument('--traps',action='store_true');parser.add_argument('--trap-probe',type=int,choices=range(5));args=parser.parse_args()
assert args.command_ui_pairs==64 or args.packed_command_ui
if args.code_label_offsets:assert args.original_reference and args.packed_command_ui
if args.aspect_snapshot_lease:assert args.external_render and args.notice_input and args.large_view_frames
if args.chat_storage:assert args.chat_loader and args.original_reference and args.large_view_frames
if args.chat_presentation:assert args.chat_storage
if args.chat_adapters:assert args.chat_presentation
if args.chat_text_transport:assert args.chat_adapters and args.optimize_size
if args.chat_timing:assert args.chat_text_transport
if args.chat_echo:assert args.chat_timing and args.chat_frontend
if args.chat_foreground_text:assert args.chat_echo and args.code_label_offsets
if args.chat_redisplay:assert args.chat_foreground_text
if args.chat_frontend:assert args.chat_adapters and args.keyboard_bank
if args.external_editor:args.external_viewer=True
if args.external_viewer:
 args.file_viewer=True
 assert args.session_baseline,'External viewer requires the accepted PRM baseline'
if args.file_directory:args.path_control=True
if args.file_viewer:
 args.path_control=True
 assert args.gateway and args.large_view_frames,'File viewer requires composed Gateway/large-frame ownership'
if args.gateway:args.gateway_uart=True;assert args.program_display_owner and args.mouse,'Gateway frontend requires composed display/mouse owners'
if args.gateway_uart_probe:args.gateway_uart=True;args.gateway_files_probe='normal'
if args.gateway_uart:args.gateway_files=True
if args.gateway_uart:assert args.program_display_owner or args.directory_resource_owner,'Gateway UART requires the IF0 raw EXEC return gate'
if args.gateway_files_probe:args.gateway_files=True;args.gateway_probe=True
if args.gateway_files:args.gateway_handles=True
if args.gateway_handles:args.gateway_lookup=True;args.path_control=True
if args.gateway_probe:args.gateway_lookup=True;args.path_control=True
if args.gateway_lookup:assert args.hook_lookup,'Direct Gateway resolver requires the bounded HOOK_CODE DOS boundary'
if args.path_control:
 args.cwd_identities=True
 args.original_reference=True
if args.directory_adopt:
 assert args.hook_apply
 args.directory_compile=True
if args.directory_compile:args.directory_scripts=True
if args.directory_scripts:args.directory_translation=True
if args.directory_translation:args.directory_retirement=True
if args.directory_retirement:args.directory_resource_owner=True
if args.directory_resource_owner:args.directory_resource_cli=True
if args.directory_resource_owner:assert not args.native_reset_bank,'Frozen EXEC loans require the independent live ring; native reset overlay is a separate ownership variant'
if args.directory_resource_owner:assert args.mouse,'Frozen EXEC loans use the checked high mouse-state allocation policy'
if args.directory_resource_cli:args.directory_storage=True
if args.directory_storage:args.directory_preview=True
if args.directory_preview:
 args.directory_view=True
 assert args.session_baseline and args.session_capture
if args.directory_view:args.original_reference=True
if args.local_controls:assert args.original_reference,'Local controls require the original reference interface'
if args.status_owner:
 args.reset_row_owner=True
 assert args.native_reset_bank and args.screen_pause and args.elapsed_view and args.auto_answer,'Status transaction requires the current banked modal-owner candidate'
if args.xlt_display_probe:
 assert args.program_display_owner and not args.profile_display_probe,'XLT diagnostic requires PROGRAM owner and excludes profile diagnostic'
 args.display_row_probe=True
if args.profile_display_probe:
 assert args.program_display_owner,'Profile diagnostic requires the full-height PROGRAM owner'
 args.display_row_probe=True
if args.row_notices:assert args.row_geometry_owner and args.program_display_owner and args.status_owner,'Row notices require composed geometry/PROGRAM/status owners'
if args.session_rows_probe is not None:
 assert args.aspect_row_owner and not args.display_row_probe and not args.status_probe and not args.aspect_admission_probe and not args.profile_display_probe and not args.xlt_display_probe,'Session row diagnostic requires ASPECT rows and excludes startup probes'
if args.aspect_admission_probe:
 assert args.aspect_row_owner and not args.profile_display_probe and not args.xlt_display_probe,'ASPECT diagnostic requires row owner and excludes editor probes'
 args.display_row_probe=True
if args.aspect_row_owner:assert args.program_display_owner and args.external_render,'ASPECT rows require full-height PROGRAM and external renderer'
if args.program_display_owner:assert args.large_view_frames,'PROGRAM display owner requires full-height shared frames'
if args.large_view_frames:assert args.row_geometry_owner,'Large view frames require the canonical row geometry component'
if args.status_control:assert args.status_owner and args.local_controls,'Status control requires the tested status and local-control owners'
if args.status_probe:assert args.status_owner and not args.hook_probe and not args.input_probe and not args.projection_probe,'Status probe requires the isolated status-owner build'
if args.display_row_owner:assert args.status_owner,'Display row bank requires the current status-owner component'
if args.row_geometry_owner:assert args.display_row_owner,'Row geometry owner requires the verified BIOS row bank'
if args.display_preferences:assert args.row_geometry_owner,'Display preference capture requires the row geometry component'
if args.display_startup:
 assert args.display_preferences and args.aspect_row_owner and args.row_notices and args.status_control,'Display startup requires the composed display/frame/modal/status owners'
 assert args.session_rows_probe is None and not args.display_row_probe and not args.status_probe,'Saved display startup excludes competing geometry initializers'
if args.line_control:assert args.display_startup,'Toggle Lines requires the composed startup selector owner'
if args.window_size_report:assert args.display_preferences,'Window size report requires the canonical display component'
if args.display_row_probe:assert args.display_row_owner and not args.status_probe and not args.hook_probe and not args.input_probe and not args.projection_probe,'Display row probe requires the isolated row-bank build'
if args.reset_row_owner:assert args.status_geometry and args.local_controls,'Row-default component requires the reserved-row local-controls candidate'
if args.auto_answer:
 args.auto_answer_owner=True
 args.manual_init=True
 assert args.notice_sound and args.status_geometry,'Auto Answer requires the sound owner and reserved status row'
if args.auto_answer_owner:args.manual_init_owner=True
if args.manual_init:
 args.manual_init_owner=True
 assert args.local_controls,'Manual Init integration requires local controls'
if args.manual_init_owner:assert args.original_reference,'Manual Init owner requires original-reference candidate'
if args.elapsed_view:assert args.call_timer and args.local_controls,'Elapsed view requires call timer and local controls'
if args.call_timer:assert args.original_reference,'Call timer requires original-reference candidate'
if args.screen_pause:assert args.local_controls,'Screen Pause requires the shared local-controls owner'
if args.original_reference:args.original_keys=True
if args.phone_log_reservations:args.phone_log_bank=True
if args.phone_log_controls:args.phone_log_disk=True
if args.phone_log_disk:args.phone_log_events=True
if args.phone_log_events:args.phone_log_lifecycle=True
if args.phone_log_lifecycle:args.phone_log_startup=True
if args.phone_log_startup:
 args.phone_log_bank=True
 args.phone_log_reservations=True
 assert args.session_baseline
if args.session_capture:assert args.directory_keys and args.process_bank
if args.session_projection:assert args.session_capture
if args.projection_probe:assert args.session_projection
if args.session_baseline:assert args.session_projection
if args.register_handoff:assert args.session_baseline
if args.session_controls:assert args.session_baseline and args.mouse and args.notice_input and args.notice_sound
if args.hook_return:assert args.session_controls and args.register_handoff
if args.hook_execute:assert args.hook_return
if args.hook_modem:assert args.hook_execute
if args.hook_input:assert args.hook_modem
if args.hook_apply:assert args.hook_input
if args.hook_lookup:assert args.hook_apply
if args.custom_irq:assert args.register_handoff
if args.native_reset_static:assert args.native_reset_bank
if args.native_reset_transaction:assert args.native_reset_bank and not args.native_reset_static
if args.input_probe:assert args.hook_input and not args.hook_probe and not args.projection_probe
if args.hook_probe:assert args.hook_execute and not args.projection_probe
if args.exit_probe is not None:assert args.exit_guard
if args.process_bank:assert args.external_render
if args.traps:assert args.process_bank
if args.trap_probe is not None:assert args.traps and args.exit_probe is None
out_name='terminal-mouse-process' if args.external_render and args.mouse else 'terminal-mouse' if args.mouse else 'terminal-process' if args.external_render else 'terminal'
if args.exit_guard:out_name='terminal-exit-mouse' if args.mouse else 'terminal-exit'
if args.process_bank:out_name='terminal-process-bank-mouse' if args.mouse else 'terminal-process-bank'
if args.traps:out_name='terminal-traps-mouse' if args.mouse else 'terminal-traps'
if args.exit_probe is not None:out_name+='-probe-'+str(args.exit_probe)
if args.trap_probe is not None:out_name+='-probe-'+str(args.trap_probe)
if args.notice_sound:
 assert args.external_render
 out_name='terminal-mouse-notice-sound' if args.mouse else 'terminal-notice-sound'
if args.notice_input:
 assert args.notice_sound and args.mouse
 out_name='terminal-mouse-notice-input'
if args.aspect_keys:
 assert args.notice_input
 out_name='terminal-aspect-keys'
if args.directory_keys:
 assert args.aspect_keys
 out_name='terminal-directory-keys'
if args.process_bank and args.notice_sound:
 # Keep the established notice/KEY products intact while giving their near
 # callers and the upcoming far HOOK owner one shared banked EXEC boundary.
 out_name+='-process-bank'
if args.session_capture:out_name+='-session-capture'
if args.session_projection:out_name+='-projection'
if args.session_baseline:out_name+='-bound'
if args.register_handoff:out_name+='-registers'
if args.session_controls:out_name+='-controls'
if args.hook_return:out_name+='-return'
if args.hook_execute:out_name+='-execute'
if args.hook_modem:out_name+='-modem'
if args.hook_input:out_name+='-input'
if args.hook_apply:out_name+='-apply'
if args.hook_lookup:out_name+='-lookup'
if args.input_probe:out_name+='-inputprobe'
if args.hook_probe:out_name+='-hookprobe'
if args.projection_probe:out_name+='-probe'
if args.notice_sound and args.exit_guard:out_name+='-guarded'
if args.notice_sound and args.traps:out_name+='-traps'
if args.notice_sound and args.trap_probe is not None:out_name+='-probe-'+str(args.trap_probe)
if args.notice_sound and args.exit_probe is not None:out_name+='-exit-probe-'+str(args.exit_probe)
if args.custom_irq:out_name+='-custom-irq'
if args.special_edition:out_name+='-special'
if args.original_keys:out_name='terminal-original-keys-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
if args.original_reference:out_name='terminal-reference-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
if args.directory_view:out_name='terminal-directory-view-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
if args.directory_preview:out_name='terminal-directory-preview-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
if args.directory_storage:out_name='terminal-directory-storage-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
if args.directory_resource_cli:out_name='terminal-resource-cli-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
if args.directory_resource_owner:out_name='terminal-resource-owner-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
if args.directory_retirement:out_name='terminal-directory-retirement-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
if args.directory_translation:out_name='terminal-directory-translation-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
if args.directory_scripts:out_name='terminal-directory-scripts-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
if args.directory_compile:out_name='terminal-directory-compile-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
if args.directory_adopt:out_name='terminal-directory-adopt-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
if args.native_reset_bank:out_name+='-native-bank'
if args.native_reset_static:out_name+='-static'
if args.native_reset_transaction:out_name+='-transaction'
if args.phone_log_reservations:out_name+='-log-claims'
if args.phone_log_startup:out_name+='-log-startup'
if args.phone_log_lifecycle:out_name+='-log-lifecycle'
if args.phone_log_events:out_name+='-log-events'
if args.phone_log_disk:out_name+='-log-disk'
if args.phone_log_controls:out_name+='-log-controls'
if args.status_geometry:out_name+='-status-geometry'
if args.reset_row_owner:out_name+='-reset-rows'
if args.status_owner:out_name+='-status-owner'
if args.status_control:out_name+='-status-control'
if args.large_view_frames:out_name+='-large-view-frames'
if args.row_notices:out_name+='-row-notices'
if args.session_rows_probe is not None:out_name+='-session-rows-'+str(args.session_rows_probe)
if args.aspect_admission_probe:out_name+='-aspect-admission-probe'
if args.aspect_row_owner:out_name+='-aspect-row-owner'
if args.program_display_owner:out_name+='-program-display-owner'
if args.xlt_display_probe:out_name+='-xlt-display-probe'
if args.profile_display_probe:out_name+='-profile-display-probe'
if args.status_probe:out_name+='-status-probe'
if args.display_row_owner:out_name+='-display-row-owner'
if args.row_geometry_owner:out_name+='-row-geometry-owner'
if args.display_preferences:out_name+='-display-preferences'
if args.display_startup:out_name+='-display-startup'
if args.line_control:out_name+='-line-control'
if args.window_size_report:out_name+='-window-size-report'
if args.display_row_probe:out_name+='-display-row-probe'
if args.local_controls:out_name+='-local-controls'
if args.screen_pause:out_name+='-screen-pause'
if args.call_timer:out_name+='-call-timer'
if args.elapsed_view:out_name+='-elapsed-view'
if args.manual_init_owner:out_name+='-manual-init-owner'
if args.manual_init:out_name+='-manual-init'
if args.auto_answer_owner:out_name+='-auto-answer-owner'
if args.auto_answer:out_name+='-auto-answer'
if args.keyboard_bank:out_name+='-keyboard-bank'
if args.input_tables_data:out_name+='-input-tables-data'
if args.cwd_identities:out_name+='-cwd-identities'
if args.path_control:out_name+='-path-control'
if args.file_directory:out_name+='-file-directory'
if args.file_viewer:out_name+='-file-viewer'
if args.external_viewer:out_name+='-external-viewer'
if args.external_editor:out_name+='-external-editor'
if args.packed_command_ui:out_name+='-packed-ui'
if args.optimize_size:out_name+='-optimized-size'
if args.chat_loader:out_name+='-chat-loader'
if args.chat_storage:out_name+='-chat-storage'
if args.chat_presentation:out_name+='-chat-presentation'
if args.chat_adapters:out_name+='-chat-adapters'
if args.chat_text_transport:out_name+='-chat-text-transport'
if args.chat_timing:out_name+='-chat-timing'
if args.chat_echo:out_name+='-chat-echo'
if args.chat_foreground_text:out_name+='-foreground-text'
if args.chat_redisplay:out_name+='-chat-redisplay'
if args.code_label_offsets:out_name+='-code-label-offsets'
if args.chat_frontend:out_name+='-chat-frontend'
if args.command_ui_pairs==0:out_name+='-control'
if args.gateway_lookup:out_name+='-gateway-lookup'
if args.gateway_handles:out_name+='-gateway-handles'
if args.gateway_files:out_name+='-gateway-files'
if args.gateway_uart:out_name+='-gateway-uart'
if args.gateway:out_name+='-gateway'
if args.gateway_files_probe:out_name+='-'+args.gateway_files_probe
if args.gateway_probe:out_name+='-gateway-probe'
if args.phone_log_bank:
 # Keep this new combination distinct without exceeding DOSBox's host-path
 # buffers as the existing feature suffix chain grows.
 out_name='terminal-phone-log-bank-'+hashlib.sha256(out_name.encode('ascii')).hexdigest()[:12]
OUT=ROOT/'build'/out_name
if args.output_dir:
 OUT=args.output_dir.resolve()
 assert OUT.is_relative_to(ROOT/'build') and not OUT.exists(),'Choose a new build/ output directory'
OUT.mkdir(parents=True,exist_ok=True)
modules=['ansi','attributes','screen','erase','scroll','terminal_services','cursor_shape','cursor_state','modes','reports','input_dispatch','input_controls','render','text','ui_windows','modem_commands','modem_responses']
modules += ['attribute_boundary','keyboard_reverse_tab','attribute_repair']
modules += ['viewport','protected_erase','alternate_output','substitute_control']
sources=[]
if args.path_control:sources += [ROOT/'src/filesystem/path_bank.asm',ROOT/'src/filesystem/path_kernel.asm',ROOT/'reconstruction/file_path/change.asm']
if args.file_directory:sources.append(ROOT/'src/filesystem/find_kernel.asm')
if args.file_viewer:sources.append(ROOT/'src/filesystem/viewer_kernel.asm')
if args.gateway_probe:sources.append(ROOT/('standalone/gateway_files_probe.asm' if args.gateway_files_probe else 'standalone/gateway_lookup_probe.asm'))
for module in modules:
 sources += sorted((ROOT/'reconstruction'/module).glob('*.asm'))
sources += [ROOT/'reconstruction/uart/core.asm',ROOT/'reconstruction/keyboard/core.asm',ROOT/'src/uart/api.asm',ROOT/'src/ansi/decimal.asm',ROOT/'src/reports/decimal.asm',ROOT/'src/reports/data.asm']
# These native diagnostic entries have separate owners. A new recovered file
# must not enter the interactive application merely through a module glob.
sources = [p for p in sources if p not in (
 ROOT/'reconstruction/modem_responses/attempt.asm',
 ROOT/'reconstruction/modes/width_request.asm')]
sources += [ROOT/'reconstruction/directory_dial/bounded.asm',ROOT/'reconstruction/directory_accounting/patch.asm']
sources += [ROOT/'reconstruction/keyboard_mapping/classifier.asm']
sources += [ROOT/'reconstruction/keyboard_mapping/raw_classifier.asm']
sources += [ROOT/'reconstruction/keyboard_detection/detect.asm']
sources += [ROOT/'reconstruction/line_edit/insert_line.asm',ROOT/'reconstruction/line_edit/delete_line.asm']
sources += sorted((ROOT/'reconstruction/character_edit').glob('*.asm'))
sources += [ROOT/'src/process/dos_exec.asm']
if args.hook_execute:sources.append(ROOT/'src/process/hook_owner_dos.asm')
if args.hook_lookup:sources.append(ROOT/'src/process/hook_lookup_dos.asm')
sources += [ROOT/'reconstruction/snapshot'/name for name in ['row.asm','copy.asm','video_begin.asm','video_end.asm']]
sources += sorted((ROOT/'src/terminal').glob('*.asm'))
if not args.gateway_uart:sources=[p for p in sources if p.name!='gateway_uart.asm']
if not args.gateway:sources=[p for p in sources if p.name!='gateway_front.asm']
if not args.local_controls:sources=[p for p in sources if p.name!='local_controls.asm']
if not args.window_size_report:sources=[p for p in sources if p.name!='window_size_report.asm']
if not args.reset_row_owner:sources=[p for p in sources if p.name!='reset_rows.asm']
if not args.status_owner:sources=[p for p in sources if p.name!='status_transition_glue.asm']
if not args.manual_init_owner:sources=[p for p in sources if p.name!='manual_init.asm']
if not args.manual_init:sources=[p for p in sources if p.name!='manual_init_dispatch.asm']
if not args.auto_answer:sources=[p for p in sources if p.name!='modem_answer_ui.asm']
if not args.call_timer:sources=[p for p in sources if p.name!='call_timer.asm']
if args.call_timer:sources += [ROOT/'reconstruction/local_controls'/('timer_'+name+'.asm') for name in ('start','seconds','update')]
if not args.screen_pause:sources=[p for p in sources if p.name!='screen_pause.asm']
if args.local_controls:sources += [ROOT/'reconstruction/local_controls/reset.asm',ROOT/'reconstruction/local_controls/duplex.asm']
if args.notice_sound:sources.append(ROOT/'src/ui/speaker_native.asm')
# The dedicated call-log bank is built explicitly; never pull its callbacks or
# end marker into established terminals through the assembly glob.
sources = [p for p in sources if p.name not in
 ('phone_log_bank.asm','phone_log_resident.asm','phone_log_storage.asm','phone_log_end.asm','phone_log_startup_bank.asm','phone_log_lifecycle_bank.asm','phone_log_events_bank.asm','phone_log_disk_bank.asm','phone_log_controls_bank.asm','directory_reader_bank.asm')]
if args.projection_probe:sources.append(ROOT/'standalone/session_projection_probe.asm')
if args.hook_probe:sources.append(ROOT/'standalone/hook_transaction_probe.asm')
if args.input_probe:sources += [ROOT/'standalone/hook_transaction_probe.asm',ROOT/'standalone/hook_input_probe.asm']
if args.status_probe:sources.append(ROOT/'standalone/status_transition_probe.asm')
if args.display_row_probe:sources.append(ROOT/'standalone/display_rows_terminal_probe.asm')
sources += [ROOT/'src/aspect/resident_bridge.asm']
sources += [ROOT/'reconstruction/script_menu/window.asm']
sources += [ROOT/'src/status/status_renderer_bridge.asm',ROOT/'src/status/status_helpers.asm',
 ROOT/'reconstruction/terminal_reset/status_refresh.asm',ROOT/'reconstruction/terminal_reset/status_fill.asm',
 ROOT/'reconstruction/program_exec/strlen.asm']
sources += [ROOT/'reconstruction/terminal_reset/protected_home.asm']
mouse_units=[]
if args.mouse:
 mouse_provenance=json.loads((ROOT/'reconstruction/program_mouse/provenance.json').read_text())
 mouse_units=[ROOT/u['file'] for u in mouse_provenance['units']]
 sources += [ROOT/'src/mouse/terminal.asm',*mouse_units,ROOT/'reconstruction/program_mouse/defaults.asm',ROOT/'src/mouse/state.asm',ROOT/'src/mouse/platform.asm',ROOT/'src/mouse/dos_memory.asm']
 for source,unit in zip(mouse_units,mouse_provenance['units']):
  flat=OUT/('mouse-baseline-'+source.stem+'.bin')
  subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(flat)],check=True)
  assert hashlib.sha256(flat.read_bytes()).hexdigest()==unit['sha256']
protected_provenance=ROOT/'reconstruction/protected_erase/provenance.json'
protected_unit=json.loads(protected_provenance.read_text())['units'][0]
protected_flat=OUT/'protected-erase-baseline.bin'
subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/protected_unit['file']),'-o',str(protected_flat)],check=True)
assert protected_flat.stat().st_size==protected_unit['bytes']==142
assert hashlib.sha256(protected_flat.read_bytes()).hexdigest()==protected_unit['sha256']
alternate_provenance=ROOT/'reconstruction/alternate_output/provenance.json'
for alternate_unit in json.loads(alternate_provenance.read_text())['units']:
 flat=OUT/('alternate-'+Path(alternate_unit['file']).stem+'-baseline.bin')
 subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/alternate_unit['file']),'-o',str(flat)],check=True)
 assert flat.stat().st_size==alternate_unit['bytes']and hashlib.sha256(flat.read_bytes()).hexdigest()==alternate_unit['sha256']
substitute_provenance=ROOT/'reconstruction/substitute_control/provenance.json'
substitute_unit=json.loads(substitute_provenance.read_text())['units'][0]
substitute_flat=OUT/'substitute-control-baseline.bin'
subprocess.run(['nasm','-fbin',str(ROOT/substitute_unit['file']),'-o',str(substitute_flat)],check=True)
assert substitute_flat.stat().st_size==substitute_unit['bytes']==53 and hashlib.sha256(substitute_flat.read_bytes()).hexdigest()==substitute_unit['sha256']
render_import_adapters={}
sources.append(ROOT/'src/aspect/break_cursor_read.asm')
objects=[]
if args.directory_view:sources.append(ROOT/'src/terminal/directory_reader_bank.asm')
for index,source in enumerate(sources):
 obj=OUT/f'unit-{index}.obj';objects.append(str(obj));options=[]
 if source==ROOT/'src/ui/speaker_native.asm':options+=['-D_TEXT=CONFIG_CODE','-DCODE=FARCODE']
 if source.parent.parent.name=='reconstruction':options=['-D'+source.parent.name.upper()+'_OMF']
 if args.row_geometry_owner and source==ROOT/'reconstruction/program_mouse/init.asm':options+=['-Dmouse_bind=terminal_rows_mouse_bind']
 if source==ROOT/'reconstruction/ansi/dispatch.asm':options+=['-DTERMINAL_CHARACTER_PREFLIGHT','-DTERMINAL_LINE_PREFLIGHT','-DTERMINAL_RENDER_PREFLIGHT']
 if source==ROOT/'reconstruction/erase/display_after.asm':options+=['-Dcsi_service_d8b6=terminal_erase_after_native','-DTERMINAL_ERASE_PREFLIGHT']
 if source==ROOT/'reconstruction/erase/rectangle.asm':options+=['-Dcsi_service_2530=terminal_rectangle_native']
 if source==ROOT/'reconstruction/scroll/scroll_up.asm':options+=['-Dscroll_up=terminal_scroll_up_native']
 if source.parent.name=='script_menu':
  options=['-DLOCAL_WINDOW_OMF','-DLOCAL_WINDOW_FAR',
   '-Dlocal_window_help_context=keyboard_debug_gate',
   '-Dlocal_window_hook_enabled=keyboard_mapping_hook_enabled',
   '-Dlocal_window_hook_character=keyboard_mapping_hook_character']
  # The maintained window owns static far storage/prose, not native resource
  # tables. Its unused legacy pointer/scalar arguments share the initialized
  # context word; no duplicate near-data resource placeholders are needed.
  options += ['-Dlocal_window_'+name+'=keyboard_debug_gate' for name in
   ('descriptor','box_attribute','keyboard_table','text','text_attribute','status')]
 if source.parent.name=='alternate_output':options += ['-Derase_previous_attribute=repair_previous_attribute','-Dtext_write_cell=alternate_output_text','-Dattributes_protected_value=attributes_preset_value']
 if source.parent.name=='protected_erase':options += ['-Derase_repair_attributes=protected_erase_repair']
 if source.parent.name=='attribute_repair':
  options += ['-DATTRIBUTE_REPAIR_FAR','-Derase_default_attribute=repair_default_attribute',
   '-Derase_previous_attribute=repair_previous_attribute','-Dtext_write_char=repair_text_write_char',
   '-Dattributes_protected_value=attributes_preset_value']
 if source.parent.name=='viewport':
  options += ['-D_TEXT=ASPECT_CODE','-DCODE=FARCODE','-DVIEWPORT_PRESERVE_DS',
   '-Dui_cga_blank=viewport_cga_blank','-Dui_cga_unblank=viewport_cga_unblank']
 if source.parent.name in ('attribute_boundary','keyboard_reverse_tab') or source.name=='protected_home.asm':
  options += ['-DKEYBOARD_ECHO_FAR','-Dscreen_set_cursor=attribute_screen_set_cursor',
   '-Dscreen_cursor_left=attribute_screen_cursor_left','-Dscreen_cursor_right=attribute_screen_cursor_right',
   '-Dscreen_adjust_attribute_boundary=attribute_boundary_local']
 if source==ROOT/'src/aspect/resident_bridge.asm':options+=['-DRESIDENT_BRIDGE_FAR']
 if args.keyboard_bank:options+=['-DTERMINAL_KEYBOARD_BANK']
 if args.local_controls:options+=['-DTERMINAL_LOCAL_CONTROLS']
 if args.status_owner:options+=['-DTERMINAL_STATUS_OWNER']
 if args.status_control:options+=['-DTERMINAL_STATUS_CONTROL']
 if args.large_view_frames:options+=['-DTERMINAL_LARGE_VIEW_FRAMES']
 if args.row_notices:options+=['-DTERMINAL_ROW_NOTICES']
 if args.session_rows_probe is not None:options+=['-DTERMINAL_SESSION_ROWS_PROBE='+str(args.session_rows_probe)]
 if args.aspect_admission_probe:options+=['-DTERMINAL_ASPECT_ADMISSION_PROBE']
 if args.aspect_row_owner:options+=['-DTERMINAL_ASPECT_ROWS']
 if args.program_display_owner:options+=['-DTERMINAL_PROGRAM_DISPLAY']
 if args.xlt_display_probe:options+=['-DTERMINAL_XLT_DISPLAY_PROBE']
 if args.profile_display_probe:options+=['-DTERMINAL_PROFILE_DISPLAY_PROBE']
 if args.status_probe:options+=['-DTERMINAL_STATUS_PROBE']
 if args.display_row_probe:options+=['-DTERMINAL_DISPLAY_ROW_PROBE']
 if args.row_geometry_owner:options+=['-DTERMINAL_ROW_GEOMETRY']
 if args.display_preferences:options+=['-DTERMINAL_DISPLAY_PREFERENCES']
 if args.display_startup:options+=['-DTERMINAL_DISPLAY_STARTUP']
 if args.line_control:options+=['-DTERMINAL_LINE_CONTROL']
 if args.window_size_report and source==ROOT/'reconstruction/ansi/dispatch.asm':options+=['-DTERMINAL_WINDOW_SIZE_REPORT']
 if args.row_geometry_owner and args.display_row_probe:options+=['-DTERMINAL_ROW_GEOMETRY_PROBE']
 if args.screen_pause:options+=['-DTERMINAL_SCREEN_PAUSE']
 if args.call_timer:options+=['-DTERMINAL_CALL_TIMER']
 if args.elapsed_view:options+=['-DTERMINAL_ELAPSED_VIEW']
 if args.manual_init_owner:options+=['-DTERMINAL_MANUAL_INIT_OWNER']
 if args.auto_answer_owner:options+=['-DTERMINAL_AUTO_ANSWER_OWNER']
 if args.auto_answer:options+=['-DTERMINAL_AUTO_ANSWER']
 if args.manual_init:options+=['-DTERMINAL_MANUAL_INIT']
 if args.original_keys:options+=['-DTERMINAL_ORIGINAL_KEYS']
 if args.original_reference:options+=['-DTERMINAL_REFERENCE']
 if args.directory_view:options+=['-DTERMINAL_DIRECTORY_VIEW']
 if args.directory_preview:options+=['-DTERMINAL_DIRECTORY_PREVIEW']
 if args.directory_storage:options+=['-DTERMINAL_DIRECTORY_STORAGE']
 if args.directory_resource_cli:options+=['-DTERMINAL_DIRECTORY_RESOURCE_CLI']
 if args.directory_resource_owner:options+=['-DTERMINAL_DIRECTORY_RESOURCE_OWNER']
 if args.directory_retirement:options+=['-DTERMINAL_DIRECTORY_RETIREMENT']
 if args.directory_translation:options+=['-DDIRECTORY_TRANSLATION_RESOURCES']
 if args.directory_scripts:options+=['-DDIRECTORY_SCRIPT_RESOURCES']
 if args.directory_compile:options+=['-DDIRECTORY_SCRIPT_COMPILE']
 if args.directory_adopt:options+=['-DDIRECTORY_RESOURCE_ADOPTION']
 if args.external_render:options+=['-DASPECT_EXTERNAL_RENDER']
 if args.aspect_snapshot_lease:options+=['-DASPECT_SNAPSHOT_LEASE']
 if args.chat_storage:options+=['-DTERMINAL_CHAT_STORAGE']
 if args.chat_frontend:options+=['-DTERMINAL_CHAT_FRONTEND']
 if args.chat_echo:options+=['-DTERMINAL_CHAT_ECHO']
 if args.chat_foreground_text:options+=['-DTERMINAL_CHAT_FOREGROUND_TEXT']
 if args.chat_redisplay:options+=['-DTERMINAL_CHAT_REDISPLAY']
 if args.notice_sound:options+=['-DASPECT_SOUND_POLICY','-DTERMINAL_SOUND']
 if args.notice_input:options+=['-DASPECT_NOTICE_INPUT']
 if args.aspect_keys:options+=['-DASPECT_KEY_ACTIONS']
 if args.directory_keys:options+=['-DDIRECTORY_KEY_BINDINGS']
 if args.session_capture:options+=['-DTERMINAL_SESSION_CAPTURE']
 if args.session_projection:options+=['-DTERMINAL_SESSION_PROJECTION']
 if args.projection_probe:options+=['-DTERMINAL_SESSION_PROJECTION_PROBE']
 if args.session_baseline:options+=['-DTERMINAL_SESSION_BASELINE']
 if args.register_handoff:options+=['-DTERMINAL_REGISTER_HANDOFF']
 if args.session_controls:options+=['-DTERMINAL_SESSION_CONTROLS']
 if args.hook_return:options+=['-DTERMINAL_HOOK_RETURN']
 if args.hook_execute:options+=['-DTERMINAL_HOOK_EXECUTE']
 if args.hook_modem:options+=['-DTERMINAL_HOOK_MODEM']
 if args.hook_input:options+=['-DTERMINAL_HOOK_INPUT']
 if args.hook_apply:options+=['-DTERMINAL_HOOK_APPLY']
 if args.hook_lookup:options+=['-DTERMINAL_HOOK_LOOKUP']
 if args.gateway_files:options+=['-DTERMINAL_GATEWAY_FILES']
 if args.gateway_uart:options+=['-DTERMINAL_GATEWAY_UART']
 if args.gateway:options+=['-DTERMINAL_GATEWAY']
 if args.gateway_uart_probe:options+=['-DTERMINAL_GATEWAY_UART_PROBE']
 if args.phone_log_startup:options+=['-DTERMINAL_PHONE_LOG_STARTUP']
 if args.phone_log_events:options+=['-DTERMINAL_PHONE_LOG_EVENTS']
 if args.phone_log_disk:options+=['-DTERMINAL_PHONE_LOG_DISK']
 if args.custom_irq:options+=['-DTERMINAL_CUSTOM_IRQ']
 if args.cwd_identities:options+=['-DTERMINAL_CWD_IDENTITIES']
 if args.gateway_probe:options+=['-DTERMINAL_GATEWAY_PROBE']
 if args.file_directory:options+=['-DTERMINAL_FILE_DIRECTORY']
 if args.file_viewer:options+=['-DTERMINAL_FILE_VIEWER']
 if args.external_viewer:options+=['-DTERMINAL_EXTERNAL_VIEWER']
 if args.external_editor:options+=['-DTERMINAL_EXTERNAL_EDITOR']
 if args.path_control:
  options+=['-DTERMINAL_PATH_CONTROL']
  if source in (ROOT/'src/filesystem/path_kernel.asm',ROOT/'reconstruction/file_path/change.asm'):
   options+=['-D_TEXT=FILE_CODE','-DCODE=FARCODE','-DFILE_PATH_OMF']
 if args.special_edition:options+=['-DTERMINAL_SPECIAL_EDITION']
 if args.status_geometry:options+=['-DTERMINAL_STATUS_GEOMETRY']
 if args.native_reset_bank:options+=['-DTERMINAL_NATIVE_RESET_BANK']
 if args.native_reset_transaction:options+=['-DTERMINAL_NATIVE_RESET_TRANSACTION']
 if args.native_reset_bank and not args.native_reset_static:options+=['-DTERMINAL_NATIVE_RESET_OVERLAY']
 if args.input_probe:options+=['-DTERMINAL_HOOK_INPUT_PROBE']
 if args.hook_probe:options+=['-DTERMINAL_HOOK_PROBE']
 if args.exit_guard:options+=['-DTERMINAL_EXIT_GUARD']
 if args.traps:options+=['-DTERMINAL_TRAPS']
 if args.notice_sound and (args.exit_guard or args.traps):options+=['-DTERMINAL_FAR_USAGE']
 if args.trap_probe is not None:options+=['-DTERMINAL_TRAP_PROBE='+str(args.trap_probe)]
 if args.process_bank and source==ROOT/'src/process/dos_exec.asm':options+=['-DPROCESS_CODE_BANK']
 if args.hook_lookup and source==ROOT/'src/process/dos_exec.asm':options+=['-DPROCESS_LONG_PATHS']
 if args.exit_probe is not None:options+=['-DTERMINAL_EXIT_PROBE='+str(args.exit_probe)]
 if args.mouse:
  options+=['-DTERMINAL_MOUSE']
  if source in mouse_units or source in (ROOT/'src/mouse/platform.asm',ROOT/'src/mouse/dos_memory.asm'):
   options+=['-D_TEXT=MOUSE_CODE','-DCODE=FARCODE']
  if source==ROOT/'src/mouse/platform.asm':options+=['-DMOUSE_BANK']
 if source.parent==ROOT/'reconstruction/terminal_reset':
  options+=['-DSTATUS_CONFIG_CODE','-Dtext_fill_cells=status_text_fill','-Dtext_write_packed=status_text_packed',
   '-Dterminal_reset_ui_75e8=status_ui_printf','-Dterminal_reset_ui_7630=status_character_fill',
   '-Dterminal_reset_status_message=status_message']
 if source==ROOT/'src/status/status_helpers.asm':
  options+=['-DSTATUS_HELPERS_CONFIG','-Dui_write_string=status_write_string','-Dprogram_strlen=status_strlen']
 if source==ROOT/'reconstruction/input_dispatch/dispatch.asm':options+=['-Dterminal_receive_character=terminal_receive_character_native']
 if args.input_tables_data and source==ROOT/'reconstruction/input_dispatch/dispatch.asm':options+=['-DINPUT_TABLES_DATA']
 # Keep NASM's THEADR source name independent of the checkout location, so
 # recorded import-adapter object hashes also reproduce in a fresh tree.
 subprocess.run(['nasm','-f','obj',*options,'-I',str(ROOT/'reconstruction/uart')+'/', '-I',str(ROOT/'reconstruction/ansi')+'/', '-I',str(ROOT/'src/terminal')+'/', '-I',str(ROOT/'src/config')+'/', '-I',str(ROOT/'src/directory')+'/', '-I',str(ROOT/'src/aspect')+'/',str(source.relative_to(ROOT)),'-o',str(obj)],cwd=ROOT,check=True)
 if source==ROOT/'reconstruction/ansi/dispatch.asm':
  before=obj.read_bytes();normalized,counts=rename_imports(before,{'csi_set_modes':'terminal_aspect_set_modes','csi_reset_modes':'terminal_aspect_reset_modes'})
  assert counts=={'csi_set_modes':1,'csi_reset_modes':1},counts
  obj.write_bytes(normalized);render_import_adapters=dict(import_counts=counts,compiler_object_sha256=hashlib.sha256(before).hexdigest(),normalized_object_sha256=hashlib.sha256(normalized).hexdigest())
c_sources=[ROOT/'src/config/prm_dos.c',ROOT/'src/config/terminal_import.c',ROOT/'src/config/modem_import.c',ROOT/'src/config/startup_import.c',ROOT/'src/directory/directory_dos.c',ROOT/'src/directory/directory_live.c',ROOT/'src/directory/directory_actions.c',ROOT/'src/directory/directory_replace.c',ROOT/'src/directory/directory_replace_fs.c',ROOT/'src/key_mapping/keymap_dos.c',ROOT/'src/key_mapping/keymap_dos_fs.c']
path_sources={ROOT/'src/filesystem'/n for n in ('path_owner.c','path_session.c','path_dialog.c')} if args.path_control else set()
if args.file_directory:path_sources.update(ROOT/'src/filesystem'/n for n in ('find_owner.c','file_dialog.c'))
if args.file_viewer:path_sources.update(ROOT/'src/filesystem'/n for n in ('viewer_file.c','viewer_decode.c','viewer_session.c','viewer_dialog.c'))
if args.external_viewer:path_sources.update(ROOT/'src/filesystem'/n for n in ('viewer_external.c','viewer_external_dialog.c'))
c_sources+=sorted(path_sources)
if args.file_viewer:c_sources.append(ROOT/'src/filesystem/viewer_admission.c')
if args.gateway_handles:c_sources.append(ROOT/'src/process/process_handles.c')
if args.gateway_files:c_sources.append(ROOT/'src/process/gateway_files.c')
if args.gateway:c_sources.append(ROOT/'src/terminal/gateway_front.c')
if args.gateway_files_probe:c_sources.append(ROOT/'standalone/gateway_files_probe.c')
c_sources += [ROOT/'src/key_mapping/key_actions_dos.c',ROOT/'src/process/program.c']
c_sources += [ROOT/'src/config/live_configuration.c']
c_sources += [ROOT/'src/config/live_setup_owner.c']
if args.status_owner:c_sources.append(ROOT/'src/terminal/status_transition.c')
if args.status_probe:c_sources.append(ROOT/'standalone/status_transition_probe.c')
if args.display_row_probe:c_sources.append(ROOT/'standalone/display_rows_terminal_probe.c')
c_sources += [ROOT/'src/config'/name for name in ['terminal_preferences.c','transfer_import.c']]
if args.notice_sound:c_sources += [ROOT/'src/ui/speaker.c',ROOT/'src/ui/connect_alert.c']
c_sources += [ROOT/'src/translation/xlt_dos.c',ROOT/'src/translation/xlt_dos_fs.c']
c_sources += [ROOT/'src/translation/xlt_default.c',ROOT/'src/config/resource_path.c']
c_sources += [ROOT/'src/translation/xlt_live.c',ROOT/'src/redisplay/redisplay.c']
c_sources += [ROOT/'src/redisplay/command_menu.c',ROOT/'src/terminal/script_launch.c']
if args.original_reference:c_sources.append(ROOT/'src/redisplay/command_reference.c')
if args.directory_view:c_sources += [ROOT/'src/redisplay/directory_view.c',ROOT/'src/directory/directory_reader.c',ROOT/'src/directory/directory_reader_fs.c']
if args.directory_preview:c_sources += [ROOT/'src/directory/directory_selection.c',ROOT/'src/terminal/directory_preview.c']
if args.directory_storage:c_sources.append(ROOT/'src/directory/directory_storage.c')
if args.directory_resource_cli:c_sources += [ROOT/'src/directory/directory_resource_cli.c',ROOT/'src/terminal/resource_cli_bind.c']
if args.directory_resource_owner:c_sources += [ROOT/'src/directory/directory_resources.c',ROOT/'src/terminal/directory_resource_owner.c',ROOT/'src/terminal/directory_identity.c']
if args.cwd_identities:
 c_sources.append(ROOT/'src/filesystem/startup_identities.c')
 if not args.directory_resource_owner:c_sources.append(ROOT/'src/terminal/directory_identity.c')
if args.directory_retirement:c_sources.append(ROOT/'src/terminal/directory_retirement.c')
if args.directory_scripts:c_sources.append(ROOT/'src/directory/directory_script.c')
if args.directory_compile:c_sources.append(ROOT/'src/directory/directory_compile.c')
c_sources += sorted((ROOT/'src/clipboard').glob('*.c'))
c_sources += [ROOT/'src/transfer'/name for name in ['download_file.c','download_fs.c','native_file_bridge.c','terminal_receive.c']]
c_sources += [ROOT/'src/transfer/download_compare.c']
c_sources += [ROOT/'src/transfer'/name for name in ['upload_file.c','upload_fs.c','terminal_upload.c']]
c_sources += [ROOT/'src/transfer'/name for name in ['batch_header.c','batch_download.c','batch_upload.c','batch_upload_fs.c','ymodem.c','terminal_ymodem.c']]
c_sources += [ROOT/'src/transfer'/name for name in ['zmodem.c','zmodem_wire.c','zmodem_name.c','terminal_zmodem.c']]
c_sources += [ROOT/'src/transfer'/name for name in ['zmodem_autostart.c','terminal_autostart.c']]
c_sources += sorted((ROOT/'src/capture').glob('*.c'))
c_sources += sorted((ROOT/'src/printer').glob('*.c'))
c_sources += [ROOT/'src/aspect/renderer_client.c',ROOT/'src/aspect/renderer_policy.c']
c_sources += [ROOT/'src/aspect/recorder.c']
c_sources += sorted((ROOT/'src/recording').glob('*.c'))
c_sources += [ROOT/'src/status/status_formatter.c']
if args.mouse:c_sources += [ROOT/'src/mouse/owner.c',ROOT/'src/mouse/terminal.c']
if args.directory_keys:c_sources.append(ROOT/'src/terminal/directory_keys.c')
hook_sources={ROOT/'src/config/prm_projection.c',ROOT/'src/terminal/session_projection.c'} if args.session_projection else set()
if args.register_handoff:hook_sources.add(ROOT/'src/terminal/register_owner.c')
if args.hook_return:hook_sources.add(ROOT/'src/config/hook_return.c')
if args.hook_execute:hook_sources.update({ROOT/'src/terminal/hook_transaction.c',ROOT/'src/process/hook_owner.c',ROOT/'src/process/hook_exchange.c'})
if args.hook_modem:hook_sources.add(ROOT/'src/config/hook_modem.c')
if args.hook_input:hook_sources.add(ROOT/'src/config/hook_input.c')
if args.hook_apply:hook_sources.update({ROOT/'src/config/hook_apply.c',ROOT/'src/terminal/hook_launch.c'})
if args.hook_lookup:hook_sources.add(ROOT/'src/process/hook_lookup.c')
if args.directory_adopt:hook_sources.add(ROOT/'src/terminal/directory_adopt.c')
if args.hook_probe:hook_sources.add(ROOT/'standalone/hook_transaction_probe.c')
if args.input_probe:hook_sources.add(ROOT/'standalone/hook_input_probe.c')
c_sources+=sorted(hook_sources)
config_sources={ROOT/'src/directory/directory_live.c',ROOT/'src/config/live_configuration.c',ROOT/'src/config/live_setup_owner.c'}
if args.cwd_identities:config_sources.update({ROOT/'src/filesystem/startup_identities.c',ROOT/'src/terminal/directory_identity.c'})
if args.status_owner:config_sources.add(ROOT/'src/terminal/status_transition.c')
if args.status_probe:config_sources.add(ROOT/'standalone/status_transition_probe.c')
if args.display_row_probe:config_sources.add(ROOT/'standalone/display_rows_terminal_probe.c')
if args.directory_preview:config_sources.update({ROOT/'src/directory/directory_selection.c',ROOT/'src/terminal/directory_preview.c'})
if args.directory_storage:config_sources.update({ROOT/'src/directory/directory_actions.c',ROOT/'src/directory/directory_storage.c'})
if args.directory_resource_cli:config_sources.update({ROOT/'src/directory/directory_resource_cli.c',ROOT/'src/terminal/resource_cli_bind.c'})
if args.directory_resource_owner:config_sources.update({ROOT/'src/directory/directory_resources.c',ROOT/'src/terminal/directory_resource_owner.c',ROOT/'src/terminal/directory_identity.c'})
if args.directory_retirement:config_sources.add(ROOT/'src/terminal/directory_retirement.c')
if args.directory_scripts:config_sources.add(ROOT/'src/directory/directory_script.c')
if args.directory_compile:config_sources.add(ROOT/'src/directory/directory_compile.c')
config_sources.update({ROOT/'src/config'/name for name in ['terminal_preferences.c','transfer_import.c']})
if args.notice_sound:config_sources.update({ROOT/'src/ui/speaker.c',ROOT/'src/ui/connect_alert.c'})
config_sources.update({ROOT/'src/transfer'/name for name in ['zmodem_autostart.c','terminal_autostart.c']})
config_sources.add(ROOT/'src/translation/xlt_dos.c')
config_sources.update({ROOT/'src/translation/xlt_default.c',ROOT/'src/config/resource_path.c'})
config_sources.add(ROOT/'src/translation/xlt_live.c')
if args.elapsed_view:
 c_sources.append(ROOT/'src/redisplay/elapsed_view.c')
 config_sources.add(ROOT/'src/redisplay/elapsed_view.c')
config_sources.add(ROOT/'src/redisplay/redisplay.c')
if args.file_viewer:config_sources.add(ROOT/'src/filesystem/viewer_admission.c')
config_sources.add(ROOT/'src/redisplay/command_menu.c')
config_sources.add(ROOT/'src/terminal/script_launch.c')
if args.directory_keys:config_sources.add(ROOT/'src/terminal/directory_keys.c')
config_sources.update((ROOT/'src/clipboard').glob('*.c'))
config_sources.add(ROOT/'src/process/program.c')
config_sources.update({ROOT/'src/transfer/ymodem.c',ROOT/'src/transfer/batch_header.c'})
config_sources.update({ROOT/'src/transfer'/name for name in ['zmodem.c','zmodem_wire.c','zmodem_name.c','terminal_zmodem.c']})
config_sources.add(ROOT/'src/transfer/download_compare.c')
config_sources.add(ROOT/'src/capture/capture_reservation.c')
config_sources.add(ROOT/'src/capture/capture_session.c')
config_sources.update({ROOT/'src/recording/file.c',ROOT/'src/aspect/recorder.c'})
config_sources.add(ROOT/'src/recording/foreground.c')
config_aliases={'terminal_script_prepare':'terminal_script_prepare_impl'}
if args.directory_resource_owner:config_aliases.update({'keymap_dos_read':'config_resource_keymap_service','key_actions_dos_read':'config_resource_actions_service','capture_fs_attributes':'config_resource_attributes_service'})
if args.directory_storage:
 config_aliases.update({name:name+'_impl' for name in ['directory_save_record','directory_save_accounting']})
 config_aliases.update({name:'config_directory_'+short+'_service' for name,short in {
  'directory_replace_paths':'paths','directory_replace_record':'replace','directory_accounting_patch':'patch'}.items()})
if args.hook_input:config_aliases['xlt_live_offer']='xlt_live_offer_impl'
if args.hook_apply:config_aliases.update({'xlt_live_commit_check':'xlt_live_commit_check_impl','xlt_live_publish':'xlt_live_publish_impl'})
config_aliases.update({name:name+'_impl' for name in ['directory_live_decode','directory_live_read','directory_live_read_context','directory_live_context_matches','live_configuration_decode','live_setup_bind','live_setup_begin','live_setup_finish','live_setup_abort','live_setup_finish_policy','live_setup_acknowledge']})
config_aliases.update({name:'config_'+name+'_service' for name in ['memcpy','memset','memcmp','strchr','strcmp']})
config_aliases.update({name:name+'_impl' for name in ['terminal_preferences_read','terminal_directory_preferences_read','live_setup_transfer_settings']})
config_aliases.update({name:name+'_impl' for name in ['capture_session_initialize','capture_session_begin','capture_session_put','capture_session_flush','capture_session_stop','capture_session_pause','capture_session_poll','capture_session_shutdown']})
config_aliases.update({name:'config_capture_'+short+'_service' for name,short in {
 'capture_file_initialize':'initialize','capture_file_validate_path':'validate',
 'capture_file_begin':'begin','capture_file_append':'append','capture_file_cleanup':'cleanup'}.items()})
config_aliases.update({name:name+'_impl' for name in ['terminal_autostart_initialize','terminal_autostart_flush','terminal_autostart_poll','terminal_autostart_input']})
config_aliases.update({name:'config_'+name+'_service' for name in ['terminal_auto_deliver','terminal_auto_allowed','terminal_auto_start','terminal_auto_ticks']})
config_aliases['memmove']='config_memmove_service'
config_aliases['strlen']='config_strlen_service'
config_aliases.update({'terminal_import_decode':'config_terminal_decode_service','modem_import_decode':'config_modem_decode_service','prm_dos_load':'config_prm_read_service','directory_dos_read':'config_directory_read_service','directory_number_expand':'config_number_expand_service'})
config_aliases.update({'capture_fs_canonical':'config_canonical_service','live_modem_expand':'config_live_expand_service'})
config_aliases.update({'xlt_dos_read':'xlt_dos_read_impl',
 'xlt_dos_read_default':'xlt_dos_read_default_impl',
 'clipboard_transport':'config_clipboard_transport_service','history_file_event':'config_history_file_service','program_execute':'program_execute_impl','process_run':'config_process_run_service',
 'redisplay_event':'redisplay_event_impl','xlt_live_bind':'xlt_live_bind_impl','xlt_live_stage':'xlt_live_stage_impl','xlt_live_commit':'xlt_live_commit_impl',
 'xlt_live_initialize':'xlt_live_initialize_impl','xlt_live_reload':'xlt_live_reload_impl','xlt_live_editor':'xlt_live_editor_impl',
 'xlt_fs_open':'config_xlt_open_service','xlt_fs_read':'config_xlt_read_service',
 'xlt_fs_close':'config_xlt_close_service'})
config_aliases.update({name:name+'_impl' for name in ['ymodem_run','batch_header_end','batch_header_encode','batch_header_decode']})
config_aliases.update({'terminal_zmodem_store':'terminal_zmodem_store_impl','strcpy':'config_strcpy_service',
 'batch_upload_seek':'config_bu_seek_service','batch_upload_skip':'config_bu_skip_service',
 'batch_download_exact':'config_bd_exact_service'})
config_aliases.update({name:'config_'+short+'_service' for name,short in {
 'transfer_crc_buffer_original':'ym_crc','ymodem_io_read':'ym_read','ymodem_io_put':'ym_put','ymodem_io_unread':'ym_unread',
 'ymodem_io_poll':'ym_poll','ymodem_io_progress':'ym_progress','ymodem_io_modem':'ym_modem',
 'batch_download_begin':'bd_begin','batch_download_open':'bd_open','batch_download_append':'bd_append',
 'batch_download_finish':'bd_finish','batch_download_cleanup':'bd_cleanup',
 'batch_upload_begin':'bu_begin','batch_upload_read':'bu_read','batch_upload_next':'bu_next',
 'batch_upload_close':'bu_close','batch_upload_abort':'bu_abort'}.items()})
helper_adapters={};zmodem_helper_adapters={};directory_fs_adapters={}
packed_command_ui=None
size_profile_path=ROOT/'standalone/terminal_size_profile.json'
size_profile=json.loads(size_profile_path.read_text())if args.optimize_size else None
optimized_c_sources={}
if size_profile:assert size_profile['version']==1
if args.chat_text_transport:
 chat_size_path=ROOT/'src/chat/text_transport_size.json'
 chat_size=json.loads(chat_size_path.read_text());assert chat_size['version']==1
 size_profile['compiler_options'].update(chat_size['compiler_options'])
 size_profile['sources'].update(chat_size['sources'])
if args.chat_echo:
 echo_size_path=ROOT/'src/chat/echo_size.json'
 echo_size=json.loads(echo_size_path.read_text());assert echo_size['version']==1
 size_profile['compiler_options'].update(echo_size['compiler_options'])
 size_profile['sources'].update(echo_size['sources'])
for source in c_sources:
 obj=OUT/(source.stem+'.obj');objects.append(str(obj))
 options=['-nt=CONFIG_CODE','-nc=FARCODE']+['-d'+name+'='+alias for name,alias in config_aliases.items()] if source in config_sources else []
 if args.directory_storage and source in (ROOT/'src/directory/directory_actions.c',ROOT/'src/directory/directory_storage.c'):
  options+=['-os']
 if (args.directory_resource_owner and source.name in ('directory_resources.c','directory_resource_owner.c')) or (args.directory_retirement and source.name=='directory_retirement.c') or (args.directory_scripts and source.name=='directory_script.c') or (args.directory_compile and source.name=='directory_compile.c'):
  options+=['-os']
 if args.directory_adopt and source.name in ('live_setup_owner.c','xlt_live.c'):options+=['-os']
 if source==ROOT/'src/redisplay/command_reference.c':options=['-nt=REFERENCE_CODE','-nc=FARCODE']
 if args.original_reference and source==ROOT/'src/redisplay/command_menu.c':
  # The foreground owner remains in CONFIG_CODE. Its explicitly far cdecl
  # menu entry shares the reference bank; DGROUP and frame ownership stay put.
  options=['-nt=REFERENCE_CODE','-nc=FARCODE']
 if args.code_label_offsets and source.name in ('command_menu.c','command_reference.c'):options+=['-dCHAT_NEAR_TEXT']
 if args.directory_view and source in (ROOT/'src/redisplay/directory_view.c',ROOT/'src/directory/directory_reader.c',ROOT/'src/directory/directory_reader_fs.c'):
  options=['-nt=DIRECTORY_CODE','-nc=FARCODE','-dDIRECTORY_READER_FAR']
 if source in hook_sources:
  aliases={'memcpy':'hook_memcpy_service','memcmp':'hook_memcmp_service',
           'terminal_import_decode':'hook_terminal_decode_service','modem_import_decode':'hook_modem_decode_service',
           'transfer_import_decode':'hook_transfer_decode_service','transfer_import_path':'hook_transfer_path_service'}
  if args.hook_return:aliases['live_modem_expand']='hook_live_expand_service'
  options=['-nt=HOOK_CODE','-nc=FARCODE','-dPRM_PROJECT_FAR_RATES',*['-d'+name+'='+alias for name,alias in aliases.items()]]
 if args.phone_log_bank and source in (ROOT/'src/capture/capture_file.c',ROOT/'src/capture/capture_reservation.c'):
  options+=['-dCAPTURE_FIXED_RESERVATION']
 if source.parent==ROOT/'src/aspect' and source not in config_sources:options=['-nt=ASPECT_CODE','-nc=FARCODE']
 if args.phone_log_controls:options+=['-dPHONE_LOG_CONTROLS']
 if args.local_controls:options+=['-dTERMINAL_LOCAL_CONTROLS']
 if args.cwd_identities:options+=['-dTERMINAL_CWD_IDENTITIES']
 if args.gateway_lookup:options+=['-dTERMINAL_GATEWAY_LOOKUP']
 if args.gateway_handles:options+=['-dTERMINAL_GATEWAY_HANDLES']
 if args.gateway_files:options+=['-dTERMINAL_GATEWAY_FILES']
 if args.gateway:options+=['-dTERMINAL_GATEWAY']
 if source==ROOT/'src/terminal/gateway_front.c':options+=['-nt=FILE_CODE','-nc=FARCODE']
 if args.gateway_handles and source==ROOT/'src/process/process_handles.c':options+=['-dPROCESS_HANDLES_BANKED','-nt=FILE_CODE','-nc=FARCODE']
 if args.gateway_files and source==ROOT/'src/process/gateway_files.c':options+=['-dPROCESS_HANDLES_BANKED','-nt=FILE_CODE','-nc=FARCODE']
 if source==ROOT/'standalone/gateway_files_probe.c':
  options+=['-nt=FILE_CODE','-nc=FARCODE']
  if args.gateway_uart_probe:options+=['-dTERMINAL_GATEWAY_UART_PROBE']
  if args.gateway_files_probe=='hold':options+=['-dGATEWAY_PROBE_HOLD']
 if args.file_directory:options+=['-dTERMINAL_FILE_DIRECTORY']
 if args.file_viewer:options+=['-dTERMINAL_FILE_VIEWER']
 if args.external_viewer:options+=['-dTERMINAL_EXTERNAL_VIEWER']
 if args.external_editor:options+=['-dTERMINAL_EXTERNAL_EDITOR']
 if args.path_control:options+=['-dTERMINAL_PATH_CONTROL']
 if source in path_sources:options+=['-nt=FILE_CODE','-nc=FARCODE']
 if args.status_control:options+=['-dTERMINAL_STATUS_CONTROL']
 if args.line_control:options+=['-dTERMINAL_LINE_CONTROL']
 if args.large_view_frames:options+=['-dTERMINAL_LARGE_VIEW_FRAMES']
 if args.aspect_admission_probe:options+=['-dTERMINAL_ASPECT_ADMISSION_PROBE']
 if args.aspect_row_owner:options+=['-dTERMINAL_ASPECT_ROWS']
 if args.native_reset_transaction:options+=['-dASPECT_WIDTH_PREFLIGHT']
 if args.program_display_owner:options+=['-dTERMINAL_PROGRAM_DISPLAY']
 if args.xlt_display_probe:options+=['-dTERMINAL_XLT_DISPLAY_PROBE']
 if args.profile_display_probe:options+=['-dTERMINAL_PROFILE_DISPLAY_PROBE']
 if args.screen_pause:options+=['-dTERMINAL_SCREEN_PAUSE']
 if args.elapsed_view:options+=['-dTERMINAL_ELAPSED_VIEW']
 if args.manual_init:options+=['-dTERMINAL_MANUAL_INIT']
 if args.auto_answer:options+=['-dTERMINAL_AUTO_ANSWER']
 if args.original_keys:options+=['-dTERMINAL_ORIGINAL_KEYS']
 if args.original_reference:options+=['-dTERMINAL_REFERENCE']
 if args.directory_view:options+=['-dTERMINAL_DIRECTORY_VIEW']
 if args.directory_preview:options+=['-dTERMINAL_DIRECTORY_PREVIEW']
 if args.directory_storage:options+=['-dTERMINAL_DIRECTORY_STORAGE']
 if args.directory_resource_cli:options+=['-dTERMINAL_DIRECTORY_RESOURCE_CLI']
 if args.directory_resource_owner:options+=['-dTERMINAL_DIRECTORY_RESOURCE_OWNER']
 if args.directory_retirement:options+=['-dTERMINAL_DIRECTORY_RETIREMENT']
 if args.directory_translation:options+=['-dDIRECTORY_TRANSLATION_RESOURCES']
 if args.directory_scripts:options+=['-dDIRECTORY_SCRIPT_RESOURCES']
 if args.directory_compile:options+=['-dDIRECTORY_SCRIPT_COMPILE']
 if args.directory_adopt:options+=['-dDIRECTORY_RESOURCE_ADOPTION']
 if args.directory_resource_owner and source.name in ('directory_resources.c','keymap_dos.c','key_actions_dos.c'):options+=['-dKEY_RESOURCE_PRIVATE_READS']
 if args.external_render:options+=['-dASPECT_EXTERNAL_RENDER']
 if args.aspect_snapshot_lease:options+=['-dASPECT_SNAPSHOT_LEASE']
 if args.session_baseline:options+=['-dTERMINAL_SESSION_BASELINE']
 if args.display_preferences:options+=['-dTERMINAL_DISPLAY_PREFERENCES']
 if args.register_handoff:options+=['-dTERMINAL_REGISTER_HANDOFF']
 if args.custom_irq:options+=['-dTERMINAL_CUSTOM_IRQ']
 if args.session_controls:options+=['-dTERMINAL_SESSION_CONTROLS']
 if args.hook_return:options+=['-dTERMINAL_HOOK_RETURN']
 if args.hook_modem:options+=['-dTERMINAL_HOOK_MODEM']
 if args.hook_input:options+=['-dTERMINAL_HOOK_INPUT']
 if args.hook_apply:options+=['-dTERMINAL_HOOK_APPLY']
 if args.notice_sound:options+=['-dASPECT_SOUND_POLICY','-dTERMINAL_SOUND']
 if args.notice_input:options+=['-dASPECT_NOTICE_INPUT']
 if args.directory_keys:options+=['-dDIRECTORY_KEY_BINDINGS']
 if args.mouse:
  options+=['-dTERMINAL_MOUSE']
  if source.parent==ROOT/'src/mouse':
   mouse_names=['mouse_settings_decode','mouse_owner_open','mouse_owner_suspend','mouse_owner_resume','mouse_owner_close','mouse_owner_key','mouse_owner_phase','mouse_owner_bytes','mouse_owner_reconfigure',
    'terminal_mouse_bootstrap','terminal_mouse_stage','terminal_mouse_start','terminal_mouse_pause','terminal_mouse_resume','terminal_mouse_stop','terminal_mouse_offer','terminal_mouse_commit','terminal_mouse_discard']
   if args.hook_apply:mouse_names+=['mouse_owner_reconfigure_check','mouse_owner_reconfigure_publish','terminal_mouse_check','terminal_mouse_publish']
   options+=['-nt=MOUSE_CODE','-nc=FARCODE','-ecc','-dMOUSE_DOS_PLATFORM',*['-d'+n+'='+n+'_impl' for n in mouse_names]]
 if source==ROOT/'src/status/status_formatter.c':options=['-ecc']
 if args.row_geometry_owner and args.display_row_probe and source==ROOT/'standalone/display_rows_terminal_probe.c':options+=['-dTERMINAL_ROW_GEOMETRY_PROBE']
 compiled_source=source;packed_includes=[]
 if size_profile:
  entry=size_profile['sources'].get(str(source.relative_to(ROOT)))
  if entry:
   assert hashlib.sha256(source.read_bytes()).hexdigest()==entry['source_sha256'],'Refresh the reviewed size profile after source changes: '+str(source)
   chosen=size_profile['compiler_options'][entry['profile']]
   options+=chosen;optimized_c_sources[str(source.relative_to(ROOT))]=chosen
 if args.packed_command_ui and source==ROOT/'src/redisplay/command_menu.c':
  from pack_command_ui import pack
  compiled_source,packed_command_ui=pack(source,OUT,args.command_ui_pairs)
  packed_includes=['-i='+str(source.parent),'-i='+str(OUT)]
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we',*options,*packed_includes,'-i='+str(ROOT/'src/config'),'-i='+str(ROOT/'src/directory'),'-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'src/process'),'-i='+str(ROOT/'src/transfer'),'-fo='+str(obj),str(compiled_source)],cwd=OUT,check=True)
 if args.directory_view and source.name=='directory_reader_fs.c':
  before=obj.read_bytes();normalized,counts=rename_imports(before,{
   '_dos_'+name+'_':'directory_dos_'+name+'_service_' for name in ('open','read','close')})
  assert counts=={'_dos_open_':1,'_dos_read_':1,'_dos_close_':1}
  (OUT/'directory-fs-compiler.obj').write_bytes(before);obj.write_bytes(normalized)
  directory_fs_adapters=dict(import_counts=counts,compiler_sha256=hashlib.sha256(before).hexdigest(),normalized_sha256=hashlib.sha256(normalized).hexdigest())
 if source in (ROOT/'src/transfer/batch_header.c',ROOT/'src/transfer/zmodem.c'):
  before=obj.read_bytes();normalized,counts=rename_imports(before,{'__U4D':'config_u4div_service_','__U4M':'config_u4mul_service_'})
  (OUT/('batch-header-compiler.obj' if source.stem=='batch_header' else 'zmodem-compiler.obj')).write_bytes(before);obj.write_bytes(normalized)
  record=dict(import_counts=counts,compiler_object_sha256=hashlib.sha256(before).hexdigest(),normalized_object_sha256=hashlib.sha256(normalized).hexdigest())
  if source.stem=='batch_header':helper_adapters=record
  else:zmodem_helper_adapters=record
config_end=ROOT/'src/config/far_end.asm';config_end_obj=OUT/'config-end.obj'
subprocess.run(['nasm','-f','obj',str(config_end),'-o',str(config_end_obj)],check=True)
objects.append(str(config_end_obj));sources.append(config_end)
if args.mouse:
 mouse_end=ROOT/'src/mouse/far_end.asm';mouse_end_obj=OUT/'mouse-end.obj'
 subprocess.run(['nasm','-fobj',str(mouse_end),'-o',str(mouse_end_obj)],check=True)
 objects.append(str(mouse_end_obj));sources.append(mouse_end)
native=build_native_receiver(ROOT,OUT)
objects += list(map(str,native['objects']))
sender=build_native_sender(ROOT,OUT)
objects += list(map(str,sender['objects']))
reset_bank=None
if args.native_reset_bank:
 from ui.native_reset_link import build_native_reset_bank
 reset_bank=build_native_reset_bank(ROOT,OUT,overlay=not args.native_reset_static,transaction=args.native_reset_transaction)
 objects+=list(map(str,reset_bank['objects']));sources+=reset_bank['inputs']
phone_log_bank=None
display_rows_bank=None
if args.display_row_owner:
 from process.display_rows_link import build_display_rows_bank
 display_rows_bank=build_display_rows_bank(ROOT,OUT,geometry=args.row_geometry_owner,mouse=args.mouse,selectors=args.display_preferences,program_display=args.program_display_owner,startup=args.display_startup)
 objects+=list(map(str,display_rows_bank['objects']));sources+=display_rows_bank['inputs']
if args.phone_log_bank:
 from build_phone_log_bank import build_bank
 phone_log_bank=build_bank(OUT,reservations=args.phone_log_reservations,startup=args.phone_log_startup,lifecycle=args.phone_log_lifecycle,events=args.phone_log_events,disk=args.phone_log_disk,controls=args.phone_log_controls,gateway=args.gateway_files)
 objects+=list(map(str,phone_log_bank['objects']));sources+=phone_log_bank['sources']
ordering=['CODE','FARCODE']+(['NATIVE_DATA']if args.native_reset_static else[])+(['PHONE_DATA']if args.phone_log_bank else[])+['DATA','BSS','STACK']
chat_loader=None
if args.chat_loader:
 from chat.loader_link import build_loader
 chat_loader=build_loader(ROOT,OUT,presentation=args.chat_presentation,timing=args.chat_timing,foreground=args.chat_foreground_text,redisplay=args.chat_redisplay)
 objects+=list(map(str,chat_loader['objects']));sources+=chat_loader['inputs']
if args.chat_adapters:
 source=ROOT/'src/chat/parent_sink.asm';obj=OUT/'chat-adapters.obj'
 subprocess.run(['nasm','-fobj',*(['-DCHAT_REDISPLAY'] if args.chat_redisplay else []),str(source),'-o',str(obj)],check=True)
 objects.append(str(obj));sources+=[source,ROOT/'src/chat/parent_sink.h']
if args.chat_text_transport:
 source=ROOT/'src/chat/text_transport.asm';obj=OUT/'chat-text-transport.obj'
 subprocess.run(['nasm','-fobj',str(source),'-o',str(obj)],check=True)
 objects.append(str(obj));sources+=[source,ROOT/'src/chat/text_transport.h']
if args.chat_echo:
 for leaf in ('echo_cursor','echo_owner'):
  source=ROOT/'src/chat'/(leaf+'.asm');obj=OUT/(leaf+'.obj')
  subprocess.run(['nasm','-fobj',*(['-DTERMINAL_CHAT_FOREGROUND_TEXT'] if args.chat_foreground_text else []),str(source),'-o',str(obj)],check=True)
  objects.append(str(obj));sources.append(source)
if args.chat_frontend:
 source=ROOT/'src/chat/frontend.c';obj=OUT/'chat-frontend.obj'
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-ox','-os','-oe=0',
  '-dCHAT_PRESENTATION',*(['-dCHAT_TEXT','-dCHAT_TIMING'] if args.chat_timing else []),*(['-dCHAT_ECHO'] if args.chat_echo else []),*(['-dCHAT_FOREGROUND_TEXT'] if args.chat_foreground_text else []),*(['-dCHAT_REDISPLAY'] if args.chat_redisplay else []),'-nt=CONFIG_CODE','-nc=FARCODE','-fo='+str(obj),str(source)],check=True)
 objects.insert(objects.index(str(config_end_obj)),str(obj));sources.append(source)
 source=ROOT/'src/chat/frontend.asm';obj=OUT/'chat-frontend-bridges.obj'
 subprocess.run(['nasm','-fobj',*(['-DCHAT_FOREGROUND_TEXT'] if args.chat_foreground_text else []),*(['-DCHAT_REDISPLAY'] if args.chat_redisplay else []),str(source),'-o',str(obj)],check=True)
 objects.insert(objects.index(str(config_end_obj)),str(obj));sources.append(source)
if args.directory_resource_owner:ordering+=['FAR_DATA','FROZEN_DATA']
subprocess.run(['wlink','system','dos','order',*[value for kind in ordering for value in ('clname',kind)],'option','quiet','option','map='+str(OUT/'terminal.map'),'name',str(OUT/'TERMINAL.EXE'),'file',','.join(objects),'library',str(Path(os.environ['WATCOM'])/'lib286/dos/clibs.lib')],check=True)
listing=(OUT/'terminal.map').read_text();group=re.search(r'^DGROUP\s+[0-9a-f]+:[0-9a-f]+\s+([0-9a-f]+)',listing,re.M|re.I)
assert group and int(group[1],16)<65536,'DS=SS small-model data/stack exceeds 64KiB'
memory=inspect_terminal_memory(OUT/'TERMINAL.EXE',OUT/'terminal.map')
if chat_loader:
 bank=next(c for c in memory['code_segments'] if c['name']=='CHAT_LOAD_CODE')
 assert bank['bytes']==chat_loader['code_bytes'] and bank['offset']+bank['bytes']<=65536
 assert '_chat_module_dispatch' not in listing,'Chat implementation must remain outside the resident parent'
if args.display_row_owner:
 bank=next((c for c in memory['code_segments'] if c['name']=='DISPLAY_CODE'),None)
 assert bank and bank['offset']+bank['bytes']<=65536,'BIOS row bank exceeds its code segment'
 assert all(c is bank or c['relative_segment']!=bank['relative_segment'] for c in memory['code_segments']),'BIOS row bank shares an executable CS'
 display_rows_bank['segment']=bank['relative_segment'];display_rows_bank['offset']=bank['offset'];display_rows_bank['bytes']=bank['bytes']
assert memory['initial_terminal_rows']==(24 if args.status_geometry or args.directory_adopt else 25)
if args.phone_log_reservations:assert memory['phone_log_claim_far_calls_verified']==2
if args.display_preferences:sources.append(ROOT/'src/config/display_preferences.h')
inputs=sources+c_sources+[ROOT/'src/config/prm_dos.h',ROOT/'src/config/terminal_import.h',ROOT/'src/config/terminal_import.inc',ROOT/'src/config/modem_import.h',ROOT/'src/config/modem_import.inc',ROOT/'src/config/startup_import.h',ROOT/'reconstruction/uart/encodings.inc',ROOT/'reconstruction/uart/layout.inc',ROOT/'reconstruction/ansi/dispatch-layout.inc']
inputs += [ROOT/'src/config/live_configuration.h',ROOT/'src/aspect/resident_render.h',ROOT/'src/aspect/resident_bridge.inc',ROOT/'src/aspect/renderer_policy.h',ROOT/'src/aspect/serial_handoff.h']
inputs += [protected_provenance,alternate_provenance,substitute_provenance]
inputs += [ROOT/'src/status/status_state.inc',ROOT/'src/status/status_formatter.h']
inputs += [ROOT/'src/config/live_setup_owner.h',ROOT/'src/config/terminal_preferences.h',ROOT/'src/config/transfer_import.h']
if args.notice_sound:inputs.append(ROOT/'src/ui/speaker.h')
inputs += [ROOT/'src/config/resource_path.h']
if args.status_owner:inputs.append(ROOT/'src/terminal/status_transition.h')
if args.custom_irq:inputs.append(ROOT/'src/config/irq_policy.h')
if args.gateway_uart:inputs.append(ROOT/'src/terminal/gateway_uart.h')
if args.gateway:inputs.append(ROOT/'src/terminal/gateway_front.h')
inputs += sorted((ROOT/'src/directory').glob('*.h'))+sorted((ROOT/'src/directory').glob('*.inc'))
inputs += sorted((ROOT/'src/process').glob('*.h'))
inputs += sorted((ROOT/'src/capture').glob('*.h'))
inputs += sorted((ROOT/'src/recording').glob('*.h'))+[ROOT/'src/aspect/recorder.h']
inputs += sorted((ROOT/'src/printer').glob('*.h'))
inputs += sorted((ROOT/'src/clipboard').glob('*.h'))
inputs += sorted((ROOT/'src/redisplay').glob('*.h'))
inputs += [ROOT/'src/transfer'/name for name in ['download_file.h','download_fs.h','native_file_bridge.h','upload_file.h','upload_fs.h','batch_header.h','batch_download.h','batch_upload.h','batch_upload_fs.h','ymodem.h']]+native['inputs']+[ROOT/'standalone/terminal_memory.py']
inputs += sender['inputs']
inputs += [ROOT/'src/transfer/zmodem.h',ROOT/'src/transfer/zmodem_wire.h',ROOT/'src/transfer/zmodem_name.h',ROOT/'src/transfer/zmodem_autostart.h']
inputs += [ROOT/'src/transfer/download_compare.h']
inputs += [ROOT/'standalone/omf_imports.py',Path(__file__).resolve()]
inputs += sorted((ROOT/'src/terminal').glob('*.inc'))
if args.packed_command_ui:inputs += [ROOT/'standalone/pack_command_ui.py',ROOT/'src/redisplay/command_ui_codec.h']
if args.optimize_size:inputs.append(size_profile_path)
if args.chat_text_transport:inputs.append(chat_size_path)
if args.chat_echo:inputs.append(echo_size_path)
if args.session_projection:inputs += [ROOT/'src/config/prm_projection.h',ROOT/'src/terminal/session_projection.h']
if args.session_baseline:inputs += [ROOT/'src/terminal/session_baseline.h']
if args.directory_preview:inputs += [ROOT/'src/terminal/directory_preview.h']
if args.keyboard_bank:inputs.append(ROOT/'src/terminal/keyboard_bank_targets.json')
if args.directory_resource_cli:inputs += [ROOT/'src/directory/directory_resource_cli.h',ROOT/'src/directory/directory_resources.h']
if args.directory_resource_owner:inputs += [ROOT/'src/terminal/directory_resource_owner.h',ROOT/'src/terminal/directory_identity.h']
if args.cwd_identities and not args.directory_resource_owner:inputs += [ROOT/'src/terminal/directory_identity.h']
if args.file_directory:inputs += [ROOT/'src/filesystem'/n for n in ('find_owner.h','file_dialog.h')]
if args.file_viewer:inputs += [ROOT/'src/filesystem'/n for n in ('viewer_file.h','viewer_file_backend.h','viewer_decode.h','viewer_session.h','viewer_dialog.h')]
if args.external_viewer:inputs += [ROOT/'src/filesystem'/n for n in ('viewer_external.h','viewer_external_dialog.h')]
if args.path_control:inputs += [ROOT/'src/filesystem'/n for n in ('path_owner.h','path_session.h','path_dialog.h')]+[ROOT/'reconstruction/file_path/provenance.json']
if args.directory_retirement:inputs.append(ROOT/'src/terminal/directory_retirement.h')
if args.directory_scripts:inputs.append(ROOT/'src/directory/directory_script.h')
if args.register_handoff:inputs += [ROOT/'src/terminal/register_owner.h',ROOT/'src/aspect/register_handoff.h',ROOT/'src/aspect/register_codec.h']
if args.hook_return:inputs.append(ROOT/'src/config/hook_return.h')
if args.hook_execute:inputs += [ROOT/'src/terminal/hook_transaction.h',ROOT/'src/process/hook_owner.h',ROOT/'src/process/hook_exchange.h']
if args.hook_modem:inputs.append(ROOT/'src/config/hook_modem.h')
if args.hook_input:inputs.append(ROOT/'src/config/hook_input.h')
if args.hook_apply:inputs.append(ROOT/'src/config/hook_apply.h')
if args.hook_lookup:inputs.append(ROOT/'src/process/hook_lookup.h')
inputs += sorted((ROOT/'src/translation').glob('*.h'))
inputs += sorted((ROOT/'src/key_mapping').glob('*.h'))+sorted((ROOT/'src/key_mapping').glob('*.inc'))
if args.mouse:inputs += [ROOT/'src/mouse/owner.h',ROOT/'reconstruction/program_mouse/provenance.json',ROOT/'reconstruction/program_mouse/defaults.json']
manifest={'experimental_directory_keys':args.directory_keys,'experimental_aspect_keys':args.aspect_keys,'aspect_renderer_import_adapters':render_import_adapters,'kind':'source-only-interactive-dos-terminal','binary_sha256':hashlib.sha256((OUT/'TERMINAL.EXE').read_bytes()).hexdigest(),'data_stack_bytes':int(group[1],16),'memory_layout':memory,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'limitations':['Interactive terminal milestone, not the complete PCPlus application.','Explicit /X:FILE.XLT stages an exact256-byte input table before UART ownership. Normal terminal bytes translate after connection/raw-monitor/controller/transfer filtering; parser continuations, TX and binary/dedicated owners stay raw. RIS preserves selection. Saved PRM modes0/1/2 select identity, current-directory then bounded PCPLUS-environment PCPLUS.XLT lookup, or a7-bit driver mask; /X overrides valid saved modes. Binary transfers reject non-FF masks. AltF10 mode changes use a frozen pre-child current/PCPLUS namespace, checked table staging and separate confirmation before table/enabled/mask commit while serial ownership is handed off. Explicit /X pins its selection. Queued raw input uses the accepted mode after return. Alt-F9 or Setup/Reload input table stages the frozen active canonical source and asks before accepting a same-mode reload over the drained PROGRAM UART owner, without DOS EXEC. Failed/declined reloads retain the table; queued input uses an accepted table. Startup canonical source paths are limited to63 bytes, including resolved CWD. Alt-F8/menu launches sibling XLTEDIT for the frozen active canonical table via a bounded DOS3+ PSP trailer and direct EXEC. A fresh checked snapshot requires separate confirmation after return. The editor accepts DOS8.3 leaves and absolute63-byte paths with same-parent recovery. Complete resource and settings integration remain unfinished.','Selected ANSI/ordinary controls and ASCII/raw CP437 output; all79 raw keyboard binding slots, function/modifier/keypad banks and bounded binary output now integrated. Specialized controls, fonts, other profiles and full UI remain unfinished.','Maintained /S @8.3-leaf runs local source-built PRMEDIT.EXE directly before UART ownership; failure stops startup and successful return reloads through existing validation/CLI precedence. Alt-F10 invokes the editor through the live PROGRAM handoff for an explicit current-directory8.3 leaf. A canonical startup binding, validated candidate and selective commit adopt display, pacing, future modem commands/responses and BREAK; A separate Y/N choice permits same-port baud/line/flow changes after old-format XON/TEMT handoff; Supported4/6 profile changes use a separate confirmation, staged canonical KBD selection and clean RIS/view baseline. Confirmed COM moves require idle ports, preserve target DTR, restore old hardware/vector ownership and recheck acquisition after profile confirmation. No automatic hangup/redial, original PCSETUP ABI, complete emulation collection or source of defaults.', 'Standard COM1..4; default builds require a matching BIOS entry. Custom-IRQ builds also accept an omitted BIOS slot for the validated base/IRQ, but reject a conflicting nonzero entry. Explicit partial2.01 PRM import and CLI category overrides. Explicit KBD profile import stages and validates before UART access. AUTO BIOS detection and manual STANDARD/ENHANCED selection supported; no complete PRM schema/default generation.','Explicit-target and directory/browser MODEM/DIRECT connections supported. Native 16-field editor stages changes until acceptance; explicit saves use validated full-file staging and backup replacement.', 'Successful directory connections queue date/call-count updates for deferred foreground persistence. Replacement does not guarantee crash atomicity or concurrent-writer exclusion.', 'Stored password remains private metadata, masked in the editor and never automatically transmitted. Scripts, KEY/META bindings and HALF mode fail explicitly; cycles, advanced transfers, Host and the complete original settings/UI remain unfinished.','NETWORK line editing clips counts to the active region and preserves the column. ORIGINAL ANSI CSI M uses a serviced36-tick discard wait; the exact unbounded original helper is not linked. Complex attribute repair remains explicit. Supported-profile RIS restores a captured source-owned startup state and keymap without DOS/file IO.', 'KBD defaults are maintained network choices, not recovered factory per-profile blocks. Unknown original local actions stop explicitly; Explicit /T:FILE.KEY stages ten actions before UART installation. Alt1..Alt0 execute bounded nonblocking TEXT; PROGRAM uses bounded COMSPEC/PATH lookup, static-parent DOS EXEC, serial handoff, screen restoration and a return key prompt. ASPECT/HOOK execution and binding UI remain unfinished.', 'Alt-G freezes80x25 characters through recovered row helpers and appends checked PCPLUS.SCR rows via an independent canonical-path file owner. Far memory is retained across PROGRAM. Full original snapshot/printer/script/UI modes remain unfinished.', 'Alt-F1/F2 processed text capture uses checked append/exclusive creation, pause/resume and periodic buffering. Alt-F3 toggles CR-adds-LF. Write/close failures retain partial logs and sticky exit12; PROGRAM closes capture before EXEC. Full capture/printer/settings/UI and ASPECT modes remain unfinished.', 'Ctrl-backslash enters a serviced raw monitor using the actual UART and renderer. Explicit Y replaces PCPLUS.DMP through a third checked canonical-path owner; other answers select view-only. Binary256-byte buffering, periodic flush and failure-aware shutdown preserve text-capture ownership. Nested local/KEY/PROGRAM owners are blocked; the exact original owner/resolver/prompt remain separate diagnostics. Native HOOK and complete monitor/UI geometry remain unfinished.', 'AltR receives ordinary XMODEM CRC/checksum128/1024 using the real UART and checked staged DOS storage. HARD/NONE only; SOFT rejects before staging. FinalACK follows checked installation. AltS uses the native ordinary sender with checked read-only DOS source files and automatic1K blocks; only actual ACKs advance maintained progress. F2 inside the transfer prompt selects maintained CRC YMODEM batch transfer with checked per-file ownership and exact declared lengths. Window/streaming/other protocols, full transfer settings/UI and physical peers remain unfinished.', 'CtrlPgUp opens a maintained63000-byte frozen history viewer in80x25 BIOS mode3/page0 with local line/page/Home/End navigation, ASCII case-insensitive incremental search/F3 and Escape return to the updated live screen. UART/parser/history/capture/replies continue, with frame swaps at top-level receive/idle and64 search candidates per turn. W appends the frozen snapshot through a fourth checked file owner, expanding CR to CRLF in128-source-byte foreground chunks. Append/create, short writes, cancellation, close ambiguity and DOS child inheritance are checked. Alt-= opens a maintained filename clipboard and C enters it from redisplay. The15-entry list supports bounded extraction, add/edit/delete/purge, tags, runtime decimal separator and one/all/tagged paste. Whole-packet TX admission requires an empty queue; cancellation removes only the unsent prefix and preserves later parser replies. Single removal waits for actual UART acceptance, and connection queue resets retain the entry as interrupted. PRM04EA imports a validated0..255 separator through the44-byte settings plan; PRMEDIT offers46 fields. Live setup applies deliberate saved separator edits and preserves session R across canceled/no-op/unrelated returns using an acknowledged source baseline in the628-byte candidate owner. Full native UI, transfer-prompt workflows and other geometries remain unfinished.', 'PROGRAM preserves DTR, pauses configured flow and releases its UART IRQ during child execution; NONE cannot guarantee incoming-data preservation while a child owns the machine. No physical UART/modem/public BBS validation. ENiGMA editor escape-fragmentation behavior remains a server/packetization compatibility boundary.']}
manifest['experimental_keyboard_bank']=args.keyboard_bank
manifest['experimental_cwd_identities']=args.cwd_identities
manifest['experimental_path_control']=args.path_control
manifest['experimental_file_directory']=args.file_directory
manifest['experimental_file_viewer']=args.file_viewer
manifest['experimental_external_viewer']=args.external_viewer
manifest['experimental_external_editor']=args.external_editor
manifest['experimental_packed_command_ui']=args.packed_command_ui
manifest['experimental_optimize_size']=args.optimize_size
manifest['experimental_chat_loader']=args.chat_loader
manifest['experimental_chat_storage']=args.chat_storage
manifest['experimental_chat_presentation']=args.chat_presentation
manifest['experimental_chat_adapters']=args.chat_adapters
manifest['experimental_chat_text_transport']=args.chat_text_transport
manifest['experimental_chat_echo']=args.chat_echo
manifest['experimental_chat_foreground_text']=args.chat_foreground_text
manifest['experimental_chat_redisplay']=args.chat_redisplay
manifest['experimental_code_label_offsets']=args.code_label_offsets
manifest['experimental_chat_timing']=args.chat_timing
manifest['experimental_chat_frontend']=args.chat_frontend
if chat_loader:manifest['chat_loader']={k:v for k,v in chat_loader.items() if k not in ('objects','inputs')}
if args.optimize_size:manifest['optimized_c_sources']=optimized_c_sources
manifest['packed_command_ui']=packed_command_ui
manifest['experimental_gateway_lookup']=args.gateway_lookup
manifest['experimental_gateway_handles']=args.gateway_handles
manifest['experimental_gateway_files']=args.gateway_files
manifest['experimental_gateway_uart']=args.gateway_uart
manifest['experimental_gateway_frontend']=args.gateway
manifest['diagnostic_gateway_uart_probe']=args.gateway_uart_probe
manifest['diagnostic_gateway_files_probe']=args.gateway_files_probe
manifest['diagnostic_gateway_probe']=args.gateway_probe
manifest['experimental_reset_row_owner']=args.reset_row_owner
manifest['experimental_status_owner']=args.status_owner
manifest['diagnostic_xlt_display_probe']=args.xlt_display_probe
manifest['diagnostic_profile_display_probe']=args.profile_display_probe
manifest['experimental_row_notices']=args.row_notices
manifest['diagnostic_session_rows_probe']=args.session_rows_probe
manifest['diagnostic_aspect_admission_probe']=args.aspect_admission_probe
manifest['experimental_aspect_row_owner']=args.aspect_row_owner
manifest['experimental_program_display_owner']=args.program_display_owner
if args.program_display_owner:manifest['limitations'].append('PROGRAM saves/restores verified25/28/43/50-row text frames and cursor around ordinary DOS children, without changing parent canonical state. Child UART is quieted after DS/SS/SP restoration and before trap resume. Unverified display restoration requests fatal exit2/service6EF7 and skips mouse/flow resume. Inline adopted views keep their existing separate contract. Live preference adoption, arbitrary fonts/VGA-state equivalence, broader composition and physical acceptance remain separate gates.')
manifest['experimental_large_view_frames']=args.large_view_frames
if args.large_view_frames:manifest['limitations'].append('Shared redisplay/reference/browser/clipboard/elapsed frames retain verified25/28/43/50 physical rows. Full history capacity retained; two8000-byte far frames add8000 retained bytes. Specialized owners, online changes and physical acceptance remain separate gates; line-control bindings remain optional.')
manifest['experimental_status_control']=args.status_control
if args.status_control:
 supported_rows='25/28/43/50' if args.large_view_frames and args.program_display_owner else '25'
 manifest['limitations'].append('Ctrl-] and reference/browser Toggle Status dispatch through the guarded offline owner after modal-frame release. Narrow profiles4/6 at'+supported_rows+' physical rows; tracked-online and unsupported geometry refuse. Captured RIS defaults/parser bounds follow visibility. No saved preference rewrite, bridge deployment or physical acceptance.')
manifest['diagnostic_status_probe']=args.status_probe
manifest['experimental_display_row_owner']=args.display_row_owner
manifest['diagnostic_display_row_probe']=args.display_row_probe
manifest['experimental_row_geometry_owner']=args.row_geometry_owner
manifest['experimental_display_preferences']=args.display_preferences
manifest['experimental_display_startup']=args.display_startup
manifest['experimental_line_control']=args.line_control
if args.line_control:manifest['limitations'].append('Ctrl-minus/Toggle Lines uses the accepted selector cycle after releasing menu frames. No imported/accepted preferences gives status7; tracked-online and busy/unsupported states retain guarded refusal/deferral. Saved preferences are not rewritten; live NAWS/BBS/physical acceptance remain separate gates.')
if args.display_startup:manifest['limitations'].append('Imported display preferences apply after baseline capture before UART enable/dialing; no import preserves the default baseline without inventing selector readiness. Verified fallback and fatal refusal retain hardware cleanup. Live adoption/NAWS and BBS/physical acceptance remain separate gates; Toggle Lines is a separate option.')
manifest['experimental_window_size_report']=args.window_size_report
manifest['experimental_input_tables_data']=args.input_tables_data
manifest['diagnostic_row_geometry_probe']=args.row_geometry_owner and args.display_row_probe
if args.display_row_owner:
 manifest['display_row_bank']={k:display_rows_bank[k] for k in ('namespace','native_bytes','segment','offset','bytes','scope','selector_service','selector_transaction')}
 manifest['limitations'].append(display_rows_bank['scope'])
manifest['experimental_local_controls']=args.local_controls
manifest['experimental_screen_pause']=args.screen_pause
manifest['experimental_call_timer']=args.call_timer
manifest['experimental_elapsed_view']=args.elapsed_view
manifest['experimental_manual_init_owner']=args.manual_init_owner
manifest['experimental_manual_init']=args.manual_init
manifest['experimental_auto_answer_owner']=args.auto_answer_owner
manifest['experimental_auto_answer']=args.auto_answer
manifest['experimental_original_keys']=args.original_keys
manifest['experimental_status_geometry']=args.status_geometry
manifest['experimental_original_reference']=args.original_reference
manifest['experimental_directory_view']=args.directory_view
manifest['experimental_directory_preview']=args.directory_preview
manifest['experimental_directory_storage']=args.directory_storage
manifest['experimental_directory_resource_cli']=args.directory_resource_cli
manifest['experimental_directory_resource_owner']=args.directory_resource_owner
manifest['experimental_directory_retirement']=args.directory_retirement
manifest['experimental_directory_translation']=args.directory_translation
manifest['experimental_directory_scripts']=args.directory_scripts
manifest['experimental_directory_compile']=args.directory_compile
manifest['experimental_directory_adopt']=args.directory_adopt
if args.directory_adopt:manifest['limitations'].insert(0,'Preview A applies the staged selection/resources through the quiesced PROGRAM owner; the Connection menu dials the accepted target. Canonical automatic scripts are checked before ASPECT execution. Full application, exhaustive stack/port-race, complete rendering and physical/card acceptance remain open.')
if args.directory_compile:manifest['limitations'].append('Preview C stages resources privately and compiles a SOURCE with direct ASPCOMP under canonical source/output/helper/scratch claims, retaining independent far recovery state. No script execution, selection adoption or dialing.')
if args.directory_scripts:manifest['limitations'].append('Directory script preflight resolves ASX before ASP and streams a32-bit length/CRC32 fingerprint. Header validation is not full bytecode validation. Source candidates still require compilation before adoption; no script is executed or applied by preflight.')
if args.directory_translation:manifest['limitations'].append('Preview R stages XLT with KEY/KBD as one far bundle, retaining original CLI /X identity. No active translation, selected entry, script or dialing is published.')
if args.directory_retirement and not args.directory_adopt:manifest['limitations'].append('Offline pending accounting queues one PROGRAM kind7 attempt per connected event, with no child or acknowledgement prompt. Installed statistics reconcile the frozen logical/setup contexts. Refusals preserve pending counts for shutdown; file recovery is never retried. Selected entry adoption and dialing remain pending.')
if args.directory_resource_owner and not args.directory_adopt:manifest['limitations'].append('Preview R checks KEY/KBD resources through PROGRAM kind6 under UART quiescence. Pending/active guards pin the proposal/bundle until restore. This preflight does not adopt settings/target/accounting or dial; translation/script staging and full live selection remain pending.')
if args.directory_resource_cli and not args.directory_adopt:manifest['limitations'].append('Original CLI KEY/KBD identities are bound before directory startup; staged live resources, lease/UART adoption and dialing remain pending. This experimental build retains the LoC.6 splash version.')
if args.directory_storage and not args.directory_adopt:
 manifest['limitations'].append('LoC.6: record/accounting saves use a banked canonical three-name shared file claim. Close/rollback/recovery-file/release uncertainty holds the owner and the shared DOS EXEC boundary refuses child launch. A refused retry returns no stale installed flag. No force recovery/reset, live selection adoption or new UART handoff is implemented.')
if args.directory_preview and not args.directory_adopt:
 manifest['limitations'].append('LoC.5: Enter in a published Alt-D page stages and previews a selection from the accepted in-memory PRM and actual session capture. Pure preparation runs on a foreground idle turn. The existing empty command snapshot lends1190 more far bytes after its2788-byte page lease. No active target/settings/resource/accounting changes occur; validated adoption and dialing remain pending. Paths retain spellings, not canonical claims; preview success does not prove resource availability or physical compatibility.')
manifest['directory_filesystem_import_adapters']=directory_fs_adapters
if args.directory_view and not args.directory_adopt:
 manifest['limitations'].append('LoC.4: Alt-D opens a serviced read-only directory view. Explicit path, bounded incremental IO and separate far staging publish pages only after complete read/probe/close. Arrows/page/Home/End browse; F2 changes file and F5 reloads. Current target/configuration/connection and deferred accounting identity stay unchanged. This is the view component; live dialing/profile/key/script/translation/accounting adoption remains unfinished. Borrowed startup scratch and empty command snapshot are mutually exclusive with their other owners. Driver call-time and physical serial integrity remain unverified.')
if args.original_reference:
 manifest['limitations']=[s.replace('Alt-F8/menu launches sibling XLTEDIT','Alt-W/browser launches sibling XLTEDIT') for s in manifest['limitations']]
 manifest['limitations'].append('LoC.3 reference candidate: Alt-Z opens the 39-command Communications/Setup/Other Functions reference. Backtick opens the maintained browser. Missing original commands show a nonfatal refusal through the shared serviced view; Alt-D does not secretly redial and Alt-F8 does not open translation editing. Alt-F5 prompts for a script and Alt-W edits translation. Navigation and contextual help are maintained; exact original runtime interaction, original pull-downs and missing services remain open.')
if args.original_keys:
 manifest['limitations']=[s.replace('AltR receives ordinary','The Receive menu action receives ordinary').replace('AltS uses the native','The Send menu action uses the native') for s in manifest['limitations']]
 manifest['limitations'].append('Original-key candidate: Alt-R opens the checked recorder, Alt-S/Alt-P use the saved-settings editor, and Alt-F6 opens redisplay. Existing Alt-F10/Ctrl-PgUp aliases remain. Assigned page-key bindings retain precedence; native-local unassigned PgUp/PgDn opens send/receive. Menu transfers use private actions. Dedicated original line/port UI, Alt-D live chooser and original Alt-Z/pull-down layout remain unfinished.')
manifest['limitations'].append('Alt-Z opens a source-owned five-group command menu, contextual help and bounded ASCII help search. Existing commands run only after the shared redisplay owner restores the live screen; history/clipboard re-enter their usual guards. Incoming UART/parser/history/replies continue while browsing. Menu code and read-only text reside in CONFIG_CODE, with only bounded state/query bytes near. Original pull-down layout, advertised mouse paths, full settings/key editing and other video geometries remain unfinished.')
if args.original_reference:
 manifest['limitations']=[s.replace('Alt-Z opens a source-owned five-group','Backtick opens a source-owned five-group') for s in manifest['limitations']]
manifest['limitations'].append('An otherwise eligible Alt-Z read during normal parser ownership is retained until a distinct resident foreground service can recheck all guards. All BIOS key values, including AX0, retain their key meaning. Subsequent keys remain in the existing32-word typeahead FIFO; repeated Alt-Z coalesces. Escape cancels locally; Alt-X/Alt-H cancel then use normal dispatch. Changed owners/geometry or foreground stop discard the owned pending typeahead. Overflow retains the existing explicit exit3 policy. This is maintained behavior; it does not identify the cause of the earlier unobserved Synchronet refusal.')
manifest['compiler_helper_adapters']={'import_counts':helper_adapters['import_counts'],'record_policy':'Only EXTDEF names/record lengths/checksums change; symbol indices, code, data, local symbols and fixups are preserved.'}
(OUT/'compiler-helper-adapters.json').write_text(json.dumps({'binary_sha256':manifest['binary_sha256'],**helper_adapters},indent=2)+'\n')
manifest['zmodem_compiler_helper_adapters']=zmodem_helper_adapters
(OUT/'zmodem-compiler-helper-adapters.json').write_text(json.dumps({'binary_sha256':manifest['binary_sha256'],**zmodem_helper_adapters},indent=2)+'\n')
manifest['limitations'].append('Maintained YMODEM framing and header codec execute in CONFIG_CODE with unchanged near data and protocol logic. Explicit callbacks bridge resident UART/CRC/file owners; zero-argument callbacks have their own declared family. Newly compiled batch_header OMF imports for Watcom32-bit arithmetic are renamed to local register adapters; all code/data/fixup records and external indices are preserved. Original ordinary XMODEM modules remain resident and unchanged.')
manifest['experimental_external_render']=args.external_render
manifest['experimental_aspect_snapshot_lease']=args.aspect_snapshot_lease
manifest['experimental_mouse']=args.mouse
manifest['experimental_notice_input']=args.notice_input
manifest['terminal_exit_guard']=args.exit_guard
manifest['terminal_exit_probe']=args.exit_probe
manifest['banked_process']=args.process_bank
manifest['experimental_session_capture']=args.session_capture
manifest['experimental_session_projection']=args.session_projection
manifest['session_projection_probe']=args.projection_probe
manifest['experimental_session_baseline']=args.session_baseline
manifest['experimental_register_handoff']=args.register_handoff
manifest['experimental_session_controls']=args.session_controls
manifest['experimental_hook_return']=args.hook_return
manifest['experimental_hook_execute']=args.hook_execute
manifest['experimental_hook_modem']=args.hook_modem
manifest['experimental_hook_input']=args.hook_input
manifest['experimental_hook_apply']=args.hook_apply
manifest['experimental_hook_lookup']=args.hook_lookup
manifest['hook_input_probe']=args.input_probe
manifest['hook_transaction_probe']=args.hook_probe
manifest['terminal_traps']=args.traps
manifest['terminal_trap_probe']=args.trap_probe
if args.custom_irq:manifest['experimental_custom_irq']=True
if args.special_edition:manifest['special_edition']=True
if args.phone_log_bank:
 manifest['experimental_phone_log_bank']=True
 if args.phone_log_startup:manifest['experimental_phone_log_startup']=True
 if args.phone_log_lifecycle:manifest['experimental_phone_log_lifecycle']=True
 if args.phone_log_events:manifest['experimental_phone_log_events']=True
 if args.phone_log_disk:manifest['experimental_phone_log_disk']=True
 if args.phone_log_controls:manifest['experimental_phone_log_controls']=True
 manifest['phone_log_compiler_adapters']=phone_log_bank['adapters']
 if args.phone_log_controls:
  manifest['limitations'].append('Alt-Z File call-log pane shows retained status and offers confirmed RAM-only safe retry. Uncertain handles/recovery and uncaptured event faults cannot be cleared. No complete transport, original menu or physical acceptance yet.')
 elif args.phone_log_disk:
  manifest['limitations'].append('Guarded main-loop one-record append and bounded shutdown draining. Online NONE flow defers to idle/offline/shutdown. No retry/recovery UI or complete sustained/physical/child acceptance yet.')
 elif args.phone_log_events:
  manifest['limitations'].append('RAM session admission/CONNECT/disconnect/shutdown hooks are wired. No live disk scheduler; queued records explicitly fail shutdown with error12 and an unsaved notice. Physical carrier/child-clock acceptance remains open.')
 else:
  manifest['limitations'].append('Checked call-log code bank linked with retained far event storage and explicit DOS/CRT callbacks. No modem events or poll scheduling are wired yet; startup PRM/path adoption is optional; this build does not produce a live telephone log.')
 if args.phone_log_reservations:manifest['experimental_phone_log_reservations']=True
 else:manifest['limitations'].append('The queue does not yet acquire shared file reservations in this variant.')
if args.native_reset_bank:
 manifest['experimental_native_reset_bank']=True
 manifest['native_reset_overlay']=not args.native_reset_static
 manifest['native_reset_namespace']=reset_bank['namespace']
 manifest['native_reset_transaction']=args.native_reset_transaction
 manifest['limitations'].append(reset_bank['scope'])
if args.auto_answer:
 manifest['limitations'].append('Experimental Alt-Y/reference/browser sends the configured answer-on field with guarded ownership, captured duplex and physically accepted ordinary-byte echo. Configured information sound uses a nonblocking440Hz/four-BIOS-tick generation-owned tone and serviced status-row notice. Requires reserved24-row terminal inside BIOS80x25 color text/page0. This is not a toggle, ACK/dial operation, online escape or original calibrated timing/pixel equivalence. Source/DOS/BBS/package/physical acceptance require scoped evidence for this image.')
if args.auto_answer_owner and not args.auto_answer:
 manifest['limitations'].append('Typed answer-on component links the bounded send owner with captured local echo after physical acceptance and a renderer reentrancy guard. No Alt-Y/reference/browser/configured answer-on binding or sound/notice UI. Existing Init remains no-echo. No automatic toggle, answer-off selection, dial, ACK, escape prefix or call event. Native pre-write echo/calibrated pacing equivalence and actual DOS/BBS/physical acceptance are not established by this component build.')
if args.manual_init_owner and not args.manual_init:
 manifest['limitations'].append('Isolated manual Init send owner is linked for component verification only. No Alt-J/menu binding, dispatcher output exclusion or automatic carrier-loss cancellation. Caller supplies an exclusive physical-write grant and cancel/loss/exit notification. Native bounded expansion and send-only bytes are retained; maintained ordinary pacing is one BIOS tick and pauses ten ticks, not calibrated-native timing equivalence. Partial physical command debt is reported without inserting recovery bytes or retiring the call. Do not deploy this component candidate as an enabled manual-init release.')
if args.manual_init:
 manifest['limitations'].append('Experimental Alt-J/reference/browser manual Init uses guarded admission, exclusive foreground command output, deferred ordinary keys, actual qualified DCD/exit/cancel hooks and existing startup partial-line retry. Sends configured initialization only: no ACK wait, dial, echo, settings loan or call-timer event. Ordinary incoming data/CPR remains serviced. Maintained BIOS pacing is not calibrated-native timing equivalence. Actual DOS/BBS/package and physical acceptance require separate evidence for this image.')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built',str((OUT/'TERMINAL.EXE').relative_to(ROOT)),manifest['binary_sha256'],'DS/SS bytes',manifest['data_stack_bytes'])
