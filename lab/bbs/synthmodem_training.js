'use strict';
// Real originating native DSP -> PCMU/RTP -> normal guest answering DSP.
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),dgram=require('dgram');
const runtime=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
const config=require(path.join(runtime,'source/config.js'));
config.logging.level='info';config.logging.colorize=false;config.modem.native.forceProtocol='V22';
const {PjsipBackend}=require(path.join(runtime,'source/src/backends/PjsipBackend.js'));
const {ModemDSP}=require(path.join(runtime,'source/src/dsp/ModemDSP.js'));
const {RtpSession}=require(path.join(runtime,'source/src/rtp/RtpSession.js'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,ms,label){const end=Date.now()+ms;while(!fn()){assert(Date.now()<end,label);await sleep(20);}}
const record=b=>{const h=Buffer.alloc(4);h.writeUInt32LE(b.length);return Buffer.concat([h,b]);};
const checks={},errors=[],wire=[],rtpRx=[],rtpTx=[],callerData=[],answerData=[],events=[];
const pattern=Buffer.alloc(1024);for(let i=0;i<pattern.length;i++)pattern[i]=i&255;
const fromCaller=Buffer.concat([Buffer.from('PCPLUS-FROM-CALLER\r\n'),pattern,Buffer.from('\r\nEND-CALLER\r\n')]);
const fromAnswer=Buffer.concat([Buffer.from('PCPLUS-FROM-ANSWER\r\n'),Buffer.from(pattern).reverse(),Buffer.from('\r\nEND-ANSWER\r\n')]);
async function main(){
 const atInit=['AT&K0','AT+MS=22,0,1200,1200','AT\\N0','AT%C0'];
 const b=new PjsipBackend({qemuPath:'qemu-system-i386',kernelPath:path.join(runtime,'bzImage'),
  initrdPath:path.join(runtime,'candidate.cpio.gz'),bootLogPath:path.join(out,'qemu.log'),
  enableControl:true,useRegistrar:true,readinessTimeoutMs:45000,atInit});
 const dsp=new ModemDSP('originate'),rtp=new RtpSession({playoutMode:'immediate'});
 let ext,caller,child,answerInfo,callerInfo,hello='',atText='',diag,stats,exception;
 const now=()=>Math.round(performance.now());
 b.on('error',e=>errors.push(e.message));rtp.on('error',e=>errors.push(e.message));
 b.on('hello',s=>hello=s);b.on('at-response',s=>atText+=s);
 b.on('connected',v=>{answerInfo={bps:v.bps,protocol:v.protocol};events.push({ms:now(),answer:answerInfo});});
 b.on('data',v=>answerData.push(Buffer.from(v)));
 b.on('silenceHangup',()=>events.push({ms:now(),answer:'silenceHangup'}));
 dsp.on('connected',v=>{callerInfo={bps:v.bps,protocol:v.protocol};events.push({ms:now(),caller:callerInfo});});
 dsp.on('data',v=>callerData.push(Buffer.from(v)));
 dsp.on('silenceHangup',()=>events.push({ms:now(),caller:'silenceHangup'}));
 dsp.on('audioOut',samples=>rtp.send(samples));rtp.on('audio',samples=>dsp.receiveAudio(samples));
 try{
  await b.startAsync();child=b._vmChild;
  checks.normal_guest_ready=b.state==='READY' && b._registrar.currentBinding?.contactUri===b.targetUri;
  await until(()=>hello,10000,'Guest HELLO deadline');
  b.controlSocket.on('data',v=>wire.push(Buffer.from(v)));
  b.sendAt('ATE0');await until(()=>/\bOK\b/.test(atText),5000,'ATE0 deadline');atText='';
  ext=dgram.createSocket('udp4');caller=dgram.createSocket('udp4');
  for(const s of [ext,caller])await new Promise(r=>s.bind(0,'127.0.0.1',r));
  // Adopt a loopback-bound socket instead of open(), which binds all interfaces.
  rtp.adoptSocket(caller);rtp.setRemote('127.0.0.1',ext.address().port);rtp.setCodec('PCMU',0);
  caller.on('message',v=>rtpRx.push(Buffer.from(v)));ext.on('message',v=>rtpTx.push(Buffer.from(v)));
  await b.activate({extRtpSocket:ext,extPeer:{address:'127.0.0.1',port:caller.address().port}});
  checks.real_RING_and_init_OK=/\bRING\b/.test(atText) && !/\bERROR\b/.test(atText);
  dsp.start();
  diag=setInterval(()=>console.log(JSON.stringify({callerState:dsp.handshakeState,phase:dsp._handshake._protocol?.phase,rxTraining:dsp._handshake._protocol?.demodulator.trainingStage,answerConnected:b._connected,
   callerBytes:Buffer.concat(callerData).length,answerBytes:Buffer.concat(answerData).length,stats:b._bridge?.stats})),5000);
  await until(()=>answerInfo && callerInfo,30000,'Both DSP CONNECT deadline');
  checks.both_DSP_CONNECT=answerInfo.bps===1200 && callerInfo.bps===1200;
  // Both DSP state machines must be online before admitting any payload.
  events.push({ms:now(),phase:'payload'});b.write(fromAnswer);dsp.write(fromCaller);
  await until(()=>Buffer.concat(callerData).includes(fromAnswer) && Buffer.concat(answerData).includes(fromCaller),20000,'Exact duplex DSP payload deadline');
  checks.exact_all_byte_duplex=Buffer.concat(callerData).equals(fromAnswer) && Buffer.concat(answerData).equals(fromCaller);
  stats=JSON.parse(JSON.stringify(b._bridge.stats));
  const uac=b._uac;await b.stop();await until(()=>child.signalCode!==null || child.exitCode!==null,5000,'QEMU exit deadline');
  checks.teardown=b.state==='STOPPED' && uac.state==='TERMINATED' && b.controlSocket===null;
  checks.no_errors=errors.length===0;
 }catch(e){exception=e.stack;errors.push(e.message);}
 finally{
  if(diag)clearInterval(diag);dsp.stop();rtp.close();
  await b.stop();if(ext)await new Promise(r=>ext.close(r));
  for(const [name,data] of [['caller-decoded.bin',Buffer.concat(callerData)],['answer-decoded.bin',Buffer.concat(answerData)],
   ['control-wire.bin',Buffer.concat(wire)],['rtp-from-answer.bin',Buffer.concat(rtpRx.map(record))],['rtp-from-caller.bin',Buffer.concat(rtpTx.map(record))],
   ['expected-from-caller.bin',fromCaller],['expected-from-answer.bin',fromAnswer]])fs.writeFileSync(path.join(out,name),data);
  const result={passed:!exception && Object.values(checks).every(Boolean),checks,errors,exception,events,atInit,
   hello,atText,answerInfo,callerInfo,stats,node:process.version,
   config:{forceProtocol:'V22',playoutMode:'immediate',callerRole:'originate',codec:'PCMU',sampleRate:8000},
   scope:'Actual native originating DSP, PCMU/RTP and normal guest slmodemd/d-modem answering DSP with rebuilt helper. Internal SIP leg only; no external SIP server, DOS/BBS or physical modem/ATA.'};
  fs.writeFileSync(path.join(out,'node-result.json'),JSON.stringify(result,null,2)+'\n');
 }
 assert(!exception,exception);assert(Object.values(checks).every(Boolean));
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
