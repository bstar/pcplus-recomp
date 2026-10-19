'use strict';
// Real Client -> exact owned GameDetails draw/key/leave code. Data and the
// surrounding previous-menu owner are synthetic; initSequence/SQLite/login
// are exercised separately by the DOS integration runner.
const assert=require('assert/strict'),fs=require('fs'),path=require('path');
const crypto=require('crypto');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const {PassThrough}=require('stream');
const root=path.resolve(process.argv[2]),fixed=process.argv.includes('--fixed');
require(path.join(root,'test/setup.js'));
require(path.join(root,'core/config.js')).get().logging={traceUserKeyboardInput:false};
const {Client}=require(path.join(root,'core/client.js'));
const GameDetails=require(path.join(root,'mods/loc_game_details/loc_game_details.js')).getModule;
const baselineAt=process.argv.indexOf('--baseline');
const baseline=baselineAt<0?null:JSON.parse(fs.readFileSync(process.argv[baselineAt+1],'utf8')).unfragmented;
if(fixed)assert.ok(baseline,'Fixed run requires stock unfragmented parity');
const unfragmented={};let checks=0,fragmentedDifferences=0,unexpectedLeaves=0;
function fixture(offset=0){
 const client=new Client(),output=new PassThrough(),writes=[];
 output.on('data',b=>writes.push(Buffer.from(b)));
 client.setInputOutput(new PassThrough(),output);client.user.isAuthenticated=()=>false;
 client.disconnect=()=>{};client.dataHandler=b=>client.emit('data',b);
 client.term.termWidth=80;client.term.termHeight=25;
 const view=new GameDetails({client,menuName:'notesProbe',menuConfig:{config:{interrupt:'never'}},extraArgs:{fileId:1}});
 view.active=true;view.tab='nfo';view.offset=offset;view.file={fileName:'PCXTEST.BIN',desc:'Synthetic notes probe'};
 view.notes=[{kind:'nfo',member:'PCPLUS.NFO',storage:'pcplus_transfer',text:Array.from({length:22},(_,i)=>`PCPLUS NFO LINE ${String(i+1).padStart(2,'0')} : synthetic navigation fixture`).join('\n')},{kind:'diz',member:'FILE_ID.DIZ',storage:'pcplus_transfer',text:'Synthetic FILE_ID.DIZ'}];
 view.scanStatus='Complete synthetic notes';let leaves=0;
 view.prevMenu=()=>{++leaves;view.leave();};
 client.on('key press',view.handler);view.draw();
 return {write:b=>client.emit('data',Buffer.from(b)),snapshot:()=>({tab:view.tab,offset:view.offset,leaves,active:view.active,headers:[...Buffer.concat(writes).toString('ascii').matchAll(/(NFO|OVERVIEW|FILE_ID[.]DIZ) \| lines (\d+)-(\d+)\/(\d+)/g)].map(m=>m[0])}),close:()=>{view.leave();client.end();}};
}
function run(parts,offset){const f=fixture(offset);for(const part of parts)f.write(part);const result=f.snapshot();f.close();return result;}
function partitions(bytes){
 const out=[];
 for(let mask=1;mask<(1<<(bytes.length-1));++mask){
  const parts=[];let start=0;
  for(let i=0;i<bytes.length-1;++i)if(mask&(1<<i)){parts.push(bytes.subarray(start,i+1));start=i+1;}
  parts.push(bytes.subarray(start));out.push(parts);
 }
 return out;
}
for(const [wire,offset,expected] of [
 ['\x1b[A',5,4],['\x1b[B',5,6],['\x1b[5~',8,0],['\x1b[6~',0,9],
 ['\x1b[H',9,0],['\x1b[F',0,9],['\x1b[1~',9,0],['\x1b[4~',0,9],
 ['n\x1b[B\x1b[6~',9,9],
]){
 const key=JSON.stringify([wire,offset]);const bytes=Buffer.from(wire),reference=run([bytes],offset);
 assert.equal(reference.offset,expected);assert.equal(reference.leaves,0);assert.equal(reference.active,true);
 assert.equal(reference.headers.at(-1),`NFO | lines ${expected+1}-${Math.min(expected+15,24)}/24`);
 unfragmented[key]=reference;if(fixed)assert.deepEqual(reference,baseline[key],'Unfragmented parity');++checks;
 for(const parts of partitions(bytes)){
  const got=run(parts,offset);
  if(fixed)assert.deepEqual(got,reference,JSON.stringify(parts.map(p=>p.toString('hex'))));
  else if(JSON.stringify(got)!==JSON.stringify(reference))++fragmentedDifferences;
  if(got.leaves)++unexpectedLeaves;++checks;
 }
}
// Normal tab switching, reset-to-top, direct Q and handler removal stay intact.
for(const [wire,tab] of [['i','diz'],['o','overview'],['in','nfo']]){
 const got=run([Buffer.from(wire)],9);assert.equal(got.tab,tab);assert.equal(got.offset,0);assert.equal(got.leaves,0);++checks;
}
const f=fixture();f.write(Buffer.from('q'));const left=f.snapshot();
assert.equal(left.leaves,1);assert.equal(left.active,false);f.write(Buffer.from('n\x1b[B'));
assert.deepEqual(f.snapshot(),left,'Departed module must not handle later keys');f.close();++checks;
if(!fixed){assert.ok(fragmentedDifferences>0);assert.ok(unexpectedLeaves>0);}
console.log(JSON.stringify({passed:true,fixed,checks,fragmented_differences:fragmentedDifferences,unexpected_leaves:unexpectedLeaves,unfragmented,
 checker_sha256:sha(__filename),client_sha256:sha(path.join(root,'core/client.js')),
 module_sha256:sha(path.join(root,'mods/loc_game_details/loc_game_details.js')),
 helper_sha256:sha(path.join(root,'mods/black_flag_files/helpers.js')),node:process.version,
 scope:'Actual ENiGMA Client and exact owned GameDetails constructor/draw/lines/onKey/leave, all selected escape-sequence partitions, tab reset and listener teardown. Synthetic data and previous-menu boundary; no network/login/SQLite or physical modem claim.'}));
