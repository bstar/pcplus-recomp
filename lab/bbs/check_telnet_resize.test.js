'use strict';
// SPDX-License-Identifier: GPL-2.0-or-later
// Isolated candidate: no production service/configuration or serial interception.
const assert = require('node:assert/strict');
const { test } = require('node:test');
const { TelnetCodec } = require(process.env.SYNTHMODEM_CODEC_UNDER_TEST);
const { TelnetCodec: Baseline } = require(process.env.SYNTHMODEM_CODEC_BASELINE);
const IAC=255, DO=253, DONT=254, WILL=251, BINARY=0, NAWS=31;
function codec(Type=TelnetCodec) {
  const wire=[],screen=[];
  const value=new Type({send:b=>wire.push(Buffer.from(b)),display:b=>screen.push(Buffer.from(b)),terminalCols:80,terminalRows:24});
  return {value,wire,screen};
}
function naws(cols,rows) {
  const payload=[31,cols>>8,cols&255,rows>>8,rows&255],out=[255,250];
  for(const b of payload){out.push(b);if(b===255)out.push(b);}
  return Buffer.from([...out,255,240]);
}
function enable(c){c.value.feed(Buffer.from([IAC,DO,NAWS]));c.wire.length=0;}

test('ordinary startup, negotiation and bytewise data equal the installed baseline',()=>{
  const a=codec(),b=codec(Baseline);
  for(const c of [a,b]){
    c.value.start();
    const input=Buffer.from([255,253,31,255,253,0,255,251,0,13,0,65,255,255]);
    for(const n of input)c.value.feed(Buffer.from([n]));
  }
  assert.deepEqual(a.wire,b.wire);assert.deepEqual(a.screen,b.screen);
  assert.deepEqual(a.value.encode(Buffer.from([0,13,10,255,27])),b.value.encode(Buffer.from([0,13,10,255,27])));
});
test('resize before agreement caches the last dimensions without sending unsolicited NAWS',()=>{
  const c=codec();c.value.start();c.wire.length=0;
  assert.deepEqual(c.value.resize(132,43),{changed:true,advertised:false});
  assert.deepEqual(c.value.resize(80,25),{changed:true,advertised:false});assert.equal(c.wire.length,0);
  for(const b of [255,253,31])c.value.feed(Buffer.from([b]));
  assert.deepEqual(c.wire,[naws(80,25)]);
});
test('accepted resize emits one exact width/height message; duplicates emit none',()=>{
  const c=codec();enable(c);
  assert.deepEqual(c.value.resize(80,25),{changed:true,advertised:true});
  assert.deepEqual(c.wire,[Buffer.from([255,250,31,0,80,0,25,255,240])]);
  assert.deepEqual(c.value.resize(80,25),{changed:false,advertised:false});assert.equal(c.wire.length,1);
  assert.deepEqual(c.value.resize(132,50),{changed:true,advertised:true});assert.deepEqual(c.wire[1],naws(132,50));
});
test('all FF byte positions and boundary dimensions are escaped in network order',()=>{
  for(const cols of [1,24,80,255,256,511,65280,65535])for(const rows of [1,25,255,256,511,65535]){
    const c=codec();enable(c);c.value.resize(cols,rows);assert.deepEqual(c.wire,[naws(cols,rows)]);
  }
});
test('invalid dimensions never partially commit or send, before or after agreement',()=>{
  const invalid=[0,-1,65536,1.5,NaN,Infinity,'80',null,undefined,80n,{},[]];
  for(const accepted of [false,true])for(const n of invalid)for(const args of [[n,25],[132,n]]){
    const c=codec();if(accepted)enable(c);
    assert.throws(()=>c.value.resize(...args),/Invalid dimensions/);
    assert.equal(c.value.cols,80);assert.equal(c.value.rows,24);assert.deepEqual(c.wire,[]);
  }
});
test('peer withdrawal suppresses updates and later agreement announces the latest size',()=>{
  const c=codec();enable(c);c.value.feed(Buffer.from([IAC,DONT,NAWS]));
  assert.deepEqual(c.wire,[Buffer.from([IAC,252,NAWS])]);c.wire.length=0;
  assert.deepEqual(c.value.resize(80,25),{changed:true,advertised:false});assert.deepEqual(c.wire,[]);
  c.value.feed(Buffer.from([IAC,DO,NAWS]));assert.deepEqual(c.wire,[Buffer.from([IAC,WILL,NAWS]),naws(80,25)]);
  c.value.feed(Buffer.from([IAC,DO,NAWS]));assert.equal(c.wire.length,2);
});
test('resize preserves an incomplete IAC receive sequence',()=>{
  const c=codec();enable(c);c.value.feed(Buffer.from([IAC,WILL,BINARY]));c.screen.length=0;
  c.value.feed(Buffer.from([IAC]));c.value.resize(80,25);c.value.feed(Buffer.from([IAC,65]));
  assert.deepEqual(Buffer.concat(c.screen),Buffer.from([255,65]));
});
test('resize preserves the NVT CR NUL receive state',()=>{
  const c=codec();enable(c);c.value.feed(Buffer.from([13]));assert.equal(c.value.rxCR,true);
  c.value.resize(80,25);c.value.feed(Buffer.from([0,65]));
  assert.deepEqual(Buffer.concat(c.screen),Buffer.from([13,65]));
});
test('binary payload including apparent serial control strings survives interleaved metadata',()=>{
  const tx=codec(),rx=codec();enable(tx);
  tx.value.feed(Buffer.from([IAC,DO,BINARY]));rx.value.feed(Buffer.from([IAC,WILL,BINARY]));
  tx.wire.length=0;rx.screen.length=0;
  const payload=Buffer.concat([Buffer.from(Array.from({length:256},(_,i)=>i)),Buffer.from('\x1b[8;25;80t\x1dSIZE 80 24\r')]);
  const chunks=[];
  for(let i=0;i<payload.length;++i){
    chunks.push(tx.value.encode(payload.subarray(i,i+1)));
    if(i===13||i===254){tx.value.resize(80,i===13?25:24);chunks.push(...tx.wire.splice(0));}
  }
  for(const chunk of chunks)for(const byte of chunk)rx.value.feed(Buffer.from([byte]));
  assert.deepEqual(Buffer.concat(rx.screen),payload);
});
test('metadata API does not introduce NVT data or echoes',()=>{
  const c=codec();enable(c);c.value.resize(80,25);
  assert.deepEqual(c.screen,[]);assert.deepEqual(c.value.encode(Buffer.from([13,0,10,255])),Buffer.from([13,0,0,10,255,255]));
});
