'use strict';
// Synthetic local Hayes control; all online data uses real SIP/RTP/DSP/gateway.
const fs=require('fs'),path=require('path'),net=require('net'),dgram=require('dgram');
const runtime=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]),src=n=>path.join(runtime,'source',n);
const trace=process.argv[4]==='--receive-trace'?new (require('./receive_trace_io.js').ReceiveTrace)(out):null;
const internal=process.argv.some(v=>v==='--lifecycle'||v==='--carrier')?new (require('./internal_sip_capture.js').InternalSipCapture)(out):null;
const cfg=require(src('config.js'));
cfg.logging.level='info';cfg.logging.colorize=false;cfg.modem.backend='slmodemd-pjsip';cfg.modem.captureAudio=false;
cfg.modem.native.forceProtocol='V22';cfg.rtp.bindAddress='127.0.0.1';cfg.rtp.portMin=42000;cfg.rtp.portMax=42100;
cfg.sip.host='127.0.0.1';cfg.sip.publicHost='127.0.0.1';
Object.assign(cfg.terminal,{banner:'PCPLUS DSP LAB {{protocol}} {{bps}}\n',prompt:'CONNECT> ',lineEnding:'\r\n',localEcho:false});
Object.assign(cfg.telnet,{terminalType:'ANSI',terminalCols:80,terminalRows:25,allowedHosts:['127.0.0.1'],blockedHosts:[],
 idleTimeoutMs:0,menuIdleHeartbeatMs:0,proxyEscapeByte:null,negotiateOptions:true,inputSequenceTimeoutMs:process.argv.includes('--key-framing')?250:0});
const {SipServer}=require(src('src/sip/SipServer.js'));
const {SipUacInternal}=require(src('src/sip/SipUacInternal.js'));
const {CallSession}=require(src('src/session/CallSession.js'));
const {PjsipBackend}=require(src('src/backends/PjsipBackend.js'));
const {ModemBackendPool}=require(src('src/backends/ModemBackendPool.js'));
const {ModemDSP}=require(src('src/dsp/ModemDSP.js'));
const {RtpSession}=require(src('src/rtp/RtpSession.js'));
const {SerialIoEvidence}=require('./serial_io_evidence');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,ms,label){const end=Date.now()+ms;while(!fn()){if(Date.now()>=end)throw Error(label);await sleep(20);}}
const record=b=>{const h=Buffer.alloc(4);h.writeUInt32LE(b.length);return Buffer.concat([h,b]);};
const serialIn=[],serialOut=[],callerData=[],control=[],rtpRx=[],rtpTx=[],sipRx=[],sipTx=[],commands=[],events=[],errors=[],backends=[];
const sip=new SipServer(),dsp=new ModemDSP('originate'),rtp=new RtpSession({playoutMode:'immediate'});
const atInit=['ATE0','AT&K0','AT+MS=22,0,1200,1200','AT\\N0','AT%C0'];
let session,serial,callerSock,sipSock,uac,line=[],mode='command',callerInfo,answerInfo,ending,ended,negotiated,stats,child,phase='startup';
const event=(type,extra={})=>{const e={type,seconds:process.uptime(),...extra};events.push(e);trace?.event(type,extra);console.log(JSON.stringify(e));};
function endpointState(p){return p?{destroyed:p.destroyed,readableEnded:p.readableEnded,writableEnded:p.writableEnded,
 writableLength:p.writableLength,bytesRead:p.bytesRead,bytesWritten:p.bytesWritten}:null;}
function observeError(source,e,endpoint=null,extra={}){
 errors.push(e.message);event('error',{source,message:e.message,code:e.code??null,syscall:e.syscall??null,
  phase,mode,endpoint:endpointState(endpoint),serialIo:serialIo.snapshot(),...extra});
}
const serialIo=new SerialIoEvidence({phase:()=>phase,error:(e,r)=>observeError('frontend-write-callback',e,serial,{offset:r.offset,length:r.length})});
const pool=new ModemBackendPool({warmupTimeoutMs:45000,backendOpts:{qemuPath:trace?.qemuPath||'qemu-system-i386',
 kernelPath:path.join(runtime,'bzImage'),initrdPath:path.join(runtime,'candidate.cpio.gz'),
 enableControl:true,useRegistrar:true,readinessTimeoutMs:40000,atInit},backendFactory:opts=>{
  const b=new PjsipBackend({...opts,bootLogPath:path.join(out,`qemu-${backends.length}.log`)});backends.push(b);
  b.on('error',e=>observeError('answer-backend',e));b.on('connected',v=>{answerInfo={bps:v.bps,protocol:v.protocol};event('answer-CONNECT',answerInfo);connected();});return b;
 }});
function send(b){serialOut.push(Buffer.from(b));return serialIo.write(serial,b);}
function connected(){
 if(mode==='dialing' && callerInfo && answerInfo){mode='online';phase='online';send(Buffer.from('\r\nCONNECT 1200\r\n'));event('serial-CONNECT');}
}
sip.on('error',e=>observeError('external-SIP',e));pool.on('error',e=>observeError('backend-pool',e));rtp.on('error',e=>observeError('originating-RTP',e));
sip.on('invite',dialog=>{
 session=new CallSession(sip,dialog,{modemPool:pool});session.on('ended',v=>{ended=v;event('session-ended',v);});
 session.setup().catch(e=>observeError('session-setup',e));
});
sip.on('ack',()=>session.activate().catch(e=>observeError('session-activate',e)));
sip.on('bye',()=>session.onBye());sip.on('cancel',()=>session.onBye());
dsp.on('connected',v=>{callerInfo={bps:v.bps,protocol:v.protocol};event('caller-CONNECT',callerInfo);connected();});
dsp.on('data',b=>{callerData.push(Buffer.from(b));if(mode==='online')send(b);else event('pre-online-data',{bytes:b.length});});
dsp.on('audioOut',b=>rtp.send(b));rtp.on('audio',b=>dsp.receiveAudio(b));
async function dial(){
 mode='dialing';phase='training';event('numeric-call');
 callerSock=dgram.createSocket('udp4');sipSock=dgram.createSocket('udp4');
 for(const s of [callerSock,sipSock])await new Promise(r=>s.bind(0,'127.0.0.1',r));
 sipSock.on('message',b=>sipTx.push(Buffer.from(b)));callerSock.on('message',b=>{rtpRx.push(Buffer.from(b));trace?.packet('rtp-from-answer',b);});
 rtp.adoptSocket(callerSock);rtp.setCodec('PCMU',0);
 uac=new SipUacInternal({udpSocket:sipSock,peerAddress:'127.0.0.1',peerPort:cfg.sip.port,
  localAddress:'127.0.0.1',targetUri:`sip:modem@127.0.0.1:${cfg.sip.port}`});
 uac.on('error',e=>observeError('originating-SIP',e));
 negotiated=await uac.invite({localRtpPort:callerSock.address().port,offerCodecs:[{payloadType:0,name:'PCMU',clockRate:8000}],timeoutMs:10000});
 rtp.setRemote(negotiated.remoteRtpAddr,negotiated.remoteRtpPort);
 await until(()=>session?._dsp?.state==='CONFIRMED',15000,'Internal SIP activation deadline');
 session._rtpSock.on('message',b=>{rtpTx.push(Buffer.from(b));trace?.packet('rtp-from-caller',b);});dsp.start();
}
const server=net.createServer(p=>{
 if(serial){p.destroy();return;}serial=p;event('serial-client');
 p.on('error',e=>observeError('DOS-TCP',e,p));
 p.on('end',()=>event('serial-end',{phase,endpoint:endpointState(p),serialIo:serialIo.snapshot()}));
 p.on('close',hadError=>{event('serial-close',{phase,hadError,endpoint:endpointState(p),serialIo:serialIo.snapshot()});shutdown('serial-close').catch(fatal);});
 p.on('data',data=>{
  serialIn.push(Buffer.from(data));
  trace?.event('serial-input',{hex:data.toString('hex'),mode});
  if(mode==='online'){dsp.write(data);return;}
  if(mode!=='command'){observeError('DOS-command-state',new Error('Unexpected DOS input during training'),p);return;}
  for(let i=0;i<data.length;i++){
   if(data[i]!==13){line.push(data[i]);continue;}
   const cmd=Buffer.from(line).toString('ascii');line=[];commands.push(cmd);event('command',{command:cmd});
   if(cmd==='ATZ')send(Buffer.from('\r\nOK\r\n'));
   else if(cmd==='ATD1'){dial().catch(e=>{observeError('dial',e);send(Buffer.from('\r\nNO CARRIER\r\n'));});break;}
   else send(Buffer.from('\r\nERROR\r\n'));
  }
 });
});
async function shutdown(reason){
 if(ending)return ending;
 ending=(async()=>{
  phase=trace?'trace-export':'teardown';event('shutdown',{reason,serialIo:serialIo.snapshot()});if(session?._dsp?._bridge)stats=JSON.parse(JSON.stringify(session._dsp._bridge.stats));
  if(trace){trace.finishWorkload(Buffer.concat(serialIn).subarray(9));try{await trace.export();}catch(e){observeError('PCM-export',e);}}
  phase='teardown';if(session?._active)session.hangup(reason);
  // recycle() has started the old stop; stopping the pool now prevents a
  // needless replacement without dropping ownership of a checked-out backend.
  await pool.stop();for(const b of backends)await b.stop();
  dsp.stop();rtp.close();uac?.close();if(sip._started)await sip.stop();
  if(sipSock)await new Promise(r=>sipSock.close(r));
  if(serial && !serial.destroyed)serial.destroy();await new Promise(r=>server.close(r));
  if(child)await until(()=>child.exitCode!==null || child.signalCode!==null,5000,'VM exit deadline');
  if(trace)await trace.close();
  internal?.save();phase='stopped';serialIo.save(out);
  for(const [n,b] of Object.entries({'serial-in.bin':Buffer.concat(serialIn),'serial-out.bin':Buffer.concat(serialOut),
   'caller-decoded.bin':Buffer.concat(callerData),'control-wire.bin':Buffer.concat(control),
   'rtp-from-answer.bin':Buffer.concat(rtpRx.map(record)),'rtp-from-caller.bin':Buffer.concat(rtpTx.map(record)),
   'sip-to-server.bin':Buffer.concat(sipRx.map(record)),'sip-to-caller.bin':Buffer.concat(sipTx.map(record))}))fs.writeFileSync(path.join(out,n),b);
  fs.writeFileSync(path.join(out,'node-result.json'),JSON.stringify({commands,events,errors,serialIo:serialIo.snapshot(),ended,callerInfo,answerInfo,stats,negotiated,
   inputSequenceTimeoutMs:cfg.telnet.inputSequenceTimeoutMs,
   pool:pool.state,backendStates:backends.map(b=>b.state),VM_exited:!child || child.exitCode!==null || child.signalCode!==null,
   receiveTrace:trace?{exported:!!trace.exported,scope:'Diagnostic export daemon/chardev added; existing DSP dumps and host timestamps, no DSP binary changes.'}:null,
   sourceScope:'Synthetic ATZ/ATD1 front end only; online bytes cross actual external/internal SIP, CallSession/pool, RTP, originating and guest answering DSP, and Telnet. DOSBox UART/modem status lines remain emulated.'},null,2)+'\n');
 })();return ending;
}
function fatal(e){console.error(e.stack);process.exitCode=1;}
async function main(){
 if(trace)await trace.start();
 const probe=net.createServer();await new Promise(r=>probe.listen(0,'127.0.0.1',r));cfg.sip.port=probe.address().port;await new Promise(r=>probe.close(r));
 await pool.start();child=backends[0]._vmChild;backends[0].controlSocket.on('data',b=>control.push(Buffer.from(b)));
 internal?.attach(backends[0]);
 if(trace)trace.attach(backends[0]);
 await sip.start();sip._udpSocket.on('message',b=>sipRx.push(Buffer.from(b)));
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 fs.writeFileSync(path.join(out,'serial-port.json'),JSON.stringify({port:server.address().port}));phase='command';event('ready');
}
process.on('SIGTERM',()=>shutdown('SIGTERM').catch(fatal));
main().catch(async e=>{fatal(e);await shutdown('startup-error');});
