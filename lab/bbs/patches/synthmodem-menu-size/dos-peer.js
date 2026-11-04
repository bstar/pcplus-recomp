'use strict';
// SPDX-License-Identifier: GPL-2.0-or-later
// Isolated fake Hayes boundary -> actual staged proxy -> real loopback TCP.
// This peer never supplies a terminal size reply on behalf of DOS.
const net=require('net'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
const [candidate,out]=process.argv.slice(2);
const config=require(path.join(candidate,'config'));
config.telnet.terminalSizeProbeTimeoutMs=3000;
const {TelnetProxy}=require(path.join(candidate,'src/telnet/TelnetProxy'));
const records={commands:[],dimensions:[],queries:0,tcpConnections:0,errors:[],serialIn:[],serialOut:[],tcpIn:[],app:[]};
let proxy,serialSocket,bbsSocket,state='data',verb=null,sub=[],line=[],online=false,finished=false;
const saved=()=>({commands:records.commands,dimensions:records.dimensions,queries:records.queries,tcpConnections:records.tcpConnections,errors:records.errors});
function serialWrite(data){records.serialOut.push(Buffer.from(data));if(data.equals(Buffer.from('\x1b[18t')))records.queries++;return serialSocket.write(data);}
function parseTcp(data){
 for(const b of data){
  if(state==='data'){if(b===255)state='iac';else records.app.push(b);}
  else if(state==='iac'){
   if(b===255){records.app.push(b);state='data';}
   else if([251,252,253,254].includes(b)){verb=b;state='option';}
   else if(b===250){sub=[];state='sub';}else state='data';
  }else if(state==='option'){state='data';}
  else if(state==='sub'){if(b===255)state='subiac';else sub.push(b);}
  else if(state==='subiac'){
   if(b===255){sub.push(b);state='sub';}
   else if(b===240){
    if(sub[0]===31){assert.equal(sub.length,5);records.dimensions.push({cols:sub[1]*256+sub[2],rows:sub[3]*256+sub[4]});
     bbsSocket.write(Buffer.from('\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c'));
    }state='data';
   }else throw new Error('bad subnegotiation');
  }
 }
}
function finish(){
 if(finished)return;finished=true;
 proxy?.disconnect();bbsSocket?.destroy();serialSocket?.destroy();serial.close();bbs.close();
 for(const [name,data] of [['serial-in.bin',Buffer.concat(records.serialIn)],['serial-out.bin',Buffer.concat(records.serialOut)],['tcp-in.bin',Buffer.concat(records.tcpIn)],['application-in.bin',Buffer.from(records.app)]])fs.writeFileSync(path.join(out,name),data);
 fs.writeFileSync(path.join(out,'peer-result.json'),JSON.stringify(saved(),null,2)+'\n');
}
const bbs=net.createServer(s=>{
 records.tcpConnections++;bbsSocket=s;
 s.on('error',e=>records.errors.push(e.message));
 s.on('data',d=>{records.tcpIn.push(Buffer.from(d));try{parseTcp(d);}catch(e){records.errors.push(e.message);finish();}});
 s.write(Buffer.from([255,253,31,255,253,0,255,251,0]));
});
const serial=net.createServer(s=>{
 serialSocket=s;s.on('error',e=>records.errors.push(e.message));s.on('close',finish);
 s.on('data',data=>{
  records.serialIn.push(Buffer.from(data));
  if(online){proxy.receive(data);return;}
  for(let i=0;i<data.length;i++){
   const b=data[i];if(b!==13){line.push(b);continue;}
   const command=Buffer.from(line).toString();line=[];records.commands.push(command);
   if(command==='ATZ')serialWrite(Buffer.from('\r\nOK\r\n'));
   else if(command==='ATD1'){
    online=true;serialWrite(Buffer.from('CONNECT\r\n'));proxy=new TelnetProxy();proxy.on('disconnect',()=>s.end());proxy.attach(serialWrite);
    if(i+1<data.length)proxy.receive(data.subarray(i+1));return;
   }else records.errors.push('unexpected command');
  }
 });
});
bbs.listen(0,'127.0.0.1',()=>{
 config.terminal.aliases.loc=`127.0.0.1:${bbs.address().port}`;
 serial.listen(0,'127.0.0.1',()=>fs.writeFileSync(path.join(out,'ready.json'),JSON.stringify({port:serial.address().port})+'\n'));
});
process.on('SIGTERM',()=>{records.errors.push('parent terminated peer');finish();});
setTimeout(()=>{records.errors.push('peer deadline');finish();},25000).unref();
