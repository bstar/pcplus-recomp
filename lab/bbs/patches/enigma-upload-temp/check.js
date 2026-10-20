'use strict';
// Actual module methods and real temporary files; no socket/protocol emulation.
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const root=path.resolve(__dirname,'../../../..');
const candidate=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
const fixed=process.argv.includes('--fixed');
assert(candidate.startsWith(root+'/build/')&&out.startsWith(root+'/build/'));
fs.mkdirSync(path.dirname(out),{recursive:true});fs.mkdirSync(out);
const temporary=path.join(out,'tmp');fs.mkdirSync(temporary);
process.env.TMPDIR=temporary;process.env.TMP=temporary;process.env.TEMP=temporary;
process.chdir(candidate);
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const common=require(candidate+'/core/oputil/oputil_common');
common.initConfigAndDatabases(async err=>{
 if(err)throw err;
 const Upload=require(candidate+'/core/upload').getModule;
 const Transfer=require(candidate+'/core/file_transfer').getModule;
 const Selector=require(candidate+'/core/file_transfer_protocol_select').getModule;
 const {Client}=require(candidate+'/core/client');
 const Session=require(candidate+'/node_modules/temptmp');
 const cases=[];
 const check=(name,value)=>{assert(value,name);cases.push({case:name,passed:true});};
 const upload=async()=>{
  const owner={uploadType:'blind',availAreas:[{areaTag:'pcplus_upload'}],menuConfig:{config:{}},
   viewControllers:{options:{getView:()=>({getData:()=>0})}},isBlindUpload:()=>true};
  owner.gotoMenu=(name,opts,cb)=>{owner.forwarded=opts.extraArgs;cb(null);};
  await new Promise((resolve,reject)=>Upload.prototype.performUpload.call(owner,e=>e?reject(e):resolve()));
  owner.file=path.join(owner.tempRecvDirectory,'PART.BIN');fs.writeFileSync(owner.file,Buffer.from([0,26,255,1]));
  return owner;
 };
 const transfer=owner=>new Transfer({client:new Client(),menuName:'owned-temp-test',menuConfig:{config:{menuFlags:[]}},
  extraArgs:{direction:'recv',...(owner?{uploadTempSession:owner.uploadTempSession}:{})}});
 const receive=(mod,error)=>{
  mod.recvFiles=cb=>setImmediate(()=>cb(error));
  return new Promise(resolve=>mod.recvFilesFreeOfCharge(resolve));
 };
 try {
  const a=await upload(),b=await upload();
  if(!fixed){
   Upload.prototype.cleanupTempFiles.call(a);
   await new Promise((resolve,reject)=>{
    const deadline=Date.now()+2000;
    const poll=()=>!fs.existsSync(a.file)?resolve():Date.now()>deadline?reject(new Error('cleanup did not finish')):setTimeout(poll,5);poll();
   });
   check('original-shared-upload-session-removes-both-owners',!fs.existsSync(a.file)&&!fs.existsSync(b.file));
  } else {
   check('each-upload-has-unique-tracked-owner',a.uploadTempSession instanceof Session&&b.uploadTempSession instanceof Session&&a.uploadTempSession.sessionId!==b.uploadTempSession.sessionId);
   check('creator-forwards-owner-to-protocol',a.forwarded.uploadTempSession===a.uploadTempSession);
   await new Promise(resolve=>Upload.prototype.cleanupTempFiles.call(a,resolve));
   check('success-cleanup-removes-only-its-own-data',!fs.existsSync(a.file)&&fs.readFileSync(b.file).equals(Buffer.from([0,26,255,1])));
   await new Promise(resolve=>Upload.prototype.cleanupTempFiles.call(a,resolve));
   check('repeated-cleanup-preserves-another-upload',fs.existsSync(b.file));
   const c=await upload(),bad=transfer(c),failure=new Error('receiver failed');
   check('transfer-retains-the-creator-owner',bad.uploadTempSession===c.uploadTempSession);
   check('failure-identity-preserved',await receive(bad,failure)===failure);
   check('failure-removes-partial-before-callback',!fs.existsSync(c.file)&&fs.existsSync(b.file));
   check('failed-upload-releases-free-time',bad.client.freeTimeDepth===0);
   const d=await upload(),good=transfer(d);
   check('successful-receive-keeps-data-for-details',await receive(good,null)===null&&fs.existsSync(d.file));
   let result;
   Selector.prototype.initSequence.call({recvFilePaths:[d.file],config:{direction:'recv'},extraArgs:d.forwarded,
    gotoMenu:(name,opts)=>{result=opts.lastMenuResult;}});
   check('selector-preserves-the-creator-owner',result.uploadTempSession===d.uploadTempSession);
   await new Promise(resolve=>Upload.prototype.cleanupTempFiles.call({uploadTempSession:result.uploadTempSession},resolve));
   check('details-cleanup-retires-only-that-owner',!fs.existsSync(d.file)&&fs.existsSync(b.file));
   const unowned=path.join(out,'unowned');fs.mkdirSync(unowned);const keep=path.join(unowned,'KEEP.BIN');fs.writeFileSync(keep,'caller data');
   const foreign=transfer();foreign.recvDirectory=unowned;
   await receive(foreign,failure);check('caller-owned-directory-is-not-removed',fs.readFileSync(keep,'utf8')==='caller data');
   foreign.uploadTempSession={cleanup:()=>{throw new Error('untyped cleanup must not run');}};
   await receive(foreign,failure);check('untyped-owner-is-not-a-cleanup-authority',fs.existsSync(keep));
   await new Promise(resolve=>Upload.prototype.cleanupTempFiles.call(b,resolve));
   check('final-owner-cleaned-independently',!fs.existsSync(b.file));
  }
  const report={passed:true,fixed,cases,checker_sha256:hash(__filename),
   core:Object.fromEntries(['upload.js','file_transfer.js','file_transfer_protocol_select.js'].map(n=>['core/'+n,hash(candidate+'/core/'+n)])),
   temptmp_sha256:hash(candidate+'/node_modules/temptmp/index.js'),package_lock_sha256:hash(candidate+'/package-lock.json'),
   scope:'Actual owned module methods and real isolated temporary files. Baseline exposes shared cleanup; fixed checks per-upload ownership, error/success, forwarding and foreign-directory preservation. No DOS/network/concurrent-client acceptance claim.'};
  fs.writeFileSync(path.join(out,'checks.json'),JSON.stringify(report,null,2)+'\n');
  console.log((fixed?'Fixed':'Baseline')+' upload temporary ownership: '+cases.length+' checks');
  process.exit(0);
 } catch(e){console.error(e);process.exit(1);}
});
