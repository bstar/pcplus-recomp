# V.22 originating caller candidate

An isolated source patch against SynthModem commit
`b1752e4d0039e0cff72735924e03aa99922723a8`, file
`src/dsp/protocols/V22.js` (stock SHA256
`ba5ed8e05029d37ef1830091768327630eb01916e45cb893e067c99408f6f783`).
This is a separately staged candidate; installed services and the source
checkout are unchanged. The upstream source is GPL-2.0-or-later; retain its
[notices](../synthmodem-telnet/UPSTREAM-NOTICES.txt) when distributing it.

The stock native V22 wrapper uses the answer-side startup sequence for both
roles: the originating side immediately emits unscrambled marking and a guard
tone. The real VM answering DSP does not complete a connection with that caller.
The preserved baseline run times out with no CONNECT and no decoded data.

[ITU-T V.22](https://www.itu.int/rec/T-REC-V.22), sections2.1 and6.3.1.1, requires
the caller to listen first, recognize the answerer's unscrambled signal, delay
its response, then send scrambled marking. Guard tone belongs to the high
channel. The candidate adds a separate originating sequence using the existing
modulator/demodulator. USB1 detection is qualified over155ms, the response delay
is456ms and data admission follows receiver training plus765ms. Timed output
transitions split the sample block at the boundary instead of depending on a
wall-clock timeout. Silence, plain answer tone and USB1 without completion of
receiver training cannot establish a connection.

The signal checker covers initial silence, rejection of unrelated tones and a
short USB burst, response with/without high-channel guard, exact sample delay,
chunk-independent waveform, absence of low-channel guard, USB-only rejection
and100 identical answer-side output blocks. It also reproduces the baseline's
immediate-transmit defect. The [VM training runner](../../synthmodem-training.md)
stages the patch, runs this checker and then uses actual native/guest DSPs for
CONNECT and exact duplex bytes. No tests force either connected flag or inject
decoded user data.

This covers a fixed V.22/1200 caller in the measured loopback conditions. It
does not implement originate-side V.22bis, establish V.8/V.32bis/14400, prove
noise or timing tolerance, or establish real modem/ATA compatibility. The
answer-side protocol algorithm is preserved; waveform comparisons are a
regression check, not a full answer-side interoperability certification.
