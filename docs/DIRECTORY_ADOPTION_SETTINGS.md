# Selection and settings workflows

The directory-adoption candidate now has native DOS evidence for a deferred
IRQ change through the complete preview Apply action, and for settings saved
or cancelled after Apply and a PROGRAM directory change. This checkpoint adds
test coverage; the application and PRMEDIT bytes are unchanged from the
[IRQ/settings-path fix](IRQ_HANDOFF_AND_SETTINGS_PATH.md).

Preview uses the application's last accepted PRM image. Replacing the file
outside the application does not automatically replace that image. The tested
IRQ workflow saves through PRMEDIT and declines its immediate hardware offer:

1. COM3 uses IRQ5. PRMEDIT saves IRQ3, IRQ4 or IRQ7 in the source PRM.
2. The user declines the immediate port/IRQ change. The saved image becomes
   the accepted baseline, while the actual session remains on IRQ5.
3. Alt-D preview A stages the selected resources and applies the saved IRQ.
4. Exact session fields are checked at the result prompt and after return.
   A passive timer observes the new IRQ active with the old mask released.
   All four UART/PIC/vector exit snapshots match their initial values.

All three target IRQ workflows pass. The IRQ3 case also selects profile4;
IRQ4/IRQ7 select profile6. The observer verifies the current IRQ masked at each
DOS boundary during handoff. The old IRQ can legitimately be released during
the target vector operations; it is no longer treated as the active IRQ.
No application routine, RAM state, return value, or UART write is supplied by
the observer. Actual PRMEDIT keyboard input creates the new accepted image.

Two additional workflows begin with a profile4 PRM and select a profile6
directory entry. They run an actual PROGRAM `CD` to another directory, where a
different valid `TEST.PRM` exists. Alt-S then opens the original canonical PRM:

- Save changes its normal attribute to `1E`. Only the canonical PRM changes;
  its saved source profile remains4, the selected live profile remains6, and
  subsequent BBS text uses attribute `1E`.
- Cancel discards the staged edit. Both PRMs remain unchanged, the selected
  profile remains6, and subsequent BBS text retains attribute `07`.

Both workflows then dial the selected endpoint through DOSBox's modem model,
answer the peer's real DA/CPR queries, and execute the selected canonical
script rather than the CWD decoy. The profile claim is checked by the terminal's
actual DA response, independently of the saved source PRM. Ordinary read-only
resource checks and the default Apply workflow also pass unchanged.

See [the receipt](validation/directory-adoption-settings.json) for hashes,
reports and checked assertions. The application remains
`da09b00dde9ee9008295e53c96aaa8630b9a4e19f1a78dc683e89e4b3186f650`;
PRMEDIT remains
`9cc71319162e7e7ff1a242081c6f1b4af124e521a342e1c01e5409bdffd3f977`.
The prior committed-source reproduction of all ten package files still applies
to these exact bytes. Earlier receipts retain their historical scopes.

The IRQ fixtures use an emulated dummy UART; the connection fixtures use a
loopback TCP peer and emulated modem carrier. They do not establish physical
Boca/SPA2102 behavior, sustained data/transfer acceptance, complete ENiGMA
rendering or full application coverage. No live bridge/BBS/network or card was
changed.
