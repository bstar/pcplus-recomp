# Automatic ASPECT login and BBS editor compatibility

The shared renderer now passes automatic directory-script login followed by
the stock Synchronet editor. Stock ENiGMA also passes with **explicit 30 ms
modem buffering and the standard network keymap**. Immediate forwarding still
fails ENiGMA's Home and Insert editor checks. These are separate outcomes, not
a universal compatibility result.

[The validation record](validation/script-bbs.json) binds four actual DOS runs
to terminal `dacbd777…e66ae` and, for scripted runs, child `3369c3cb…d2ddbf`.
The scripts send credentials; keyboard schedules contain no username/password.
Both servers use owned loopback accounts. All drafts remain unsaved. Directory
accounting, normal DOS return and before/after UART/vector state are checked.

| Workflow | Modem buffering | Result |
| --- | --- | --- |
| Synchronet, automatic script, standard keys | 0 ms | Login and all 12 editor checks pass; draft aborted |
| ENiGMA, keyboard login, standard keys | 0 ms | Login/editor entry pass; Home and Insert checks fail |
| ENiGMA, automatic script, optional control keys | 0 ms | Login passes once; Home and Insert checks fail |
| ENiGMA, automatic script, standard keys | 30 ms | Login and all seven editor checks pass; disconnect without saving |

The ENiGMA input/editor sources remain byte-identical to pinned revision
`6c25317168b762f7d9088a54d3f8295438827a0e`. Its decoder processes escape sequences
within each received data chunk. Earlier [stream-decoder experiments](ENIGMA_KEY_STREAM_DOS.md)
establish that fragmented key sequences can fail with an unchanged DOS terminal.
Buffering is in the modeled modem, not a server change or a terminal query shim.
This proves one explicit emulated configuration; physical modem packetization,
network delays and other menus still require testing.

The optional ENiGMA control-key profile does not solve this stock menu setup.
`loc-message_base.hjson` binds Ctrl-A to `editModeChangeSubject`, intercepting
the editor's alternative Home control. The failed run shows the marker text
going into the subject instead of moving to the start of the body. Keep this
failure when evaluating alternative keymaps.

The automatic ENiGMA probe waits for the matrix and password-form text, then
uses native WAITQUIET to drain form rendering and terminal negotiation before
transmitting each field. Its twelve-character test password is explicit ASPECT
data: the native directory password field supports ten characters. The first
authored fixture incorrectly crossed that field and was rejected before
connection; its evidence and exact probe source remain under
`build/bbs-lab/script-login/render-v4-dac-enigma-script01/`. The corrected
immediate/control-key failure is `render-v4-dac-enigma-script02`; neither is
overwritten by the buffered success.

Run sequentially against the already configured owned servers, choosing new
labels to preserve earlier evidence:

```sh
./tools/dev --command python3 lab/bbs/directory_script_dos_probe.py --label sync-script-new
./tools/dev --command python3 lab/bbs/packetization_editor_probe.py --delay-ms 0 --label enigma-immediate-new
./tools/dev --command python3 lab/bbs/enigma_directory_script_probe.py --profile network --packet-delay-ms 30 --label enigma-buffered-script-new
```

`standalone/record_script_bbs.py` verifies the frozen checkpoint identities and
records both successes and failures. CTS is held ready by DOSBox-X; physical
RS-232/Wi-Fi modem behavior and all full-application gates remain open.
