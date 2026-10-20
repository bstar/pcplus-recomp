'use strict';
// Full real SIP/CallSession/pool/DSP/Telnet path, loopback peers only.
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),net=require('net'),dgram=require('dgram');
const runtime=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]),src=n=>path.join(runtime,'source',n);
const cfg=require(src('config.js'));
cfg.logging.level='info';cfg.logging.colorize=false;cfg.modem.backend='slmodemd-pjsip';cfg.modem.captureAudio=false;
cfg.modem.native.forceProtocol='V22';cfg.rtp.bindAddress='127.0.0.1';cfg.rtp.portMin=42000;cfg.rtp.portMax=42100;
cfg.sip.host='127.0.0.1';cfg.sip.publicHost='127.0.0.1';
Object.assign(cfg.terminal,{banner:'PCPLUS DSP LAB {{protocol}} {{bps}}\n',prompt:'CONNECT> ',lineEnding:'\r\n',localEcho:false});
Object.assign(cfg.telnet,{terminalType:'ANSI',terminalCols:80,terminalRows:25,allowedHosts:['127.0.0.1'],blockedHosts:[],
 idleTimeoutMs:0,menuIdleHeartbeatMs:0,proxyEscapeByte:null,negotiateOptions:true});
const {SipServer}=require(src('src/sip/SipServer.js'));
const {SipUacInternal}=require(src('src/sip/SipUacInternal.js'));
const {CallSession}=require(src('src/session/CallSession.js'));
const {PjsipBackend}=require(src('src/backends/PjsipBackend.js'));
const {ModemBackendPool}=require(src('src/backends/ModemBackendPool.js'));
const {ModemDSP}=require(src('src/dsp/ModemDSP.js'));
const {RtpSession}=require(src('src/rtp/RtpSession.js'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn,ms,label){const end=Date.now()+ms;while(!fn()){assert(Date.now()<end,label);await sleep(20);}}
const record=b=>{const h=Buffer.alloc(4);h.writeUInt32LE(b.length);return Buffer.concat([h,b]);};
const escape=b=>Buffer.from(b.toString('latin1').replace(/\xff/g,'\xff\xff'),'latin1');
const pattern=Buffer.alloc(512);for(let i=0;i<pattern.length;i++)pattern[i]=i&255;
const up=Buffer.concat([Buffer.from('GATEWAY-UP\r\n'),pattern,Buffer.from('\r\nEND-UP\r\n')]);
const down=Buffer.concat([Buffer.from('GATEWAY-DOWN\r\n'),Buffer.from(pattern).reverse(),Buffer.from('\r\nEND-DOWN\r\n')]);
const errors=[],checks={},events=[],backends=[],peers=[],callerData=[],control=[],rtpRx=[],rtpTx=[],sipRx=[],sipTx=[];
async function main(){
 const sip=new SipServer(),dsp=new ModemDSP('originate'),rtp=new RtpSession({playoutMode:'immediate'});
 const atInit=['ATE0','AT&K0','AT+MS=22,0,1200,1200','AT\\N0','AT%C0'];
 const pool=new ModemBackendPool({warmupTimeoutMs:45000,backendOpts:{qemuPath:'qemu-system-i386',
  kernelPath:path.join(runtime,'bzImage'),initrdPath:path.join(runtime,'candidate.cpio.gz'),
  enableControl:true,useRegistrar:true,readinessTimeoutMs:40000,atInit},backendFactory:opts=>{
   const b=new PjsipBackend({...opts,bootLogPath:path.join(out,`qemu-${backends.length}.log`)});backends.push(b);
   b.on('error',e=>errors.push(e.message));b.on('connected',v=>events.push({type:'answer-CONNECT',bps:v.bps}));return b;
  }});
 let session,callerSock,sipSock,uac,exception,diag,stats,ended,negotiated,replacementReadyNs;
 const text=()=>Buffer.concat(callerData),prompts=()=>text().toString('latin1').split('CONNECT> ').length-1;
 const bbs=net.createServer(p=>{
  const peer={socket:p,input:[],output:[],data:[],sub:[],negotiation:[],state:0,binaryLocal:false,binaryRemote:false,ready:false};peers.push(peer);
  const send=b=>{peer.output.push(Buffer.from(b));p.write(b);};
  const ready=()=>{
   if(peer.ready || !peer.binaryLocal || !peer.binaryRemote || peer.type!=='ANSI' || !peer.size)return;
   peer.ready=true;send(escape(peers.length===1?down:Buffer.from('RECONNECTED\r\n')));
  };
  p.setNoDelay(true);p.on('error',e=>errors.push(e.message));
  p.on('data',chunk=>{
   peer.input.push(Buffer.from(chunk));const bytes=[];
   for(const v of chunk){
    if(peer.state===0){if(v===255)peer.state=1;else bytes.push(v);}
    else if(peer.state===1){
     if(v===255){bytes.push(255);peer.state=0;}
     else if(v>=251 && v<=254){peer.verb=v;peer.state=2;}
     else if(v===250){peer.sub=[];peer.state=3;}else peer.state=0;
    }else if(peer.state===2){
     peer.negotiation.push([peer.verb,v]);
     if(peer.verb===251){send(Buffer.from([255,253,v]));if(v===0)peer.binaryRemote=true;if(v===24)send(Buffer.from([255,250,24,1,255,240]));}
     if(peer.verb===253){send(Buffer.from([255,251,v]));if(v===0)peer.binaryLocal=true;}
     peer.state=0;
    }else if(peer.state===3){if(v===255)peer.state=4;else peer.sub.push(v);}
    else if(peer.state===4){
     if(v===255){peer.sub.push(v);peer.state=3;}
     else if(v===240){
      const b=Buffer.from(peer.sub);
      if(b[0]===24 && b[1]===0)peer.type=b.subarray(2).toString('ascii');
      if(b[0]===31 && b.length===5)peer.size=[b.readUInt16BE(1),b.readUInt16BE(3)];peer.state=0;
     }else throw Error('Unexpected subnegotiation');
    }
   }
   if(bytes.length)peer.data.push(Buffer.from(bytes));ready();
  });
 });
 sip.on('error',e=>errors.push(e.message));pool.on('error',e=>errors.push(e.message));rtp.on('error',e=>errors.push(e.message));
 sip.on('invite',dialog=>{
  session=new CallSession(sip,dialog,{modemPool:pool});session.once('ended',v=>ended=v);
  session.setup().catch(e=>errors.push(e.message));
 });
 sip.on('ack',()=>session.activate().catch(e=>errors.push(e.message)));
 sip.on('bye',()=>session.onBye());sip.on('cancel',()=>session.onBye());
 dsp.on('connected',v=>events.push({type:'caller-CONNECT',bps:v.bps}));
 dsp.on('data',b=>callerData.push(Buffer.from(b)));
 dsp.on('audioOut',s=>rtp.send(s));rtp.on('audio',s=>dsp.receiveAudio(s));
 try{
  await new Promise(r=>bbs.listen(0,'127.0.0.1',r));
  // Choose a currently free loopback port for actual UDP+TCP SIP listeners.
  const probe=net.createServer();await new Promise(r=>probe.listen(0,'127.0.0.1',r));cfg.sip.port=probe.address().port;await new Promise(r=>probe.close(r));
  await pool.start();const b=backends[0],firstChild=b._vmChild;b.controlSocket.on('data',v=>control.push(Buffer.from(v)));
  await sip.start();
  sip._udpSocket.on('message',v=>sipRx.push(Buffer.from(v)));
  callerSock=dgram.createSocket('udp4');sipSock=dgram.createSocket('udp4');
  for(const s of [callerSock,sipSock])await new Promise(r=>s.bind(0,'127.0.0.1',r));
  sipSock.on('message',v=>sipTx.push(Buffer.from(v)));
  rtp.adoptSocket(callerSock);rtp.setCodec('PCMU',0);callerSock.on('message',v=>rtpRx.push(Buffer.from(v)));
  uac=new SipUacInternal({udpSocket:sipSock,peerAddress:'127.0.0.1',peerPort:cfg.sip.port,
   localAddress:'127.0.0.1',targetUri:`sip:modem@127.0.0.1:${cfg.sip.port}`});
  uac.on('error',e=>errors.push(e.message));
  negotiated=await uac.invite({localRtpPort:callerSock.address().port,
   offerCodecs:[{payloadType:0,name:'PCMU',clockRate:8000}],timeoutMs:10000});
  rtp.setRemote(negotiated.remoteRtpAddr,negotiated.remoteRtpPort);
  await until(()=>session?._dsp?.state==='CONFIRMED',15000,'Internal SIP activation deadline');
  session._rtpSock.on('message',v=>rtpTx.push(Buffer.from(v)));
  checks.actual_SIP_and_session=uac.state==='CONFIRMED' && session._active && pool.state==='checked_out';
  checks.loopback_bound=session._rtpSock.address().address==='127.0.0.1' && sip._udpSocket.address().address==='127.0.0.1';
  dsp.start();diag=setInterval(()=>console.log(JSON.stringify({events,prompts:prompts(),peerCount:peers.length,sessionActive:session._active})),5000);
  await until(()=>prompts()===1,35000,'CONNECT prompt after training/hold deadline');
  checks.real_training_and_banner=events.filter(e=>e.type==='answer-CONNECT').length===1 && events.some(e=>e.type==='caller-CONNECT') && text().includes(Buffer.from('PCPLUS DSP LAB V22 1200'));
  const destination=`127.0.0.1:${bbs.address().port}\r`;dsp.write(Buffer.from(destination));
  await until(()=>peers[0]?.ready && text().includes(down),20000,'Negotiation/downstream DSP deadline');
  checks.ANSI_geometry=peers[0].type==='ANSI' && JSON.stringify(peers[0].size)==='[80,25]';
  dsp.write(up);await until(()=>Buffer.concat(peers[0].data).length>=up.length,15000,'Upstream DSP/Telnet deadline');
  checks.exact_duplex=Buffer.concat(peers[0].data).equals(up) && text().subarray(text().indexOf(down),text().indexOf(down)+down.length).equals(down);
  checks.proxying_with_binary=session._telnet.state==='PROXYING' && peers[0].binaryLocal && peers[0].binaryRemote;
  peers[0].socket.end();await until(()=>prompts()===2,10000,'Return to bridge prompt deadline');
  checks.remote_close_keeps_carrier=b._connected && session._active && uac.state==='CONFIRMED';
  dsp.write(Buffer.from(destination));await until(()=>peers[1]?.ready && text().includes(Buffer.from('RECONNECTED\r\n')),15000,'TCP reconnect deadline');
  checks.reconnect_same_carrier=events.filter(e=>e.type==='answer-CONNECT').length===1 && session._active;
  peers[1].socket.end();await until(()=>prompts()===3,10000,'Second return to menu deadline');
  stats=JSON.parse(JSON.stringify(b._bridge.stats));const writer=b._dataWriter;
  dsp.write(Buffer.from('QUIT\r'));await until(()=>ended && uac.state==='TERMINATED',10000,'QUIT/SIP teardown deadline');
  dsp.stop();rtp.close();
  await until(()=>pool.state==='ready',45000,'Replacement warm VM deadline');
  replacementReadyNs=process.hrtime.bigint().toString();
  checks.session_teardown=!session._active && session._rtpSock===null && session._dsp===null && writer.closed && b.listenerCount('drain')===0;
  checks.pool_recycled=backends.length===2 && backends[1]!==b && b.state==='STOPPED';
  const secondChild=backends[1]._vmChild;
  await pool.stop();await sip.stop();
  await until(()=>[firstChild,secondChild].every(c=>c.exitCode!==null || c.signalCode!==null),5000,'All VM process exits deadline');
  checks.all_VMs_stopped=backends.every(b=>b.state==='STOPPED' && b._vmChild===null);
  checks.no_errors=errors.length===0;
 }catch(e){exception=e.stack;errors.push(e.message);}
 finally{
  if(diag)clearInterval(diag);dsp.stop();rtp.close();uac?.close();
  if(session?._active)session.hangup('cleanup');await pool.stop();
  for(const b of backends)await b.stop();if(sip._started)await sip.stop();if(sipSock)await new Promise(r=>sipSock.close(r));
  for(const p of peers)p.socket.destroy();await new Promise(r=>bbs.close(r));
  const resourcesClosedNs=process.hrtime.bigint();
  process.once('beforeExit',()=>{const beforeExitNs=process.hrtime.bigint();fs.writeFileSync(path.join(out,'cleanup-time.json'),JSON.stringify({replacement_ready_ns:replacementReadyNs,resources_closed_ns:resourcesClosedNs.toString(),before_exit_ns:beforeExitNs.toString(),before_exit_lag_ms:Number(beforeExitNs-resourcesClosedNs)/1e6},null,2)+'\n');});
  const captures={'caller-decoded.bin':text(),'control-wire.bin':Buffer.concat(control),
   'rtp-from-answer.bin':Buffer.concat(rtpRx.map(record)),'rtp-from-caller.bin':Buffer.concat(rtpTx.map(record)),
   'sip-to-server.bin':Buffer.concat(sipRx.map(record)),'sip-to-caller.bin':Buffer.concat(sipTx.map(record))};
  for(let i=0;i<peers.length;i++){captures[`peer-${i}-input.bin`]=Buffer.concat(peers[i].input);captures[`peer-${i}-output.bin`]=Buffer.concat(peers[i].output);}
  for(const [n,b] of Object.entries(captures))fs.writeFileSync(path.join(out,n),b);
  fs.writeFileSync(path.join(out,'node-result.json'),JSON.stringify({passed:!exception && Object.values(checks).every(Boolean),checks,errors,exception,events,ended,negotiated,stats,
   config:{sip:cfg.sip.host,port:cfg.sip.port,bindAddress:cfg.rtp.bindAddress,terminalType:'ANSI',cols:80,rows:25,
    holdMs:cfg.modem.native.postTrainIdleMs,quiescenceMs:cfg.modem.native.postTrainQuiescenceMs,attachMaxMs:cfg.modem.native.postTrainAttachMaxMs,atInit},
   peers:peers.map(p=>({type:p.type,size:p.size,ready:p.ready,negotiation:p.negotiation})),node:process.version,
   scope:'Actual loopback external/internal SIP legs, CallSession constructor/setup/activation/teardown, real modem pool/VM, originating and answering DSP and candidate Telnet proxy. Synthetic Telnet application peer; no DOS/BBS software or physical modem/ATA.'},null,2)+'\n');
 }
 assert(!exception,exception);assert(Object.values(checks).every(Boolean));
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
