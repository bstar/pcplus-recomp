'use strict';
// Independent native receiver over the actual guest's pre-resampling PCM dump.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const runtime=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
const decoder=path.join(runtime,'source/src/dsp/protocols/V22Demodulator.js');
const {QAMDemodulator}=require(decoder),m=new QAMDemodulator({carrier:1200,bitsPerSymbol:2});
const input=path.join(out,'modem_rx_8k.raw'),b=fs.readFileSync(input),received=[];assertEven(b.length);
let sample=0;m.on('data',v=>received.push({sample,hex:v.toString('hex')}));
for(let at=0;at<b.length;at+=320){const n=Math.min(320,b.length-at)/2,s=new Float32Array(n);for(let i=0;i<n;i++)s[i]=b.readInt16LE(at+i*2)/32768;sample=at/2;m.process(s);}
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const decoded=Buffer.from(received.map(v=>v.hex).join(''),'hex'),expected=fs.readFileSync(path.join(out,'expected-upstream.bin'));
const result={samples:b.length/2,decoded_bytes:decoded.length,equals_authored_upstream:decoded.equals(expected),received,
 checker_sha256:sha(__filename),capture_sha256:sha(input),decoder_sha256:sha(decoder),
 scope:'Offline native QAM decode of actual guest pre-resampling 8kHz PCM. Distinct from the proprietary guest DSP; no injected live bytes or connection flags.'};
fs.writeFileSync(path.join(out,'offline-guest.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({samples:result.samples,decoded_bytes:decoded.length,equals_authored_upstream:result.equals_authored_upstream}));
function assertEven(n){if(n%2)throw Error('Invalid signed16 PCM size');}
