'use strict';
// Diagnostic caller bursts/idle, actual VM DSP, unchanged binaries, PCM export.
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),net=require('net'),dgram=require('dgram');
const runtime=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]),src=n=>path.join(runtime,'source',n);
const networkProfile=process.argv[4]||'direct';assert(['direct','buffered-release','buffered-increase'].includes(networkProfile));
const config=require(src('config.js'));config.logging.level='info';config.logging.colorize=false;config.modem.native.forceProtocol='V22';
const {PjsipBackend}=require(src('src/backends/PjsipBackend.js'));
const {ModemDSP}=require(src('src/dsp/ModemDSP.js'));
const {RtpSession}=require(src('src/rtp/RtpSession.js'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,ms,label){const end=Date.now()+ms;while(!fn()){assert(Date.now()<end,label);await sleep(10);}}
const record=b=>{const h=Buffer.alloc(4);h.writeUInt32LE(b.length);return Buffer.concat([h,b]);};
const events=[],wire=[],callerData=[],guestData=[],rtpCaller=[],rtpAnswer=[],rtpGuest=[],rtpDelayed=[],errors=[],checks={};
const event=(type,v={})=>events.push({type,ns:process.hrtime.bigint().toString(),...v});
function packet(type,target,b){target.push(Buffer.from(b));event(type,{packet:target.length-1,sequence:b.length>=12?b.readUInt16BE(2):null,timestamp:b.length>=12?b.readUInt32BE(4):null});}
async function main(){
 let exportSocket,exportBuffer=Buffer.alloc(0),child,callerInfo,answerInfo,exception,stats,ext,caller,relay,delayTimer,atText='';
 let delayMs=networkProfile==='buffered-release'?300:0;const delayed=[];
 const exportServer=net.createServer(s=>{assert(!exportSocket);exportSocket=s;s.on('data',b=>exportBuffer=Buffer.concat([exportBuffer,b]));s.on('error',e=>errors.push(e.message));});
 await new Promise(r=>exportServer.listen(0,'127.0.0.1',r));process.env.PCPLUS_TRACE_PORT=String(exportServer.address().port);
 const atInit=['AT&K0','AT+MS=22,0,1200,1200','AT\\N0','AT%C0'];
 const b=new PjsipBackend({qemuPath:path.join(__dirname,'qemu_trace_wrapper.py'),kernelPath:path.join(runtime,'bzImage'),
  initrdPath:path.join(runtime,'candidate.cpio.gz'),bootLogPath:path.join(out,'qemu.log'),enableControl:true,useRegistrar:true,readinessTimeoutMs:45000,atInit});
 const dsp=new ModemDSP('originate'),rtp=new RtpSession({playoutMode:'immediate'}),sent=[];
 b.on('error',e=>errors.push(e.message));rtp.on('error',e=>errors.push(e.message));b.on('at-response',s=>atText+=s);
 b.on('connected',v=>{answerInfo={bps:v.bps,protocol:v.protocol};event('guest-CONNECT',answerInfo);});
 dsp.on('connected',v=>{callerInfo={bps:v.bps,protocol:v.protocol};event('caller-CONNECT',callerInfo);});
 b.on('data',v=>{guestData.push(Buffer.from(v));event('guest-data',{hex:v.toString('hex')});});
 dsp.on('data',v=>{callerData.push(Buffer.from(v));event('caller-data',{hex:v.toString('hex')});});
 dsp.on('audioOut',samples=>rtp.send(samples));rtp.on('audio',samples=>dsp.receiveAudio(samples));
 const transmit=v=>{sent.push(Buffer.from(v));event('write-caller',{hex:v.toString('hex')});dsp.write(v);};
 const down=Buffer.alloc(6000);for(let i=0;i<down.length;i++)down[i]=i&255;
 let onlineStart=0,observed,networkPendingPackets=0;
 try{
  await b.startAsync();child=b._vmChild;checks.registered=b.state==='READY' && !!b._registrar.currentBinding;
  b.controlSocket.on('data',v=>{wire.push(Buffer.from(v));event('guest-control',{bytes:v.length});});
  b.sendAt('ATE0');await until(()=>/\bOK\b/.test(atText),5000,'ATE0');atText='';
  ext=dgram.createSocket('udp4');caller=dgram.createSocket('udp4');for(const s of [ext,caller])await new Promise(r=>s.bind(0,'127.0.0.1',r));
  if(networkProfile!=='direct'){
   relay=dgram.createSocket('udp4');await new Promise(r=>relay.bind(0,'127.0.0.1',r));
   const forward=v=>relay.send(v,ext.address().port,'127.0.0.1',e=>{if(e)errors.push(e.message);});
   relay.on('message',v=>{packet('rtp-from-caller',rtpCaller,v);if(!delayMs){forward(v);return;}assert(delayed.length<64,'Bounded delay queue');delayed.push({v:Buffer.from(v),due:performance.now()+delayMs});});
   delayTimer=setInterval(()=>{while(delayed.length && delayed[0].due<=performance.now())forward(delayed.shift().v);},2);
   relay.release=()=>{event('network-delay-release',{bufferedPackets:delayed.length,previousDelayMs:delayMs});delayMs=0;while(delayed.length)forward(delayed.shift().v);};
   relay.increase=()=>{event('network-delay-increase',{bufferedPackets:delayed.length,previousDelayMs:delayMs,nextDelayMs:120});delayMs=120;};
   ext.on('message',v=>packet('rtp-after-delay',rtpDelayed,v));
  }else ext.on('message',v=>packet('rtp-from-caller',rtpCaller,v));
  rtp.adoptSocket(caller);rtp.setRemote('127.0.0.1',relay?relay.address().port:ext.address().port);rtp.setCodec('PCMU',0);
  caller.on('message',v=>packet('rtp-from-answer',rtpAnswer,v));
  await b.activate({extRtpSocket:ext,extPeer:{address:'127.0.0.1',port:caller.address().port}});
  b._tunnel.udp.rtp.on('message',v=>packet('rtp-to-guest',rtpGuest,v));
  checks.real_RING_and_init_OK=/\bRING\b/.test(atText) && !/\bERROR\b/.test(atText);dsp.start();
  await until(()=>callerInfo && answerInfo,30000,'Both DSP CONNECT');checks.both_DSP_CONNECT=callerInfo.bps===1200 && answerInfo.bps===1200;
  await sleep(6500);onlineStart=Buffer.concat(guestData).length;event('workload-start',{guestPrefixBytes:onlineStart});
  b.write(down);transmit(Buffer.from('127.0.0.1:45505\r'));await sleep(1500);transmit(Buffer.from('\x1b[?1;2c'));await sleep(300);transmit(Buffer.from('\x1b[1;1R'));
  if(relay){await sleep(500);if(networkProfile==='buffered-release')relay.release();else relay.increase();}
  await sleep(45000);transmit(Buffer.from('NEXT\r'));await sleep(1500);
  await until(()=>Buffer.concat(callerData).length>=down.length,15000,'Downstream payload deadline');
  observed=Buffer.concat(guestData);event('workload-end',{guestBytes:observed.length});
  checks.upstream_exact_after_declared_idle=observed.subarray(onlineStart).equals(Buffer.concat(sent));
  checks.downstream_exact=Buffer.concat(callerData).equals(down);
  if(relay){
   networkPendingPackets=delayed.length;
   // A persistent delay retains its trailing packets while the source runs.
   // The release profile must drain; the increase profile may retain only its
   // bounded tail. Actual delivered packets must still be an exact prefix.
   checks.delay_route_preserves_order_and_payload=(networkProfile==='buffered-increase'?delayed.length<=8:delayed.length===0) && rtpDelayed.every((v,i)=>v.equals(rtpCaller[i]));
  }
  await until(()=>exportSocket,5000,'Diagnostic export socket');event('export-start');exportSocket.write('DUMP\n');
  for(const name of ['modem_rx_8k.raw','modem_rx.raw','modem_tx.raw']){
   await until(()=>exportBuffer.includes(10),10000,'Export header');const at=exportBuffer.indexOf(10),header=exportBuffer.subarray(0,at).toString().trim().split(/\s+/);exportBuffer=exportBuffer.subarray(at+1);
   assert.equal(header[0],name);const size=Number(header[1]);assert(Number.isInteger(size)&&size>0&&size<16*1024*1024);
   await until(()=>exportBuffer.length>=size,10000,'Export payload');fs.writeFileSync(path.join(out,name),exportBuffer.subarray(0,size));exportBuffer=exportBuffer.subarray(size);
  }
  await until(()=>exportBuffer.includes(10),5000,'Export DONE');assert.equal(exportBuffer.toString(),'DONE\n');checks.guest_PCM_export=true;
  stats=JSON.parse(JSON.stringify(b._bridge.stats));
  await b.stop();await until(()=>child.exitCode!==null || child.signalCode!==null,5000,'QEMU exit');checks.teardown=b.state==='STOPPED' && b.controlSocket===null;
 }catch(e){exception=e.stack;errors.push(e.message);}
 finally{
  dsp.stop();rtp.close();if(delayTimer)clearInterval(delayTimer);await b.stop();if(relay)await new Promise(r=>relay.close(r));if(ext)await new Promise(r=>ext.close(r));exportSocket?.destroy();await new Promise(r=>exportServer.close(r));
  const files={'caller-decoded.bin':Buffer.concat(callerData),'guest-decoded.bin':Buffer.concat(guestData),'guest-workload.bin':observed||Buffer.alloc(0),
   'control-wire.bin':Buffer.concat(wire),'rtp-from-caller.bin':Buffer.concat(rtpCaller.map(record)),'rtp-from-answer.bin':Buffer.concat(rtpAnswer.map(record)),
   'rtp-to-guest.bin':Buffer.concat(rtpGuest.map(record)),'expected-upstream.bin':Buffer.concat(sent),'expected-downstream.bin':down};
  if(relay)files['rtp-after-delay.bin']=Buffer.concat(rtpDelayed.map(record));
  for(const [name,v] of Object.entries(files))fs.writeFileSync(path.join(out,name),v);
  fs.writeFileSync(path.join(out,'timing.jsonl'),events.map(v=>JSON.stringify(v)+'\n').join(''));
  checks.no_errors=errors.length===0;const result={passed:!exception && Object.values(checks).every(Boolean),checks,errors,exception,callerInfo,answerInfo,onlineStart,stats,atInit,node:process.version,networkProfile,networkPendingPackets,
   scope:'Diagnostic-only actual native/VM V22 DSP, internal SIP/RTP and existing guest PCM dumps. Extra export daemon/chardev; selected runtime binaries pinned by Python. Optional bounded FIFO delay release or 120ms increase, no packet payload changes/loss/reordering. Authored workload; no external SIP gateway, DOS/BBS or physical modem/ATA.'};
  fs.writeFileSync(path.join(out,'node-result.json'),JSON.stringify(result,null,2)+'\n');
 }
 assert(!exception,exception);
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
