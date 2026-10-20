'use strict';
// Actual tunnel TCP/UDP routing and SIP endpoints; VM datagrams are fixtures.
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),net=require('net'),dgram=require('dgram');
const root=path.resolve(process.argv[2]),baseline=process.argv[3]==='baseline';
require(path.join(root,'config.js')).logging.level='error';
const {UdpTcpTunnel}=require(path.join(root,'src/tunnel/UdpTcpTunnel.js'));
const {VmRegistrar}=require(path.join(root,'src/sip/VmRegistrar.js'));
const {SipUacInternal}=require(path.join(root,'src/sip/SipUacInternal.js'));
const sip=require(path.join(root,'src/sip/SipParser.js'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function until(fn){const end=Date.now()+2000;while(!fn()){assert(Date.now()<end,'Network fixture deadline');await sleep(5);}}
function frame(ch,payload){const h=Buffer.alloc(7);h.writeUInt16LE(payload.length+5);h[2]=ch;h.writeUInt16LE(39999,3);h.writeUInt16LE(5062,5);return Buffer.concat([h,payload]);}
function request(method,n,contact=true){return Buffer.from(`${method} sip:modem@127.0.0.1 SIP/2.0\r\nVia: SIP/2.0/UDP 127.0.0.1:39999;branch=z9hG4bKlab${n}\r\nFrom: <sip:modem@127.0.0.1>;tag=lab\r\nTo: <sip:modem@127.0.0.1>\r\nCall-ID: registrar-lab\r\nCSeq: ${n} ${method}\r\n${contact?'Contact: <sip:modem@127.0.0.1:39999>\r\n':''}Expires: 600\r\nContent-Length: 0\r\n\r\n`);}
async function main(){
 const udp=[];for(let i=0;i<3;i++){const s=dgram.createSocket('udp4');await new Promise(r=>s.bind(0,'127.0.0.1',r));udp.push(s);}
 const probe=net.createServer();await new Promise(r=>probe.listen(0,'127.0.0.1',r));const port=probe.address().port;await new Promise(r=>probe.close(r));
 const ports=[];for(let i=0;i<3;i++){const s=dgram.createSocket('udp4');await new Promise(r=>s.bind(0,'127.0.0.1',r));ports.push(s.address().port);await new Promise(r=>s.close(r));}
 const t=new UdpTcpTunnel({tcp:{mode:'listen',host:'127.0.0.1',port},sipPort:ports[0],rtpPort:ports[1],rtcpPort:ports[2]});
 const reg=new VmRegistrar({tunnel:t}),errors=[],observed=[],packets=[],media=[[],[],[]];let peer,uac,buffer=Buffer.alloc(0),refreshes=0;
 t.on('error',e=>errors.push(e.message));reg.on('error',e=>errors.push(e.message));reg.on('refreshed',()=>refreshes++);
 t.on('frame-rx',(ch,src,dst,b)=>observed.push({channel:ch,hex:b.toString('hex')}));
 try{
  await t.start();reg.start();peer=net.createConnection({host:'127.0.0.1',port});await new Promise(r=>peer.once('connect',r));
  peer.on('data',b=>{buffer=Buffer.concat([buffer,b]);while(buffer.length>=2){const size=buffer.readUInt16LE();if(buffer.length<size+2)break;packets.push({channel:buffer[2],body:Buffer.from(buffer.subarray(7,size+2))});buffer=buffer.subarray(size+2);}});
  uac=new SipUacInternal({udpSocket:udp[0],peerAddress:'127.0.0.1',peerPort:ports[0],targetUri:'sip:modem@127.0.0.1:39999'});uac.on('error',e=>errors.push(e.message));
  for(let i=0;i<3;i++){udp[i].on('message',b=>media[i].push(Buffer.from(b)));udp[i].send(Buffer.from('learn'),ports[i],'127.0.0.1');}
  await until(()=>packets.length>=3);
  function responses(n){return packets.filter(p=>p.channel===0 && p.body.toString().startsWith('SIP/2.0')).map(p=>sip.parse(p.body.toString())).filter(p=>p.getHeader('cseq')?.startsWith(n+' ')).map(p=>p.statusCode).sort();}
  const checks={};
  for(const n of [1,2]){peer.write(frame(0,request('REGISTER',n)));await until(()=>responses(n).length>=(baseline?2:1));await sleep(50);assert.deepEqual(responses(n),baseline?[200,405]:[200]);}
  checks[baseline?'duplicate_response_reproduced':'registration_and_refresh_exclusive']=true;
  assert.equal(reg.currentBinding.registerCount,2);assert.equal(refreshes,1);checks.binding_refresh=true;
  peer.write(frame(0,request('REGISTER',3,false)));await until(()=>responses(3).length>=(baseline?2:1));await sleep(50);assert.deepEqual(responses(3),baseline?[400,405]:[400]);checks[baseline?'duplicate_error_reproduced':'error_REGISTER_has_single_owner']=true;
  peer.write(frame(0,request('OPTIONS',4)));await until(()=>responses(4).length===1);assert.deepEqual(responses(4),[405]);checks.other_SIP_still_delivered=true;
  for(let i=1;i<3;i++){const b=Buffer.from([0,255,i,13,10]);peer.write(frame(i,b));await until(()=>media[i].length===1);assert.deepEqual(media[i][0],b);}checks.RTP_RTCP_unchanged=true;
  reg.stop();peer.write(frame(0,request('REGISTER',5)));await until(()=>responses(5).length===1);assert.deepEqual(responses(5),[405]);checks.stop_releases_ownership=true;
  assert.equal(observed.length,7);checks.observers_still_see_all_frames=true;assert.deepEqual(errors,[]);checks.no_errors=true;
  console.log(JSON.stringify({passed:true,baseline,checks,responses:Object.fromEntries([1,2,3,4,5].map(n=>[n,responses(n)]))}));
 }finally{uac?.close();reg.stop();await t.stop();peer?.destroy();for(const s of udp)await new Promise(r=>s.close(r));}
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
