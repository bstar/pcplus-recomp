'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto'),cp=require('child_process');
const root=path.resolve(__dirname,'../../../..'),candidate=fs.realpathSync(process.argv[2]),out=path.resolve(process.argv[3]);
assert(candidate.startsWith(root+'/build/')&&out.startsWith(root+'/build/'));
fs.mkdirSync(path.dirname(out),{recursive:true});fs.mkdirSync(out);fs.mkdirSync(out+'/tmp');
process.env.TMPDIR=out+'/tmp';process.env.TMP=out+'/tmp';process.env.TEMP=out+'/tmp';process.chdir(candidate);
const Owner=require(candidate+'/core/transfer_temp_owner');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const cases=[],unhandled=[];process.on('unhandledRejection',e=>unhandled.push(e));
const check=(name,yes)=>{assert(yes,name);cases.push({case:name,passed:true});};
const op=fn=>new Promise((resolve,reject)=>{
 const timer=setTimeout(()=>reject(new Error('callback deadline exceeded')),1000);
 try{fn((...args)=>{clearTimeout(timer);resolve(args);});}catch(e){clearTimeout(timer);reject(e);}
});
const create=async kind=>{const [e,o]=await op(cb=>Owner[kind==='list'?'createList':'createUpload'](cb));if(e)throw e;fs.writeFileSync(o.path+'/DATA.BIN',Buffer.from([0,26,255]));return o;};
const cleanup=o=>op(cb=>o.cleanup(cb));
async function replace(obj,key,value,fn){const old=obj[key];obj[key]=value;try{return await fn();}finally{obj[key]=old;}}
const denied=()=>Object.assign(new Error('modeled cleanup denial'),{code:'EACCES'});

async function run(){
 assert.throws(()=>new Owner(out),/Use/);check('direct-construction-is-not-authority',true);
 const forged=Object.create(Owner.prototype);check('prototype-forgery-is-not-authority',!Owner.owns(forged)&&!Owner.owns({})&&!Owner.owns(null));
 const a=await create(),b=await create();check('genuine-independent-directories',Owner.owns(a,'upload')&&a.path!==b.path);
 check('temporary-directory-is-private',(fs.statSync(a.path).mode&0o777)===0o700);
 assert.throws(()=>{a.path=out;},TypeError);check('directory-cannot-be-reassigned',a.path.startsWith(out+'/tmp/'));
 check('role-cannot-be-substituted',!Owner.owns(a,'list'));
 await cleanup(a);check('retirement-preserves-an-active-peer',!fs.existsSync(a.path)&&fs.existsSync(b.path+'/DATA.BIN'));
 let calls=0;await replace(fs,'rm',()=>{++calls;},async()=>{const [e]=await cleanup(a);check('closed-owner-completes-without-new-IO',e===null&&calls===0);});
 const c=await create(),fault=denied();
 await replace(fs,'rm',(p,o,cb)=>queueMicrotask(()=>cb(fault)),async()=>{
  const [e]=await cleanup(c);check('callback-error-is-preserved',e===fault);check('failed-retirement-retains-data-and-owner',c.state==='failed'&&fs.existsSync(c.path+'/DATA.BIN'));
 });
 const [re,results]=await op(cb=>Owner.retryFailed(cb));check('explicit-retry-retires-only-failed-owners',re===null&&results.length===1&&!fs.existsSync(c.path)&&fs.existsSync(b.path));
 const d=await create(),sync=Object.assign(new Error('modeled syscall throw'),{code:'EIO'});
 await replace(fs,'rm',()=>{throw sync;},async()=>{let returned=false;const p=op(cb=>{d.cleanup(e=>{check('sync-throw-completion-is-asynchronous',returned);cb(e);});returned=true;});const [e]=await p;check('synchronous-delete-throw-becomes-callback-error',e===sync&&d.state==='failed');});
 await cleanup(d);
 const e=await create();let rmCount=0,finish;
 await replace(fs,'rm',(p,o,cb)=>{++rmCount;finish=cb;},async()=>{
  const one=cleanup(e),two=cleanup(e);check('concurrent-callers-share-one-removal',rmCount===1&&e.state==='removing');finish(fault);finish(null);
  const rows=await Promise.all([one,two]);check('duplicate-provider-completion-does-not-change-results',rows.every(r=>r[0]===fault)&&e.state==='failed');
 });
 await cleanup(e);
 const f=await create();await replace(fs,'rm',(p,o,cb)=>cb(fault),async()=>{await cleanup(f);});
 const fresh=await create();check('new-operation-starts-failed-retirement',f.state==='removing'||f.state==='closed');await cleanup(f);check('new-operation-retries-failed-retirement',!fs.existsSync(f.path)&&fs.existsSync(fresh.path));await cleanup(fresh);
 const mkFail=Object.assign(new Error('modeled creation failure'),{code:'ENOSPC'});
 await replace(fs,'mkdtemp',(p,cb)=>cb(mkFail),async()=>{const [err,o]=await op(cb=>Owner.createUpload(cb));check('creation-error-produces-no-owner',err===mkFail&&o===undefined);});
 await replace(fs,'mkdtemp',()=>{throw mkFail;},async()=>{const [err,o]=await op(cb=>Owner.createList(cb));check('creation-throw-is-delivered-as-an-error',err===mkFail&&o===undefined);});
 const common=require(candidate+'/core/oputil/oputil_common');await op(cb=>common.initConfigAndDatabases(cb));
 const Upload=require(candidate+'/core/upload').getModule,Transfer=require(candidate+'/core/file_transfer').getModule,Selector=require(candidate+'/core/file_transfer_protocol_select').getModule,{Client}=require(candidate+'/core/client');
 async function upload(){
  const u={uploadType:'blind',availAreas:[{areaTag:'pcplus_upload'}],menuConfig:{config:{}},viewControllers:{options:{getView:()=>({getData:()=>0})}},isBlindUpload:()=>true};
  u.gotoMenu=(name,opts,cb)=>{u.forwarded=opts.extraArgs;cb(null);};
  const [err]=await op(cb=>Upload.prototype.performUpload.call(u,cb));if(err)throw err;
  fs.writeFileSync(u.tempRecvDirectory+'PART.BIN','partial');return u;
 }
 function transfer(u){
  const client=new Client(),warnings=[];client.log={warn:(o,m)=>warnings.push({object:o,message:m}),debug:()=>{},trace:()=>{},info:()=>{},error:()=>{}};
  const t=new Transfer({client,menuName:'owner-test',menuConfig:{config:{menuFlags:[]}},extraArgs:{direction:'recv',...(u?{uploadTempOwner:u.uploadTempOwner}:{})}});t.warnings=warnings;return t;
 }
 const u=await upload(),t=transfer(u),recvError=new Error('receiver exited');t.recvFiles=cb=>cb(recvError);
 await replace(fs,'rm',(p,o,cb)=>cb(fault),async()=>{
  const [err]=await op(cb=>t.recvFilesFreeOfCharge(cb));check('failed-cleanup-does-not-replace-receive-error',err===recvError);check('failed-cleanup-does-not-hold-free-time',t.client.freeTimeDepth===0);
  check('cleanup-failure-is-logged-and-data-recoverable',t.warnings.length===1&&t.warnings[0].object.code==='EACCES'&&u.uploadTempOwner.state==='failed'&&fs.existsSync(u.tempRecvDirectory+'PART.BIN'));
 });
 await op(cb=>Owner.retryFailed(cb));check('failed-upload-can-be-retired-after-repair',!fs.existsSync(u.tempRecvDirectory));
 const v=await upload();await replace(fs,'rm',(p,o,cb)=>cb(fault),async()=>{const [err]=await op(cb=>Upload.prototype.cleanupTempFiles.call(v,cb));check('details-cleanup-delivers-filesystem-error',err===fault&&fs.existsSync(v.tempRecvDirectory));});await cleanup(v.uploadTempOwner);
 const w=await upload(),thrown=transfer(w),spawnError=new Error('modeled protocol spawn throw');let recvCalls=0;thrown.recvFiles=()=>{throw spawnError;};
 assert.throws(()=>thrown.recvFilesFreeOfCharge(()=>++recvCalls),e=>e===spawnError);
 await cleanup(w.uploadTempOwner);check('legacy-spawn-throw-preserves-error-and-retires-owner',recvCalls===0&&thrown.client.freeTimeDepth===0&&!fs.existsSync(w.tempRecvDirectory));
 const success=await upload(),good=transfer(success);good.recvFiles=cb=>cb(null);await op(cb=>good.recvFilesFreeOfCharge(cb));check('successful-receive-keeps-data-for-details',fs.existsSync(success.tempRecvDirectory+'PART.BIN'));
 let forwarded;Selector.prototype.initSequence.call({recvFilePaths:['file'],config:{direction:'recv'},extraArgs:success.forwarded,gotoMenu:(n,opts)=>{forwarded=opts.lastMenuResult;}});
 check('selector-retains-genuine-owner',forwarded.uploadTempOwner===success.uploadTempOwner);
 await op(cb=>Upload.prototype.cleanupTempFiles.call({uploadTempOwner:forwarded.uploadTempOwner},cb));check('details-retire-only-their-directory',!fs.existsSync(success.tempRecvDirectory)&&fs.existsSync(b.path));
 const unowned=out+'/unowned';fs.mkdirSync(unowned);fs.writeFileSync(unowned+'/KEEP.BIN','caller data');const alien=transfer();alien.recvDirectory=unowned;alien.uploadTempOwner=forged;alien.recvFiles=cb=>cb(recvError);
 await op(cb=>alien.recvFilesFreeOfCharge(cb));check('forged-owner-cannot-delete-caller-directory',fs.readFileSync(unowned+'/KEEP.BIN','utf8')==='caller data');
 const listA=transfer(),listB=transfer();for(const m of [listA,listB])m.protocolConfig={external:{sendArgs:['sz','@{fileListPath}','{filePaths}']}};
 const [la,argsA]=await op(cb=>listA.prepAndBuildSendArgs(['ONE.ZIP','TWO ZIP.ZIP'],cb)),[lb,argsB]=await op(cb=>listB.prepAndBuildSendArgs(['OTHER.ZIP'],cb));
 const fileA=argsA[1].slice(1),fileB=argsB[1].slice(1);
 check('file-list-arguments-and-bytes-are-preserved',la===null&&lb===null&&argsA.slice(2).join('|')==='ONE.ZIP|TWO ZIP.ZIP'&&fs.readFileSync(fileA,'utf8')==='ONE.ZIP\nTWO ZIP.ZIP');
 await op(cb=>listA.cleanupTempFiles(cb));check('file-list-cleanup-preserves-another-transfer',!fs.existsSync(fileA)&&fs.existsSync(fileB)&&fs.existsSync(b.path));
 const listOwner=[...listB.fileListOwners][0];await replace(fs,'rm',(p,o,cb)=>cb(fault),async()=>{const [err]=await op(cb=>listB.cleanupTempFiles(cb));check('file-list-cleanup-error-is-delivered',err===fault&&fs.existsSync(fileB)&&listOwner.state==='failed');});
 await op(cb=>Owner.retryFailed(cb));await op(cb=>listB.cleanupTempFiles(cb));check('file-list-retirement-can-be-retried',!fs.existsSync(fileB)&&listB.fileListOwners.size===0);
 const graceful=require(candidate+'/node_modules/graceful-fs'),prep=transfer();prep.protocolConfig={external:{sendArgs:['@{fileListPath}']}};const writeError=Object.assign(new Error('modeled file-list write error'),{code:'EIO'});
 await replace(graceful,'writeFile',(p,d,cb)=>cb(writeError),async()=>{const [err]=await op(cb=>prep.prepAndBuildSendArgs(['DATA.ZIP'],cb));check('failed-list-write-preserves-error-and-retires-directory',err===writeError&&prep.fileListOwners.size===0);});
 const prepThrow=transfer();prepThrow.protocolConfig=prep.protocolConfig;
 await replace(graceful,'writeFile',()=>{throw writeError;},async()=>{const [err]=await op(cb=>prepThrow.prepAndBuildSendArgs(['DATA.ZIP'],cb));check('list-write-throw-becomes-callback-error',err===writeError&&prepThrow.fileListOwners.size===0);});
 const compound=transfer();compound.protocolConfig=prep.protocolConfig;
 await replace(graceful,'writeFile',(p,d,cb)=>cb(writeError),async()=>{await replace(fs,'rm',(p,o,cb)=>cb(fault),async()=>{const [err]=await op(cb=>compound.prepAndBuildSendArgs(['DATA.ZIP'],cb));check('compound-preparation-and-cleanup-fault-preserves-primary-error',err===writeError&&compound.fileListOwners.size===1&&[...compound.fileListOwners][0].state==='failed');});});
 await op(cb=>Owner.retryFailed(cb));await op(cb=>compound.cleanupTempFiles(cb));
 const menu=transfer(),menuOwner=await create('list');menu.fileListOwners.add(menuOwner);menu.direction='send';menu.sendQueue=[];menu.checkSendTimeRemaining=cb=>cb(null);menu.sendFiles=cb=>cb(null);let stats=0,returns=0;menu.updateSendStats=cb=>{++stats;cb(null);};
 await replace(fs,'rm',(p,o,cb)=>cb(fault),async()=>{await op(cb=>{menu.prevMenu=()=>{++returns;cb(null);};menu.initSequence();});check('cleanup-error-does-not-block-menu-return',returns===1&&stats===1&&menuOwner.state==='failed');});
 await op(cb=>Owner.retryFailed(cb));await op(cb=>menu.cleanupTempFiles(cb));await cleanup(b);
 await new Promise(resolve=>setImmediate(resolve));check('no-unhandled-rejection-from-tested-failures',unhandled.length===0);
 const exit=cp.spawnSync(process.execPath,[path.join(__dirname,'exit-probe.js'),candidate,out+'/exit'],{encoding:'utf8'});fs.writeFileSync(out+'/exit-stderr.log',exit.stderr);
 assert(exit.status===0,exit.stderr);const meta=JSON.parse(fs.readFileSync(out+'/exit/paths.json','utf8'));
 check('exit-attempts-other-owners-after-one-removal-fails',fs.existsSync(meta.failed)&&!fs.existsSync(meta.healthy)&&exit.stderr.includes('EACCES'));
 const result={passed:true,cases,checker_sha256:hash(__filename),exit_probe_sha256:hash(path.join(__dirname,'exit-probe.js')),
  core:Object.fromEntries(['upload.js','file_transfer.js','file_transfer_protocol_select.js','transfer_temp_owner.js'].map(n=>['core/'+n,hash(candidate+'/core/'+n)])),
  provider_faults_modeled:['rm callback EACCES','rm synchronous EIO throw','rm duplicate callback','mkdtemp callback/throw ENOSPC','file-list write callback/throw EIO','exit rmSync EACCES'],
  scope:'Actual helper/module methods, private real filesystem data and isolated modeled filesystem error boundaries. Menu control flow is actual; protocol execution is stubbed in that unit. Separate DOS/network acceptance remains required.'};
 fs.writeFileSync(out+'/checks.json',JSON.stringify(result,null,2)+'\n');console.log('Transfer owners:',cases.length,'checks passed');
}
run().then(()=>process.exit(0)).catch(e=>{console.error(e);process.exit(1);});
