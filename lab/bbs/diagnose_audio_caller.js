'use strict';
// Offline independent receive pass over captured caller PCMU. No live I/O.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const runtime=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
const file=path.join(runtime,'source/src/dsp/protocols/V22Demodulator.js');
const {QAMDemodulator}=require(file),m=new QAMDemodulator({carrier:1200,bitsPerSymbol:2});
const capture=path.join(out,'rtp-from-caller.bin'),w=fs.readFileSync(capture),received=[];
let at=0,packet=0;m.on('data',b=>received.push({packet,hex:b.toString('hex')}));
while(at<w.length){
 const n=w.readUInt32LE(at);at+=4;
 if(n!==172 || at+n>w.length)throw Error('Invalid recorded PCMU packet');
 const s=new Float32Array(n-12);
 for(let i=12;i<n;i++){const v=w[at+i]^255,t=(((v&15)<<3)+132)<<((v>>4)&7);s[i-12]=(v&128?132-t:t-132)/32768;}
 m.process(s);packet++;at+=n;
}
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const result={packets:packet,received,checker_sha256:sha(__filename),capture_sha256:sha(capture),
 decoder_sha256:sha(file),scope:'Offline native QAM receiver over the observed external caller RTP packets. This does not establish what the in-VM PJSIP jitter buffer or proprietary receiver consumed.'};
fs.writeFileSync(path.join(out,'offline-caller.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({packets:packet,decoded_bytes:received.length,tail:received.slice(-6)}));
