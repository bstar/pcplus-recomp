# Recorder marker and late File Base footer

The placement-only normal attempt was deliberately stopped after its helper
remained phase0. Its [failure evidence](validation/recording-marker-layout-stopped.json)
is preserved; the linked layout cases do not prove the whole live workflow.
The [current fixture also waits for the plain bottom filter](RECORDING_FOOTER_READINESS.md)
before displaying readiness.

The [audio visibility diagnostic](validation/recording-marker-audio-diagnostic.json)
observed one76-sample run of `RECORDER READY`, followed by its disappearance.
The helper needed91 consecutive samples, delivered zero recipe keys, had no
BIOS queue retries and exited at its12000-tick watchdog. The marker was visible
for about4.1 seconds between its first/last matching samples. This narrows the
failure to loss of readiness visibility; it does not establish normal audio
acceptance.

The retained late458-byte ENiGMA fragment redraws the File Base title/filter,
prompt and clock using fixed cursor positions. It erases the preceding local
marker in the current renderer under placements consistent with the observed
post-MESSAGE cursor. This is a linked-instruction counterexample with modeled
hardware, not a claim to have sampled every intermediate video frame.

Both audio and TCP fixtures now use the same source-owned MESSAGE string:

~~~text
message "^M^JRECORDER READY^M^J^M^J"
~~~

The existing native MESSAGE handler appends another CRLF. The extra separating
lines place the marker above the footer's repaint area. The helper's marker
requirement,90-tick initial dwell, key pacing, final-screen stability checks and
ordinary32000-tick watchdog remain unchanged. The test fixture changes; the
application executables retain their admitted identities.

[Forty renderer cases](validation/recording-marker-layout.json) cover profiles4/6,
scroll bottoms23/24, selected bottom-row cursor positions, and late fragments
whose leading LF is pending or already consumed. Both old and revised layouts
are measured. The preceding layout survives some geometries; the revised marker
survives all selected cases. The captured footer is an owned lab fragment with
provenance and hashes in `lab/bbs/recording_marker_footer.json`, excluding login
data and page artwork.

The placement-only ordinary-helper TCP control passed13 checks, including actual
recorded bytes, DOS compilation/replay, manual Search, timer and hardware
restoration. Its ordinary SIP/audio run did not establish the complete workflow;
the current footer-gated run remains unverified. Diagnostic results remain ineligible
for production acceptance; physical Boca/SPA2102 and full application
requirements remain open.
