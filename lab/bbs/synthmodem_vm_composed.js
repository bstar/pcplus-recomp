'use strict';
// Actual candidate classes and booted helper; SIP/DSP resources stay unopened.
const assert=require('assert/strict'), fs=require('fs'), path=require('path');
const net=require('net'), Module=require('module'), crypto=require('crypto');
const {EventEmitter}=require('events');
const candidate=path.resolve(process.argv[2]), out=path.resolve(process.argv[3]);
const checks={}, errors=[], sockets=[], servers=[];
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function until(test,ms=15000){
  const end=Date.now()+ms;
  while(!test()){assert(Date.now()<end,'Observation deadline');await delay(5);}
}
function load(name){
  const file=path.join(candidate,name),real=Module.createRequire(file),cfg=real(path.join(candidate,'config.js'));
  cfg.logging.level='error';
  Object.assign(cfg.modem.native,{postTrainIdleMs:0,postTrainQuiescenceMs:0,postTrainAttachMaxMs:100});
  Object.assign(cfg.telnet,{terminalType:'ANSI',terminalCols:80,terminalRows:25,
    allowedHosts:['127.0.0.1'],blockedHosts:[],connectTimeoutMs:3000,idleTimeoutMs:0,
    menuIdleHeartbeatMs:0,proxyEscapeByte:null,negotiateOptions:false});
  cfg.terminal.banner='';cfg.terminal.prompt='';cfg.terminal.localEcho=false;
  const unopened=new Set(['../tunnel/UdpTcpTunnel','../sip/SipUacInternal','../sip/VmRegistrar',
    '../rtp/RtpBridge','../rtp/RtpSession','../dsp/AudioCapture']);
  const m=new Module(file);m.filename=file;m.paths=Module._nodeModulePaths(path.dirname(file));
  m.require=n=>unopened.has(n)?new Proxy({}, {get:()=>function(){throw Error('Unrequested SIP/DSP resource');}}):real(n);
  m._compile(fs.readFileSync(file,'utf8'),file);return m.exports;
}
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const encode=b=>Buffer.from(b.toString('latin1').replace(/\xff/g,'\xff\xff'),'latin1');
async function listen(callback){
  const server=net.createServer(p=>{sockets.push(p);p.on('error',e=>errors.push(e.message));callback(p);});
  servers.push(server);await new Promise(r=>server.listen(0,'127.0.0.1',r));return server.address().port;
}
async function main(){
  const {PjsipBackend}=load('src/backends/PjsipBackend.js');
  const {CallSession}=load('src/session/CallSession.js');
  const {TelnetProxy}=load('src/telnet/TelnetProxy.js');
  const b=new PjsipBackend({qemuPath:'unused',kernelPath:'unused',initrdPath:'unused'});
  let ctrl,modem,bbs,hello='',connected=0,info,session,drains=0,stage='commands';
  let command=Buffer.alloc(0),modemBytes=0,wireBytes=0,bbsBytes=0,reverseCount=0,telnetState=0;
  const modemChunks=[],wireChunks=[],bbsChunks=[],reverseChunks=[];
  const payload=Buffer.alloc(16*1024*1024+3);
  for(let i=0;i<payload.length;i++)payload[i]=i&255;
  const marker=Buffer.from('PCPLUS-COMPOSED-PAYLOAD-BEGIN\r\n');
  b.on('error',e=>errors.push(e.message));b.on('hello',text=>hello=text);
  b.on('drain',()=>drains++);
  // Physical SIP startup is deliberately outside this harness. CONNECT is not
  // forced: it must come through the actual guest and backend control parser.
  b.on('connected',value=>{
    connected++;info=value;
    session=Object.create(CallSession.prototype);EventEmitter.call(session);
    Object.assign(session,{_active:true,_dsp:b,_id:'vm-composed',_telnet:new TelnetProxy(),_mode:'b2bua',
      _dialog:{canBye:()=>false},_capture:null,_rtpSock:null,_rtpPort:0,_dspIsPooled:false,_connectInfo:value});
    session._onModemConnected();
  });
  const controlPort=await listen(p=>{
    ctrl=p;b.controlSocket=p;b.state='READY';
    p.on('data',chunk=>{wireChunks.push(Buffer.from(chunk));wireBytes+=chunk.length;});
    b._setupControlParser();
    b._ctrlParser.on('error',e=>errors.push(e.message));
  });
  const modemPort=await listen(p=>{
    modem=p;p.on('data',chunk=>{
      modemChunks.push(Buffer.from(chunk));modemBytes+=chunk.length;
      if(stage==='commands'){
        command=Buffer.concat([command,chunk]);
        if(command.length>=9){
          assert.deepEqual(command,Buffer.from('ATZ\rATD1\r'));
          stage='online';p.write(Buffer.from('\r\nOK\r\nCONNECT 14400\r\n'));
        }
      }
    });
  });
  const bbsPort=await listen(p=>{
    bbs=p;p.on('data',chunk=>{
      bbsChunks.push(Buffer.from(chunk));bbsBytes+=chunk.length;
      // Independent Telnet observer: consume negotiation triplets, preserve
      // doubled IAC. No candidate codec is used as the reverse-byte oracle.
      const bytes=[];
      for(const v of chunk){
        if(telnetState===0){if(v===255)telnetState=1;else bytes.push(v);}
        else if(telnetState===1){
          if(v===255){bytes.push(v);telnetState=0;}
          else {assert(v>=251 && v<=254,'Unexpected Telnet command');telnetState=2;}
        }else telnetState=0;
      }
      if(bytes.length){const data=Buffer.from(bytes);reverseChunks.push(data);reverseCount+=data.length;}
    });
    p.write(Buffer.from([255,251,0,255,253,0]));p.write(marker);p.write(encode(payload));
  });
  fs.writeFileSync(path.join(out,'ports.json'),JSON.stringify({controlPort,modemPort,bbsPort}));
  try{
    await until(()=>hello && modem);checks.guest_hello=hello.includes('pcplus-nix-i386');
    assert.equal(b._connected,false);b.sendAt('ATZ');b.sendAt('ATD1');
    await until(()=>session && session._telnet._txCallback);
    checks.actual_guest_backend_CONNECT=connected===1 && info.bps===14400 && b._currentBps===14400;
    checks.coalesced_commands_exact=command.equals(Buffer.from('ATZ\rATD1\r'));
    modem.pause();modem.write(Buffer.from(`127.0.0.1:${bbsPort}\r`));
    await until(()=>session._telnet._outputBlocked,20000);
    checks.bbs_reads_paused=session._telnet._tcpSocket.isPaused();
    const paused={ring:b._dataWriter.length,socket:ctrl.writableLength};
    checks.retained_ring_bounded=paused.ring<=262144;
    modem.resume();
    // AT bytes precede bridge connection messages, then a unique payload marker.
    await until(()=>modemBytes>=9+marker.length+payload.length,30000);
    let forward=Buffer.concat(modemChunks),start=forward.indexOf(marker);
    assert(start>=9,'Missing payload marker');
    await until(()=>modemBytes>=start+marker.length+payload.length,30000);
    forward=Buffer.concat(modemChunks);start=forward.indexOf(marker);
    const recovered=forward.subarray(start+marker.length);
    checks.forward_exact=recovered.equals(payload);
    checks.session_survives_pressure=session._active && connected===1;
    checks.drain_observed=drains>0;
    // Reverse path is read continuously: native/DSP and reverse-TCP pressure
    // support are not inferred from this exact-data test.
    modem.write(payload);
    await until(()=>reverseCount>=payload.length,30000);
    const reverse=Buffer.concat(reverseChunks);
    checks.reverse_exact=reverse.equals(payload);checks.telnet_observer_complete=telnetState===0;
    fs.writeFileSync(path.join(out,'modem-wire.bin'),forward);
    fs.writeFileSync(path.join(out,'bbs-wire.bin'),Buffer.concat(bbsChunks));
    fs.writeFileSync(path.join(out,'control-wire.bin'),Buffer.concat(wireChunks));
    const writer=b._dataWriter;
    const ended=new Promise(r=>session.once('ended',r));session.hangup('test');await ended;
    await until(()=>ctrl.destroyed);
    checks.teardown_retires_writer=writer.closed && b._dataWriter===null;
    checks.teardown_removes_drains=b.listenerCount('drain')===1 && ctrl.listenerCount('drain')===0;
    checks.session_closed=!session._active && session._telnet.state==='CLOSING';
    checks.no_errors=errors.length===0;
    const result={passed:Object.values(checks).every(Boolean),checks,errors,
      forward_bytes:recovered.length,reverse_bytes:reverse.length,payload_sha256:hash(payload),
      forward_sha256:hash(recovered),reverse_sha256:hash(reverse),paused,drains,connected,
      modem_payload_offset:start+marker.length,control_wire_bytes:wireBytes,bbs_wire_bytes:bbsBytes,
      connect:{bps:info.bps,protocol:info.protocol},node:process.version,
      configuration:{holdMs:0,quiescenceMs:0,attachMaxMs:100,terminalType:'ANSI',cols:80,rows:25,
        negotiateOptions:false,menuEscape:null},
      scope:'Actual candidate backend parser/writer and CallSession attach/teardown with booted i386 helper. Synthetic modem endpoint and modeled SIP ownership; no DSP/SIP/audio, DOS/BBS software or hardware.'};
    fs.writeFileSync(path.join(out,'node-result.json'),JSON.stringify(result,null,2)+'\n');
    assert(result.passed,JSON.stringify(checks));
  }finally{
    if(session?._active)session.hangup('cleanup');else await b.stop();
    for(const p of sockets)p.destroy();
    for(const server of servers)await new Promise(r=>server.close(r));
  }
}
main().catch(e=>{fs.writeFileSync(path.join(out,'node-error.txt'),e.stack+'\n');process.exitCode=1;});
