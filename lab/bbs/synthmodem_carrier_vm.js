'use strict';
// Real VM/internal SIP/DSP; remove the caller waveform without ending SIP first.
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),dgram=require('dgram');
const runtime=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
const src=n=>path.join(runtime,'source',n),cfg=require(src('config.js'));
cfg.logging.level='info';cfg.logging.colorize=false;cfg.modem.native.forceProtocol='V22';
const {PjsipBackend}=require(src('src/backends/PjsipBackend.js'));
const {ModemDSP}=require(src('src/dsp/ModemDSP.js'));
const {RtpSession}=require(src('src/rtp/RtpSession.js'));
const wire=require(src('vm/qemu-runner/wire.js'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,ms,label){const deadline=Date.now()+ms;while(!fn()){assert(Date.now()<deadline,label);await sleep(10);}}
const checks={},events=[],errors=[],control=[],guest=[],caller=[],rtpIn=[],rtpOut=[];
const event=(type,values={})=>events.push({type,ns:process.hrtime.bigint().toString(),...values});
const record=b=>{const h=Buffer.alloc(4);h.writeUInt32LE(b.length);return Buffer.concat([h,b]);};
async function main(){
 const atInit=['ATE0','AT&K0','AT+MS=22,0,1200,1200','AT\\N0','AT%C0'];
 const b=new PjsipBackend({qemuPath:'qemu-system-i386',kernelPath:path.join(runtime,'bzImage'),initrdPath:path.join(runtime,'candidate.cpio.gz'),
  bootLogPath:path.join(out,'qemu.log'),enableControl:true,useRegistrar:true,readinessTimeoutMs:45000,atInit});
 const dsp=new ModemDSP('originate'),rtp=new RtpSession({playoutMode:'immediate'});
 let ext,calling,child,exception,callerInfo,answerInfo,timer,writer,heldSocket,onlineStart=0,lossStarted;
 let atText='',hangups=0,structured=0;
 const pattern=Buffer.from(Array.from({length:256},(_,i)=>i));
 const up=Buffer.concat([Buffer.from('CARRIER-UP\r\nNO CARRIER\r\n'),pattern,Buffer.from('\r\nEND\r\n')]);
 const down=Buffer.concat([Buffer.from('CARRIER-DOWN\r\nNO CARRIER\r\n'),Buffer.from(pattern).reverse(),Buffer.from('\r\nEND\r\n')]);
 b.on('error',e=>{errors.push(e.message);event('backend-error',{message:e.message});});rtp.on('error',e=>errors.push(e.message));
 b.on('at-response',s=>{atText+=s;event('AT',{text:s});});
 b.on('connected',v=>{answerInfo={bps:v.bps,protocol:v.protocol};event('answer-CONNECT',answerInfo);});
 dsp.on('connected',v=>{callerInfo={bps:v.bps,protocol:v.protocol};event('caller-CONNECT',callerInfo);});
 b.on('data',v=>{guest.push(Buffer.from(v));event('guest-data',{hex:v.toString('hex')});});
 dsp.on('data',v=>{caller.push(Buffer.from(v));event('caller-data',{hex:v.toString('hex')});});
 b.on('silenceHangup',()=>{hangups++;event('backend-hangup',{writerClosed:writer?.closed ?? null,connected:b._connected,retired:b._carrierEnded});});
 dsp.on('audioOut',s=>rtp.send(s));rtp.on('audio',s=>dsp.receiveAudio(s));
 try{
  await b.startAsync();child=b._vmChild;checks.actual_REGISTER=b.state==='READY' && !!b._registrar.currentBinding;
  const parser=new wire.Parser();parser.on('frame',f=>{if(f.type===wire.TYPE.MODEM_STATUS){const v=JSON.parse(f.payload);event('status',v);if(v.event==='nocarrier')structured++;}});
  b.controlSocket.on('data',v=>{control.push(Buffer.from(v));parser.feed(v);});
  b.sendAt('ATE0');await until(()=>/\bOK\b/.test(atText),5000,'ATE0 response');atText='';
  ext=dgram.createSocket('udp4');calling=dgram.createSocket('udp4');
  for(const socket of [ext,calling])await new Promise(r=>socket.bind(0,'127.0.0.1',r));
  ext.on('message',v=>rtpIn.push(Buffer.from(v)));calling.on('message',v=>rtpOut.push(Buffer.from(v)));
  rtp.adoptSocket(calling);rtp.setRemote('127.0.0.1',ext.address().port);rtp.setCodec('PCMU',0);
  await b.activate({extRtpSocket:ext,extPeer:{address:'127.0.0.1',port:calling.address().port}});
  b._uac.on('ended',v=>event('internal-SIP-ended',{initiator:v.initiator}));
  checks.actual_RING_and_init=/\bRING\b/.test(atText) && !/\bERROR\b/.test(atText);dsp.start();
  await until(()=>callerInfo && answerInfo,30000,'Both real DSP CONNECT');
  checks.both_DSP_CONNECT_1200=callerInfo.bps===1200 && answerInfo.bps===1200;
  await sleep(6500);onlineStart=Buffer.concat(guest).length;event('workload-start',{onlineStart});
  b.write(down);dsp.write(up);
  await until(()=>Buffer.concat(guest).length>=onlineStart+up.length && Buffer.concat(caller).length>=down.length,15000,'Exact duplex payload deadline');
  checks.literal_carrier_text_and_all_bytes_up=Buffer.concat(guest).subarray(onlineStart).equals(up);
  checks.literal_carrier_text_and_all_bytes_down=Buffer.concat(caller).equals(down);
  checks.payload_does_not_hangup=hangups===0 && structured===0 && b._connected;
  // Real Node stream pressure: retain writes in the actual control socket,
  // leaving ControlWriter work pending when the analog waveform disappears.
  heldSocket=b.controlSocket;heldSocket.cork();b.write(Buffer.alloc(200000,0x58));writer=b._dataWriter;
  checks.actual_control_writer_pending=!!writer && writer.length>0 && heldSocket.writableLength>0;
  event('pressure-start',{retained:writer.length,socketBytes:heldSocket.writableLength});
  dsp.stop();lossStarted=process.hrtime.bigint();event('caller-waveform-removed');
  timer=setInterval(()=>rtp.send(new Float32Array(160)),20);
  await until(()=>structured===1 && hangups===1,18000,'Actual waveform-loss carrier callback deadline');
  checks.real_waveform_loss_yields_structured_status=structured===1;
  checks.writer_retired_before_hangup=writer.closed && writer.length===0 && !b._dataWriter && b._carrierEnded && !b._connected;
  assert.throws(()=>b.write(Buffer.from('STALE')));assert.throws(()=>b.sendAt('AT'));
  checks.retired_backend_rejects_transmission=true;
  heldSocket.uncork();await sleep(600);
  checks.one_hangup_after_carrier_loss=hangups===1 && structured===1 && events.filter(e=>e.type==='answer-CONNECT').length===1;
  checks.no_modem_result_leaks_into_DATA=Buffer.concat(guest).subarray(onlineStart).equals(up);
  checks.no_errors=errors.length===0;
 }catch(error){exception=error.stack;errors.push(error.message);}
 finally{
  if(timer)clearInterval(timer);dsp.stop();rtp.close();
  if(heldSocket && !heldSocket.destroyed)heldSocket.uncork();
  await b.stop();if(ext)await new Promise(r=>ext.close(r));
  if(child)await until(()=>child.exitCode!==null || child.signalCode!==null,5000,'QEMU exit');
  checks.VM_stopped=b.state==='STOPPED' && !b._vmChild && !b.controlSocket;
  const files={'control-wire.bin':Buffer.concat(control),'guest-data.bin':Buffer.concat(guest),'caller-data.bin':Buffer.concat(caller),
   'expected-up.bin':up,'expected-down.bin':down,'rtp-from-caller.bin':Buffer.concat(rtpIn.map(record)),'rtp-from-answer.bin':Buffer.concat(rtpOut.map(record))};
  for(const [name,value] of Object.entries(files))fs.writeFileSync(path.join(out,name),value);
  const result={passed:!exception && Object.values(checks).every(Boolean),checks,errors,exception,events,onlineStart,callerInfo,answerInfo,atInit,node:process.version,
   lossStarted:lossStarted?.toString(),scope:'Actual internal SIP/VM/native-caller/guest-DSP path. Caller waveform replaced by real PCMU silence while RTP continues; no synthetic carrier/status injection. Node control stream deliberately corked to hold pending transmission. No external SIP ATA, CallSession/Telnet, DOS/BBS or physical modem.'};
  fs.writeFileSync(path.join(out,'node-result.json'),JSON.stringify(result,null,2)+'\n');
 }
 assert(!exception,exception);assert(Object.values(checks).every(Boolean));
}
main().catch(error=>{console.error(error.stack);process.exitCode=1;});
