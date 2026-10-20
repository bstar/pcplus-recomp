'use strict';
// Observe the actual internal tunnel socket; preserve write args/return values.
const fs=require('fs'),path=require('path');
class InternalSipCapture {
 constructor(out){this.out=out;this.rx=[];this.tx=[];}
 attach(backend){
  const s=backend._tunnel.tcpSocket,write=s.write;
  s.on('data',b=>this.rx.push(Buffer.from(b)));
  const tx=this.tx;s.write=function(chunk,...args){tx.push(Buffer.from(chunk));return write.call(this,chunk,...args);};
 }
 save(){for(const [name,parts] of [['internal-from-guest.bin',this.rx],['internal-to-guest.bin',this.tx]])fs.writeFileSync(path.join(this.out,name),Buffer.concat(parts));}
}
module.exports={InternalSipCapture};
