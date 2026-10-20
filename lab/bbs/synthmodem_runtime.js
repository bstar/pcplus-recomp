'use strict';
// Normal production init and real slmodemd/d-modem; a silence RTP caller only.
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),dgram=require('dgram');
const stage=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
const profile=process.argv[4];assert(['auto','v32bis'].includes(profile));
// Commands target ONLY the VM's SmartLink answering modem, never the Boca.
const atInit=profile==='v32bis'?['AT+MS=132,0,14400,14400']:[];
const config=require(path.join(stage,'config.js'));
config.logging.level='info';config.logging.colorize=false;
const {PjsipBackend}=require(path.join(stage,'src/backends/PjsipBackend.js'));
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,ms=10000){const end=Date.now()+ms;while(!fn()){assert(Date.now()<end,'Observation deadline');await wait(10);}}
const checks={},errors=[],commands=[],rx=[],tx=[],tunnel=[];
const packet=b=>{const n=Buffer.alloc(4);n.writeUInt32LE(b.length);return Buffer.concat([n,b]);};
async function main(){
 const backend=new PjsipBackend({qemuPath:'qemu-system-i386',kernelPath:path.join(out,'bzImage'),
  initrdPath:path.join(out,'candidate.cpio.gz'),bootLogPath:path.join(out,'qemu.log'),
  enableControl:true,useRegistrar:true,readinessTimeoutMs:45000,atInit});
 let ext,caller,timer,hello='',atText='',media,connected=0,hangups=0,child;
 backend.on('error',e=>errors.push(e.message));backend.on('hello',s=>hello=s);
 backend.on('at-response',s=>atText+=s);backend.on('connected',()=>connected++);
 backend.on('silenceHangup',()=>hangups++);
 const ctrl=[];
 try{
  await backend.startAsync();child=backend._vmChild;
  checks.normal_init_READY=backend.state==='READY';
  checks.actual_registrar_binding=backend._registrar.currentBinding?.contactUri===backend.targetUri && /^sip:modem@127\.0\.0\.1:\d+/.test(backend.targetUri);
  await until(()=>hello);checks.helper_HELLO=hello.includes('modemd-ctrl v1 build=pjsip-vm');
  backend.controlSocket.on('data',b=>ctrl.push(Buffer.from(b)));
  backend._tunnel.on('frame-rx',(channel,srcPort,dstPort,payload)=>tunnel.push({channel,srcPort,dstPort,hex:payload.toString('hex')}));
  for(const command of ['ATE0','ATI','AT+MS=?','AT+MS?']){
   atText='';backend.sendAt(command);await until(()=>/(?:^|\r|\n)(?:OK|ERROR)(?:\r|\n)/.test(atText));
   commands.push({command,response:atText});assert(!/\bERROR\b/.test(atText),`${command} rejected`);
  }
  checks.real_modem_AT_commands=commands.length===4 && commands.every(c=>/\bOK\b/.test(c.response));
  ext=dgram.createSocket('udp4');caller=dgram.createSocket('udp4');
  for(const sock of [ext,caller])await new Promise(r=>sock.bind(0,'127.0.0.1',r));
  caller.on('message',b=>rx.push(Buffer.from(b)));
  caller.on('error',e=>errors.push(e.message));ext.on('error',e=>errors.push(e.message));
  backend.once('media-ready',m=>media=m);atText='';
  await backend.activate({extRtpSocket:ext,extPeer:{address:'127.0.0.1',port:caller.address().port}});
  checks.real_INVITE_answer=backend.state==='CONFIRMED' && media?.codec.codec==='PCMU';
  checks.actual_RING=/\bRING\b/.test(atText);
  checks.answer_init_accepted=profile==='auto' || (/\bOK\b/.test(atText) && !/\bERROR\b/.test(atText));
  const answerResponse=atText;
  // Feed valid PCMU silence at 8 kHz. This caller supplies neither V.8 CM nor
  // legacy modem symbols; the server's answering tones are real DSP output.
  let seq=0;
  timer=setInterval(()=>{
   const b=Buffer.alloc(172,255);b[0]=0x80;b[1]=0;b.writeUInt16BE(seq&65535,2);
   b.writeUInt32BE(seq*160,4);b.writeUInt32BE(0x50434c42,8);seq++;
   tx.push(Buffer.from(b));caller.send(b,ext.address().port,'127.0.0.1');
  },20);
  // slmodemd delays its answer tone: an initial two-second capture can contain
  // only silence even though signaling and RTP are healthy. Keep six seconds.
  await until(()=>rx.length>=300 && tx.length>=300,15000);clearInterval(timer);timer=null;
  // dgram.send and the bridge's message callback are asynchronous. Let the
  // final datagram reach the bridge before freezing its packet counters.
  await until(()=>backend._bridge.stats.extToInt.packets>=tx.length,2000);
  const stats=JSON.parse(JSON.stringify(backend._bridge.stats));
  checks.RTP_both_directions=stats.extToInt.packets>=300 && stats.intToExt.packets>=300;
  checks.real_DSP_audio=rx.some(b=>b.length>12 && b.subarray(12).some(v=>v!==255 && v!==127));
  checks.silence_is_not_CONNECT=connected===0 && !backend._connected;
  const uac=backend._uac;await backend.stop();
  await until(()=>child.exitCode!==null || child.signalCode!==null);
  checks.actual_BYE_teardown=backend.state==='STOPPED' && uac.state==='TERMINATED';
  checks.resources_released=backend.controlSocket===null && backend._tunnel===null && backend._bridge===null && backend._registrar===null;
  checks.QEMU_stopped=child.exitCode!==null || child.signalCode!==null;
  checks.no_errors=errors.length===0;
  fs.writeFileSync(path.join(out,'rtp-from-modem.bin'),Buffer.concat(rx.map(packet)));
  fs.writeFileSync(path.join(out,'rtp-to-modem.bin'),Buffer.concat(tx.map(packet)));
  fs.writeFileSync(path.join(out,'control-wire.bin'),Buffer.concat(ctrl));
  fs.writeFileSync(path.join(out,'tunnel-frames.json'),JSON.stringify(tunnel,null,2)+'\n');
  fs.writeFileSync(path.join(out,'node-result.json'),JSON.stringify({passed:Object.values(checks).every(Boolean),checks,errors,
   hello,commands,profile,atInit,answerResponse,media,stats,connected,hangups,received_packets:rx.length,sent_packets:tx.length,
   targetUri:backend.targetUri,child:{exitCode:child.exitCode,signalCode:child.signalCode},node:process.version,
   scope:'Actual candidate PjsipBackend startup/registrar/AT/INVITE/RTP/BYE with normal upstream guest init, real slmodemd and d-modem and Nix-rebuilt helper. External caller sends only PCMU silence. No negotiated modem data, external SIP server/ATA, DOS/BBS or physical hardware.'},null,2)+'\n');
  assert(Object.values(checks).every(Boolean),JSON.stringify(checks));
 }finally{
  if(timer)clearInterval(timer);
  await backend.stop();
  for(const sock of [ext,caller])if(sock)await new Promise(r=>sock.close(r));
 }
}
main().catch(e=>{fs.writeFileSync(path.join(out,'node-error.txt'),e.stack+'\n');process.exitCode=1;});
