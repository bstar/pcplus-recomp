'use strict';
// Owned loopback test adapter: synthetic Hayes call, real SynthModem TelnetProxy.
const fs = require('fs');
const path = require('path');
const net = require('net');
const candidate = path.resolve(process.argv[2]), output = path.resolve(process.argv[3]);
const cfg = require(path.join(candidate, 'config.js'));
cfg.logging.level = 'error';
Object.assign(cfg.telnet, { terminalType: 'ANSI', terminalCols: 80, terminalRows: 25,
  allowedHosts: ['127.0.0.1'], blockedHosts: [], idleTimeoutMs: 0,
  menuIdleHeartbeatMs: 0, proxyEscapeByte: null, negotiateOptions: true });
const { TelnetProxy } = require(path.join(candidate, 'src/telnet/TelnetProxy.js'));
const serialIn = [], serialOut = [], commands = [], states = [];
const clients = new Set();
const server = net.createServer(socket => {
  clients.add(socket);
  let online = false, line = [];
  const proxy = new TelnetProxy();
  const send = data => { serialOut.push(Buffer.from(data)); socket.write(data); };
  proxy.on('disconnect', () => { proxy.disconnect(); socket.end(); });
  socket.on('data', data => {
    serialIn.push(Buffer.from(data));
    if (online) { proxy.receive(data); return; }
    for (let i = 0; i < data.length; i++) {
      const b = data[i];
      if (b !== 13) { line.push(b); continue; }
      const command = Buffer.from(line).toString('ascii'); line = []; commands.push(command);
      if (command === 'ATZ') send(Buffer.from('\r\nOK\r\n'));
      else if (command === 'ATD1') {
        online = true; send(Buffer.from('CONNECT\r\n'));
        proxy.attach(send, { protocol: 'SYNTHETIC', bps: 0 });
        if (i + 1 < data.length) proxy.receive(data.subarray(i + 1));
        break;
      } else send(Buffer.from('\r\nERROR\r\n'));
    }
  });
  socket.on('error', error => states.push({ error: error.message }));
  socket.on('close', () => { states.push({ finalProxyState: proxy.state }); proxy.disconnect(); clients.delete(socket); });
});
server.listen(0, '127.0.0.1', () => {
  fs.writeFileSync(path.join(output, 'serial-port.json'), JSON.stringify({ port: server.address().port }));
});
process.on('SIGTERM', () => {
  for (const socket of clients) socket.destroy();
  server.close();
  fs.writeFileSync(path.join(output, 'node-serial-in.bin'), Buffer.concat(serialIn));
  fs.writeFileSync(path.join(output, 'node-serial-out.bin'), Buffer.concat(serialOut));
  fs.writeFileSync(path.join(output, 'node-events.json'), JSON.stringify({ commands, states }, null, 2));
  setImmediate(() => process.exit(0));
});
