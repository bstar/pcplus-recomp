'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const root=path.resolve(__dirname,'../../../..'),candidate=fs.realpathSync(process.argv[2]),samples=fs.realpathSync(process.argv[3]),out=path.resolve(process.argv[4]);
assert(candidate.startsWith(root+'/build/')&&samples.startsWith(root+'/build/')&&out.startsWith(root+'/build/'));
fs.mkdirSync(out);const {validSave,openSave,SnapshotRead}=require(candidate+'/core/zmachine_door/save_read');
const meta=JSON.parse(fs.readFileSync(candidate+'/infocom-save-instance.json'));
const story=fs.readFileSync(candidate+'/'+Object.keys(meta.fixture_inputs).find(n=>n.startsWith('local/infocom/')));
const north=fs.readFileSync(samples+'/north.glksave'),west=fs.readFileSync(samples+'/west.glksave');
const cases=[],check=(name,ok)=>{assert(ok,name);cases.push({case:name,passed:true});};
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
function chunks(data){const result=[];for(let at=12;at<data.length;){const size=data.readUInt32BE(at+4);result.push([data.toString('latin1',at,at+4),Buffer.from(data.subarray(at+8,at+8+size))]);at+=8+size+(size&1);}return result;}
function encode(entries){const parts=entries.map(([name,data])=>{const header=Buffer.alloc(8);header.write(name,0,4,'latin1');header.writeUInt32BE(data.length,4);return Buffer.concat([header,data,...(data.length&1?[Buffer.alloc(1)]:[])]);});const header=Buffer.from('FORM\0\0\0\0IFZS','latin1');const result=Buffer.concat([header,...parts]);result.writeUInt32BE(result.length-8,4);return result;}
const original=chunks(west);
function altered(type,fn){return encode(original.map(([name,data])=>[name,name===type?fn(Buffer.from(data)):data]));}
function reject(name,data,source=story,limit=100000){check(name,!validSave(data,source,limit));}
check('two-real-worker-saves-accepted',validSave(north,story,100000)&&validSave(west,story,100000)&&!north.equals(west));
reject('empty',Buffer.alloc(0));reject('non-IFF',Buffer.from('not a save'));reject('truncated',west.subarray(0,-1));
let changed=Buffer.from(west);changed.writeUInt32BE(0,4);reject('wrong-IFF-extent',changed);
changed=Buffer.from(west);changed[0]|=128;reject('high-bit-FourCC-alias',changed);
changed=Buffer.from(west);changed.write('IFRS',8);reject('wrong-container-type',changed);
for(const name of ['IFhd','CMem','Stks'])reject('missing-'+name,encode(original.filter(([type])=>type!==name)));
for(const name of ['IFhd','CMem','Stks'])reject('duplicate-'+name,encode([...original,original.find(([type])=>type===name)]));
reject('short-identity',altered('IFhd',data=>data.subarray(0,12)));
for(const [offset,name] of [[0,'release'],[2,'serial'],[8,'checksum']])reject('wrong-story-'+name,altered('IFhd',data=>{data[offset]^=1;return data;}));
reject('PC-outside-story',altered('IFhd',data=>{data.writeUIntBE(story.length,10,3);return data;}));
reject('both-memory-representations',encode([...original,['UMem',Buffer.alloc(story.readUInt16BE(14))]]));
reject('trailing-compressed-zero',altered('CMem',()=>Buffer.from([0])));
reject('compressed-memory-overflow',altered('CMem',()=>Buffer.alloc(story.readUInt16BE(14)+1,1)));
reject('short-uncompressed-memory',encode(original.map(([name,data])=>[name==='CMem'?'UMem':name,name==='CMem'?Buffer.alloc(1):data])));
reject('empty-stack',altered('Stks',()=>Buffer.alloc(0)));
reject('truncated-frame-header',altered('Stks',()=>Buffer.alloc(7)));
reject('truncated-frame-locals',altered('Stks',()=>{const data=Buffer.alloc(8);data[3]=15;return data;}));
reject('truncated-evaluation-stack',altered('Stks',()=>{const data=Buffer.alloc(8);data.writeUInt16BE(1,6);return data;}));
reject('reserved-frame-flags',altered('Stks',data=>{data[3]|=128;return data;}));
reject('return-PC-outside-story',altered('Stks',data=>{data.writeUIntBE(story.length,0,3);return data;}));
reject('VM-stack-capacity',west,story,8);reject('invalid-stack-limit',west,story,NaN);
const maximum=encode([...original,['ANNO',Buffer.alloc(128*1024-west.length-8)]]);
check('exact-128KiB-valid-file',maximum.length===128*1024&&validSave(maximum,story,100000));
reject('over-128KiB-limit',encode([...original,['ANNO',Buffer.alloc(128*1024-west.length-6)]]));
const good=out+'/good.glksave';fs.writeFileSync(good,west);
const stream=openSave(good,story,100000);fs.writeFileSync(good,'replaced');
const target=Buffer.alloc(west.length+10);check('immutable-snapshot-after-overwrite',stream.fread(target)===west.length&&target.subarray(0,west.length).equals(west));
stream.fseek(0,0);const first=Buffer.alloc(4);check('snapshot-start-seek',stream.fread(first)===4&&first.toString()==='FORM'&&stream.ftell()===4);
stream.fseek(-2,1);check('snapshot-relative-seek',stream.ftell()===2);
stream.fseek(-2,2);check('snapshot-end-seek',stream.fread(first)===2&&stream.ftell()===west.length);
stream.fseek(west.length+5,0);check('read-beyond-EOF',stream.fread(first)===0);
stream.fseek(-100000,0);check('negative-seek-clamps',stream.ftell()===0);stream.fclose();stream.fclose();check('closed-read-is-EOF',stream.fread(first)===0);
check('immutable-input-copy',(()=>{const source=Buffer.from('TEST'),read=new SnapshotRead(source);source.fill(0);const data=Buffer.alloc(4);read.fread(data);return data.toString()==='TEST';})());
fs.writeFileSync(good,west);fs.symlinkSync(good,out+'/link');
for(const [name,file] of [['missing',out+'/missing'],['directory',out],['symlink',out+'/link']]){assert.throws(()=>openSave(file,story,100000));check('reject-'+name,true);}
fs.writeFileSync(out+'/large',Buffer.alloc(128*1024+1));assert.throws(()=>openSave(out+'/large',story,100000));check('bounded-file-read',true);
let fd;const oldRead=fs.readSync;
try{fs.readSync=(value)=>{fd=value;throw Object.assign(new Error('modeled read failure'),{code:'EIO'});};assert.throws(()=>openSave(good,story,100000),e=>e.code==='EIO');}finally{fs.readSync=oldRead;}
assert.throws(()=>fs.fstatSync(fd),e=>e.code==='EBADF');check('modeled-read-error-closes-FD',true);
try{fs.readSync=(value)=>{fd=value;return 0;};assert.throws(()=>openSave(good,story,100000),/Incomplete/);}finally{fs.readSync=oldRead;}
assert.throws(()=>fs.fstatSync(fd),e=>e.code==='EBADF');check('modeled-short-read-closes-FD',true);
const Dialog=require(candidate+'/core/zmachine_door/save_dialog').createSaveDialog(out+'/dialog');
let output='';const dialog=new Dialog({stdout:{write:text=>{output+=text;}},rl:{},saveStory:story,saveStackLimit:()=>100000});
const ref={filename:out+'/dialog/bad.glksave',usage:'save'};fs.writeFileSync(ref.filename,'not a save');
check('actual-dialog-rejects-malformed-file',dialog.file_fopen(2,ref)===null&&output.includes('Cannot restore this save file.'));
ref.filename=out+'/dialog/write.glksave';const writer=dialog.file_fopen(1,ref);writer.fwrite(Buffer.from('unchanged write path'));writer.fclose();
check('actual-dialog-keeps-upstream-write-path',fs.readFileSync(ref.filename,'utf8')==='unchanged write path');
fs.writeFileSync(ref.filename,west);const reader=dialog.file_fopen(2,ref);const read=Buffer.alloc(west.length);check('actual-dialog-restores-valid-read',reader.fread(read)===west.length&&read.equals(west));reader.fclose();
fs.writeFileSync(out+'/checks.json',JSON.stringify({passed:true,cases,checker_sha256:hash(__filename),
 source_hashes:Object.fromEntries(['save_read.js','save_dialog.js','zmachine_worker.js'].map(n=>['core/zmachine_door/'+n,hash(candidate+'/core/zmachine_door/'+n)])),
 samples:{north:hash(samples+'/north.glksave'),west:hash(samples+'/west.glksave')},
 modeled_boundaries:['fs.readSync EIO','fs.readSync unexpected EOF'],
 scope:'Actual validator/read snapshot/dialog and real private filesystem. Two read-provider errors are modeled. Not a DOS, BBS, semantic-state or multiworker save-write acceptance claim.'},null,2)+'\n');
console.log('Save-read checks:',cases.length,'passed');
