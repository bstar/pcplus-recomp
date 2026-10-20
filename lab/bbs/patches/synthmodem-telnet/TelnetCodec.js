'use strict';
// Maintained SynthModem bridge candidate. SPDX-License-Identifier: GPL-2.0-or-later
// No DSP or serial-terminal work belongs here: this owns Telnet framing only.
const IAC = 255, DO = 253, DONT = 254, WILL = 251, WONT = 252, SB = 250, SE = 240;
const BINARY = 0, ECHO = 1, SGA = 3, TTYPE = 24, NAWS = 31;

class TelnetCodec {
  constructor({ send, display, terminalType = 'ANSI', terminalCols = 80, terminalRows = 25 }) {
    if (!/^[\x20-\x7e]{1,64}$/.test(terminalType)) throw new Error('Invalid terminal type');
    for (const n of [terminalCols, terminalRows]) {
      if (!Number.isInteger(n) || n < 1 || n > 65535) throw new Error('Invalid dimensions');
    }
    this.send = send;
    this.display = display;
    this.type = terminalType;
    this.cols = terminalCols;
    this.rows = terminalRows;
    this.local = new Set();
    this.remote = new Set();
    this.localPending = new Set();
    this.remotePending = new Set();
    this.state = 'data';
    this.sub = [];
    this.rxCR = false;
  }

  static escape(data) {
    const out = [];
    for (const b of data) { out.push(b); if (b === IAC) out.push(b); }
    return Buffer.from(out);
  }

  command(verb, option) { this.send(Buffer.from([IAC, verb, option])); }
  subneg(data) { this.send(Buffer.concat([Buffer.from([IAC, SB]), TelnetCodec.escape(data), Buffer.from([IAC, SE])])); }

  start() {
    // This owner only initiates enable requests, never queued enable/disable
    // reversals. Pending sets suppress acknowledgment loops for crossed offers.
    for (const option of [BINARY, SGA, TTYPE, NAWS]) {
      this.localPending.add(option); this.command(WILL, option);
    }
    for (const option of [BINARY, SGA, ECHO]) {
      this.remotePending.add(option); this.command(DO, option);
    }
  }

  negotiate(verb, option) {
    const local = verb === DO || verb === DONT;
    const enabled = local ? this.local : this.remote;
    const pending = local ? this.localPending : this.remotePending;
    const positive = verb === DO || verb === WILL;
    const yes = local ? WILL : DO, no = local ? WONT : DONT;
    const supported = (local ? [BINARY, SGA, TTYPE, NAWS] : [BINARY, SGA, ECHO]).includes(option);
    const wasPending = pending.delete(option);
    if (!positive) {
      if (enabled.delete(option)) this.command(no, option);
      return;
    }
    if (!supported) { this.command(no, option); return; }
    if (enabled.has(option)) return;
    enabled.add(option);
    if (!wasPending) this.command(yes, option);
    if (local && option === NAWS) {
      const size = Buffer.alloc(5);
      size[0] = NAWS; size.writeUInt16BE(this.cols, 1); size.writeUInt16BE(this.rows, 3);
      this.subneg(size);
    }
    if (!local && option === BINARY) this.rxCR = false;
  }

  finishSub() {
    if (this.sub.length === 2 && this.sub[0] === TTYPE && this.sub[1] === 1 && this.local.has(TTYPE)) {
      this.subneg(Buffer.concat([Buffer.from([TTYPE, 0]), Buffer.from(this.type, 'ascii')]));
    }
    this.sub = [];
    this.state = 'data';
  }

  feed(data) {
    const out = [];
    const payload = b => {
      if (!this.remote.has(BINARY)) {
        // In NVT, CR NUL means literal CR; preserve CR LF as two bytes.
        const skip = this.rxCR && b === 0;
        this.rxCR = b === 13;
        if (skip) return;
      }
      out.push(b);
    };
    for (const b of data) {
      switch (this.state) {
        case 'data': if (b === IAC) this.state = 'iac'; else payload(b); break;
        case 'iac':
          if (b === IAC) { payload(b); this.state = 'data'; }
          else if ([DO, DONT, WILL, WONT].includes(b)) { this.verb = b; this.state = 'option'; }
          else if (b === SB) { this.sub = []; this.state = 'sub'; }
          else this.state = 'data'; // Two-byte Telnet commands are not screen data.
          break;
        case 'option': this.negotiate(this.verb, b); this.state = 'data'; break;
        case 'sub':
          if (b === IAC) this.state = 'subiac';
          else if (this.sub.length < 1024) this.sub.push(b);
          else { this.sub = []; this.state = 'discard'; }
          break;
        case 'subiac':
          if (b === SE) this.finishSub();
          else if (b === IAC && this.sub.length < 1024) { this.sub.push(b); this.state = 'sub'; }
          else { this.sub = []; this.state = 'discard'; }
          break;
        case 'discard': if (b === IAC) this.state = 'discardiac'; break;
        case 'discardiac': this.state = b === SE ? 'data' : 'discard'; break;
        default: throw new Error('Invalid Telnet framing state');
      }
    }
    if (out.length) this.display(Buffer.from(out));
  }

  encode(data) {
    if (this.local.has(BINARY)) return TelnetCodec.escape(data);
    // Encode a serial CR immediately as CR NUL, so Enter never waits for a
    // subsequent chunk. CR NUL LF also has the intended CR+LF NVT meaning.
    const nvt = [];
    for (const b of data) { nvt.push(b); if (b === 13) nvt.push(0); }
    return TelnetCodec.escape(nvt);
  }
}

module.exports = { TelnetCodec };
