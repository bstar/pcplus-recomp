'use strict';
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const {atomicImageWrite,flushImage}=require('./image_flush');
const root=path.resolve(__dirname,'../../../..');
const folder=path.join(root,'build/bbs-lab','image-flush-components-'+process.pid);
fs.mkdirSync(folder,{recursive:true});
const checks=[];
async function check(name,test){await test();checks.push(name);}
function fixture(name){
    const directory=path.join(folder,name);fs.mkdirSync(directory);
    const file=path.join(directory,'disk.img'),old=Buffer.alloc(512,0x13),fresh=Buffer.alloc(512,0x37);
    fs.writeFileSync(file,old);return{directory,file,old,fresh};
}
function ioWith(changes){return new Proxy(fs,{get(target,key){return key in changes?changes[key]:target[key];}});}
function failure(code){return Object.assign(Error('modeled '+code),{code});}
const pending=f=>fs.readdirSync(f.directory).filter(n=>n.includes('.pending-'));
(async()=>{
    await check('atomic-success-and-no-temp',()=>{const f=fixture('success');atomicImageWrite(f.file,f.fresh);assert.deepEqual(fs.readFileSync(f.file),f.fresh);assert.deepEqual(pending(f),[]);});
    await check('existing-permissions-preserved',()=>{const f=fixture('mode');fs.chmodSync(f.file,0o640);const mask=process.umask(0o077);try{atomicImageWrite(f.file,f.fresh);}finally{process.umask(mask);}assert.equal(fs.statSync(f.file).mode&0o777,0o640);});
    await check('symlink-target-updated-with-link-preserved',()=>{const f=fixture('link');const link=path.join(f.directory,'link.img');fs.symlinkSync(f.file,link);atomicImageWrite(link,f.fresh);assert(fs.lstatSync(link).isSymbolicLink());assert.deepEqual(fs.readFileSync(f.file),f.fresh);});
    for(const stage of ['open','chmod','write-partial','fsync-file','close-file','rename']){
        await check(stage+'-failure-preserves-prior-image',()=>{
            const f=fixture(stage);let first=true;
            const hooks={};
            if(stage==='open')hooks.openSync=(...a)=>{if(a[0].includes('.pending-'))throw failure('EACCES');return fs.openSync(...a);};
            if(stage==='chmod')hooks.fchmodSync=()=>{throw failure('EPERM');};
            if(stage==='write-partial')hooks.writeFileSync=(fd,data)=>{fs.writeSync(fd,data.subarray(0,64));throw failure('ENOSPC');};
            if(stage==='fsync-file')hooks.fsyncSync=()=>{throw failure('EIO');};
            if(stage==='close-file')hooks.closeSync=fd=>{if(first){first=false;throw failure('EIO');}return fs.closeSync(fd);};
            if(stage==='rename')hooks.renameSync=()=>{throw failure('EACCES');};
            let error;try{atomicImageWrite(f.file,f.fresh,ioWith(hooks));}catch(e){error=e;}
            assert(error);assert.equal(error.imageCommitted,false);assert.deepEqual(fs.readFileSync(f.file),f.old);assert.deepEqual(pending(f),[]);
        });
    }
    await check('directory-sync-failure-reports-committed-image',()=>{const f=fixture('dir-sync');let count=0;const io=ioWith({fsyncSync:fd=>{if(++count===2)throw failure('EIO');return fs.fsyncSync(fd);}});assert.throws(()=>atomicImageWrite(f.file,f.fresh,io),e=>e.imageCommitted===true);assert.deepEqual(fs.readFileSync(f.file),f.fresh);assert.deepEqual(pending(f),[]);});
    await check('cleanup-error-retains-actionable-path',()=>{const f=fixture('cleanup');const io=ioWith({writeFileSync:()=>{throw failure('ENOSPC');},unlinkSync:()=>{throw failure('EACCES');}});let error;try{atomicImageWrite(f.file,f.fresh,io);}catch(e){error=e;}assert(error.temporaryPath);assert(error.message.includes(error.temporaryPath));assert.deepEqual(fs.readFileSync(f.file),f.old);assert.equal(pending(f).length,1);});
    await check('missing-registry-is-resolved-noop',async()=>{await flushImage(undefined,'absent');});
    await check('returned-promise-is-actual-queue',async()=>{const f=fixture('promise');const entry={sab:new SharedArrayBuffer(512),flushQueue:Promise.resolve()};new Uint8Array(entry.sab).set(f.fresh);const result=flushImage(entry,f.file);assert.equal(result,entry.flushQueue);await result;assert.deepEqual(fs.readFileSync(f.file),f.fresh);});
    await check('failed-attempt-does-not-poison-retry',async()=>{const f=fixture('retry');const entry={sab:new SharedArrayBuffer(512),flushQueue:Promise.resolve()};new Uint8Array(entry.sab).set(f.fresh);const absent=path.join(f.directory,'not-created.img');await assert.rejects(flushImage(entry,absent));await flushImage(entry,f.file);assert.deepEqual(fs.readFileSync(f.file),f.fresh);});
    await check('queued-attempts-settle-in-order',async()=>{const f=fixture('serial');const entry={sab:new SharedArrayBuffer(512),flushQueue:Promise.resolve()};new Uint8Array(entry.sab).set(f.fresh);const order=[];const a=flushImage(entry,f.file).then(()=>order.push(1));const b=flushImage(entry,f.file).then(()=>order.push(2));await Promise.all([a,b]);assert.deepEqual(order,[1,2]);assert.deepEqual(pending(f),[]);});
    console.log(JSON.stringify({passed:true,count:checks.length,checks,scope:'Real temporary files plus explicitly modeled syscall failures; no live images or power-loss acceptance.'}));
})().catch(e=>{console.error(e);process.exitCode=1;});
