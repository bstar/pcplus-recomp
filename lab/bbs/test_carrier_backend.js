'use strict';
// Actual backend/parser/writer methods; no VM/SIP/RTP resources are started.
const assert=require('assert/strict'),fs=require('fs'),path=require('path'),crypto=require('crypto');
const {EventEmitter}=require('events');
const runtime=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
const source=path.join(runtime,'source');
const config=require(path.join(source,'config.js'));config.logging.level='error';
const {PjsipBackend}=require(path.join(source,'src/backends/PjsipBackend.js'));
const wire=require(path.join(source,'vm/qemu-runner/wire.js'));
const checks={};
class Socket extends EventEmitter {
 constructor(){super();this.frames=[];this.destroyed=false;this.ready=true;this.writableLength=0;}
 write(b){if(this.fail)throw Error('test transport failure');this.frames.push(Buffer.from(b));return this.ready;}
 destroy(){this.destroyed=true;this.emit('close');}
}
function fixture(){
 const b=new PjsipBackend({qemuPath:'unused',kernelPath:'unused',initrdPath:'unused'}),socket=new Socket();
 b.controlSocket=socket;b.state='READY';
 const events=[];b.on('connected',v=>events.push({type:'connect',bps:v.bps}));
 b.on('data',v=>events.push({type:'data',hex:v.toString('hex')}));
 const ended=type=>{assert(!b._connected && !b._dataWriter && !b._currentBps && b._currentProtocol===null);events.push({type});};
 b.on('silenceHangup',()=>ended('hangup'));b.on('error',()=>ended('error'));b._setupControlParser();
 const send=(type,body)=>socket.emit('data',wire.encode(type,body));
 const status=event=>send(wire.TYPE.MODEM_STATUS,JSON.stringify(event));
 return {b,socket,events,send,status};
}
async function main(){
 for(const mode of ['status','text','HANGUP','SIP']){
  const f=fixture(),{b,socket,events,send,status}=f;
  send(wire.TYPE.AT_RESPONSE,'CONNECT 1200\r\n');status({event:'connect',rate:1200});
  assert.equal(events.filter(v=>v.type==='connect').length,1);
  send(wire.TYPE.DATA_RX,Buffer.concat([Buffer.from('NO CARRIER\r\n'),Buffer.from([0,255])]));
  assert(b._connected);assert.equal(events.at(-1).type,'data');
  socket.ready=false;assert.equal(b.write(Buffer.alloc(16384,65)),false);const writer=b._dataWriter;
  assert(writer.length>0);const writes=socket.frames.length;
  b._ptyLineBuf='partial';b._ptyUnterminatedTimer=setTimeout(()=>{throw Error('stale result timer');},500);
  if(mode==='status')status({event:'nocarrier'});
  if(mode==='text')send(wire.TYPE.AT_RESPONSE,'\r\nNO CARRIER\r\n');
  if(mode==='HANGUP')send(wire.TYPE.HANGUP,Buffer.alloc(0));
  if(mode==='SIP')b._retireCarrier('internal SIP ended');
  assert(writer.closed && writer.length===0 && !b._ptyUnterminatedTimer && !b._ptyLineBuf);
  assert.equal(socket.listenerCount('drain'),0);
  status({event:'connect',rate:14400});send(wire.TYPE.AT_RESPONSE,'CONNECT 14400\r\n');
  send(wire.TYPE.DATA_RX,'late data');status({event:'nocarrier'});send(wire.TYPE.HANGUP,Buffer.alloc(0));
  b._retireCarrier('late SIP');b._controlFailed(Error('late closure'));socket.emit('drain');
  assert.equal(events.filter(v=>v.type==='connect').length,1);
  assert.equal(events.filter(v=>v.type==='hangup').length,1);
  assert.equal(events.filter(v=>v.type==='data').length,1);
  assert.equal(events.filter(v=>v.type==='error').length,0);
  assert.throws(()=>b.write(Buffer.from('late')));assert.throws(()=>b.sendAt('AT'));
  assert.equal(socket.frames.length,writes);
  checks[mode+'_retires_before_notification_and_blocks_late_work']=true;
  await b.stop();
 }
 for(const result of ['BUSY','NO DIALTONE','NO CARRIER']){
  const {b,send,events}=fixture();send(wire.TYPE.AT_RESPONSE,result+'\r\n');
  send(wire.TYPE.AT_RESPONSE,'CONNECT 1200\r\n');
  assert.equal(events.filter(v=>v.type==='hangup').length,1);
  assert.equal(events.filter(v=>v.type==='connect').length,0);
  checks[result+'_failure_before_CONNECT_is_terminal']=true;await b.stop();
 }
 {
  const {b,status,events,send}=fixture();send(wire.TYPE.AT_RESPONSE,'CONNECT\r\n');
  status({event:'connect',rate:1200});assert.equal(b._currentBps,1200);
  assert.equal(events.filter(v=>v.type==='connect').length,1);
  checks.CONNECT_duplicate_completes_rate_without_duplicate_event=true;await b.stop();
 }
 for(const mode of ['control_failure','parser_failure','writer_failure']){
  const {b,socket,send,events}=fixture();send(wire.TYPE.AT_RESPONSE,'CONNECT 1200\r\n');
  socket.ready=false;b.write(Buffer.alloc(16384,42));const writer=b._dataWriter;
  if(mode==='control_failure')b._controlFailed(Error('test closure'));
  if(mode==='parser_failure')socket.emit('data',Buffer.from([0,0,0]));
  if(mode==='writer_failure'){socket.fail=true;socket.emit('drain');}
  assert(writer.closed && !b._dataWriter && b._carrierEnded && !b._connected);
  assert.equal(events.filter(v=>v.type==='error').length,1);
  b._controlFailed(Error('duplicate'));send(wire.TYPE.AT_RESPONSE,'CONNECT 1200\r\n');
  assert.equal(events.filter(v=>v.type==='error').length,1);
  assert.equal(events.filter(v=>v.type==='connect').length,1);
  checks[mode+'_retires_writer_before_one_error']=true;await b.stop();
 }
 {
  const {b,events,status}=fixture();await b.stop();status({event:'connect',rate:1200});
  assert(b._carrierEnded && !b._connected && events.length===0);
  checks.stop_blocks_late_events_without_hangup=true;
 }
 const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
 const result={passed:Object.values(checks).every(Boolean),checks,node:process.version,
  inputs:Object.fromEntries([__filename,path.join(source,'src/backends/PjsipBackend.js'),path.join(source,'src/backends/ControlWriter.js'),path.join(source,'vm/qemu-runner/wire.js')].map(p=>[p,sha(p)])),
  scope:'Actual backend constructor/parser/writer/stop with modeled sockets and supplied state transitions. No VM, real SIP ended callback or modem DSP/carrier loss.'};
 fs.writeFileSync(path.join(out,'backend-result.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
}
main().catch(error=>{console.error(error.stack);process.exitCode=1;});
