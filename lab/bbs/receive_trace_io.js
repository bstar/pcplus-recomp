'use strict';
// Diagnostic-only observers and existing PCM dump export; no online replies.
const fs=require('fs'),path=require('path'),net=require('net'),assert=require('assert/strict');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const record=b=>{const h=Buffer.alloc(4);h.writeUInt32LE(b.length);return Buffer.concat([h,b]);};
class ReceiveTrace {
 constructor(out){this.out=out;this.events=[];this.packets={};this.guest=[];this.buffer=Buffer.alloc(0);this.qemuPath=path.join(__dirname,'qemu_trace_wrapper.py');}
 event(type,v={}){this.events.push({type,ns:process.hrtime.bigint().toString(),...v});}
 packet(type,b){const list=this.packets[type]??=[];list.push(Buffer.from(b));this.event(type,{packet:list.length-1,sequence:b.length>=12?b.readUInt16BE(2):null,timestamp:b.length>=12?b.readUInt32BE(4):null});}
 async start(){
  this.server=net.createServer(s=>{assert(!this.socket);this.socket=s;s.on('data',b=>this.buffer=Buffer.concat([this.buffer,b]));s.on('error',e=>this.event('export-socket-error',{message:e.message}));});
  await new Promise(r=>this.server.listen(0,'127.0.0.1',r));process.env.PCPLUS_TRACE_PORT=String(this.server.address().port);
 }
 attach(b){
  b.on('data',v=>{this.guest.push(Buffer.from(v));this.event('guest-data',{hex:v.toString('hex')});});
  b.controlSocket.on('data',v=>this.event('guest-control',{bytes:v.length}));
  b._tunnel.udp.rtp.on('message',v=>this.packet('rtp-to-guest',v));
 }
 finishWorkload(expected){this.event('workload-end');fs.writeFileSync(path.join(this.out,'guest-workload.bin'),Buffer.concat(this.guest));fs.writeFileSync(path.join(this.out,'expected-upstream.bin'),expected);}
 async export(){
  const until=async(fn,label)=>{const end=Date.now()+15000;while(!fn()){assert(Date.now()<end,label);await sleep(10);}};
  await until(()=>this.socket,'Export socket');this.event('export-start');this.socket.write('DUMP\n');
  for(const name of ['modem_rx_8k.raw','modem_rx.raw','modem_tx.raw']){
   await until(()=>this.buffer.includes(10),'Export header');const at=this.buffer.indexOf(10),header=this.buffer.subarray(0,at).toString().trim().split(/\s+/);this.buffer=this.buffer.subarray(at+1);
   assert.equal(header[0],name);const size=Number(header[1]);assert(Number.isInteger(size)&&size>0&&size<16*1024*1024);
   await until(()=>this.buffer.length>=size,'Export payload');fs.writeFileSync(path.join(this.out,name),this.buffer.subarray(0,size));this.buffer=this.buffer.subarray(size);
  }
  await until(()=>this.buffer.includes(10),'Export DONE');assert.equal(this.buffer.toString(),'DONE\n');this.exported=true;this.event('export-complete');
 }
 async close(){this.socket?.destroy();if(this.server?.listening)await new Promise(r=>this.server.close(r));for(const [name,parts] of Object.entries(this.packets))if(name==='rtp-to-guest')fs.writeFileSync(path.join(this.out,name+'.bin'),Buffer.concat(parts.map(record)));fs.writeFileSync(path.join(this.out,'timing.jsonl'),this.events.map(v=>JSON.stringify(v)+'\n').join(''));}
}
module.exports={ReceiveTrace};
