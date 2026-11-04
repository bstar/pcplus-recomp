'use strict';
// Synthetic public test configuration; never copy a user's bridge config here.
module.exports = {
 logging: {level: 'error', timestampFormat: 'unix', colorize: false},
 telnet: {terminalType: 'ANSI', terminalCols: 80, terminalRows: 24,
  negotiateOptions: true, inputSequenceTimeoutMs: 0, proxyEscapeByte: null,
  idleTimeoutMs: 0, connectTimeoutMs: 2000, menuIdleHeartbeatMs: 0,
  allowedHosts: [], blockedHosts: []},
 terminal: {banner: 'SynthModem\r\n', prompt: 'CONNECT> ', lineEnding: '\r\n',
  localEcho: true, defaultPort: 23, aliases: {loc: '127.0.0.1:2323'}}
};
