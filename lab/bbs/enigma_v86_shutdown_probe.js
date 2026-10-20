'use strict';
// Real owned door, isolated IPC, v86, FreeDOS and disk. Only the BBS client,
// Config and logger are synthetic; no socket or live board is started.
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const {EventEmitter} = require('events');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, word, i, all) => {
    if (i % 2 === 0) pairs.push([word.replace(/^--/, ''), all[i+1]]);
    return pairs;
}, []));
const candidate = path.resolve(args.candidate), sourceImage = path.resolve(args.image);
assert(candidate.startsWith(root + '/build/'));
assert(/^[A-Za-z0-9_-]+$/.test(args.label));
assert(['baseline','fixed'].includes(args.expect));
assert(!args['flush-fault'] || args['flush-fault']==='partial');
assert(!args['flush-fault'] || args.expect==='fixed');
const out = path.join(root,'build/bbs-lab/results/enigma',args.label);
fs.mkdirSync(out);
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const meta = JSON.parse(fs.readFileSync(path.join(candidate,'v86-door-instance.json')));
const inputs = {runner: __filename, image: sourceImage};
for (const [name,digest] of Object.entries(meta.fixture_inputs)) {
    const file = path.join(candidate,name); assert.equal(sha(file),digest); inputs['candidate/'+name]=file;
}
for (const [name,digest] of Object.entries(meta.dependency_inputs)) {
    const file=path.join(candidate,'node_modules',name); assert.equal(sha(file),digest); inputs['dependency/'+name]=file;
}
const before=Object.fromEntries(Object.entries(inputs).map(([name,file])=>[name,sha(file)]));
const image=path.join(out,'probe.img');
fs.copyFileSync(sourceImage,image,fs.constants.COPYFILE_EXCL);
const initialDisk=sha(image);
let faultFired=false;
if(args['flush-fault']==='partial'){
    const writeFileSync=fs.writeFileSync;
    fs.writeFileSync=function(file,data,...options){
        if(!faultFired&&typeof file==='number'&&fs.readlinkSync('/proc/self/fd/'+file).startsWith(image+'.pending-')){
            faultFired=true;
            fs.writeSync(file,data.subarray(0,4096));
            throw Object.assign(Error('modeled ENOSPC after partial temporary image write'),{code:'ENOSPC'});
        }
        return writeFileSync.call(fs,file,data,...options);
    };
}
const marker='LOC_DISK_' + args.label.toUpperCase();
assert(!fs.readFileSync(image).includes(Buffer.from(marker)));
require(path.join(candidate,'core/config.js')).get=()=>({debug:{assertsEnabled:false},menus:{cls:false},general:{boardName:'Disk Probe'}});
const logs=[], events=[], started=Date.now();
const log={};
for(const level of ['info','warn','error','debug','trace'])log[level]=(a,b)=>logs.push({level,ms:Date.now()-started,...(typeof a==='object'?a:{}),msg:b||a});
log.child=()=>log;
require(path.join(candidate,'core/logger.js')).log=log;
const isolated=require(path.join(candidate,'core/v86_door/isolated_worker.js')).IsolatedWorker;
const originalEmit=isolated.prototype.emit;
const identities=new WeakMap();let nextIdentity=0;
isolated.prototype.emit=function(event,...values){
    if(!identities.has(this))identities.set(this,++nextIdentity);
    if(event==='exit'||event==='error'||event==='message'&&values[0].type!=='output') {
        events.push({id:identities.get(this),event,ms:Date.now()-started,
            value:event==='message'?{...values[0],data:undefined}:String(values[0]),
            parent_has_marker:Buffer.from(this.imageSab).includes(Buffer.from(marker)),
            disk_has_marker:fs.readFileSync(image).includes(Buffer.from(marker))});
    }
    return originalEmit.call(this,event,...values);
};
const ownedDoor=require(path.join(candidate,'core/v86_door/v86_door.js'));
const wait=async(predicate,label,seconds=30)=>{
    const end=Date.now()+seconds*1000;
    while(Date.now()<end){if(predicate())return;await new Promise(r=>setTimeout(r,10));}
    throw Error('Timed out: '+label);
};
async function runDoor(batch, overflow, number){
    const client=new EventEmitter();client.node=1;client.user={userId:99999,properties:{}};client.log=log;
    let received=Buffer.alloc(0), returns=0, returnMs=null;
    client.term={output:new EventEmitter(),write:data=>{received=Buffer.concat([received,Buffer.from(data)]);},
        rawWrite:data=>{received=Buffer.concat([received,Buffer.from(data)]);}};
    const door=new ownedDoor.getModule({client,menuName:'diskProbe',menuConfig:{config:{
        name:'DiskProbe',image,nodeMax:1,isolateProcess:true,memoryMb:32,
        biosPath:path.join(candidate,'misc/v86_bios/seabios.bin'),
        vgaBiosPath:path.join(candidate,'misc/v86_bios/vgabios.bin'),runBatch:batch}}});
    door.prevMenu=()=>{returns++;returnMs=Date.now()-started;};
    door.initSequence();
    if(overflow){
        await wait(()=>received.includes(Buffer.from('LOC_DISK_READY')),'guest closed file and reached ready');
        client.term.output.emit('data',Buffer.alloc(65537,120));
    }
    await wait(()=>returns>0,'menu callback');
    await wait(()=>events.some(e=>e.id===number&&e.event==='exit'),'isolated process exit');
    let flushFailure=null;
    try { await ownedDoor._test.imageRegistry.get(image).flushQueue; } catch(error) {
        if(!args['flush-fault']||number!==1)throw error;
        flushFailure=error.message;
    }
    fs.writeFileSync(path.join(out,'serial-'+number+'.bin'),received);
    return {returns,return_ms:returnMs,flush_failure:flushFailure,input_listeners:client.term.output.listenerCount('data'),
        end_listeners:client.listenerCount('end'),slot_released:door._instanceIncremented===false,
        marker_in_serial:received.includes(Buffer.from(marker)),
        marker_in_disk:fs.readFileSync(image).includes(Buffer.from(marker))};
}
(async()=>{
    const first=await runDoor('@ECHO OFF\nECHO '+marker+'>C:\\ERRCHK.TXT\nECHO LOC_DISK_READY>COM1\n:WAIT\nGOTO WAIT\n',true,1);
    const firstEvents=events.filter(e=>e.id===1);
    const stopped=firstEvents.find(e=>e.event==='message'&&e.value.type==='stopped');
    assert(stopped,'actual updated disk returned by isolated child');
    const diskAfterFirst=sha(image);
    const temporaryFiles=fs.readdirSync(out).filter(name=>name.includes('.pending-'));
    if(args['flush-fault'])await ownedDoor._test.flushSabToDisk(image);
    ownedDoor._test.imageRegistry.delete(image); // emulate a cold host image load
    const second=await runDoor('@ECHO OFF\nTYPE C:\\ERRCHK.TXT>COM1\nECHO LOC_READBACK_DONE>COM1\n',false,2);
    const counterexample=args.expect==='baseline';
    const checks={first_callback_once:first.returns===1,second_callback_once:second.returns===1,
        both_slots_released:first.slot_released&&second.slot_released,
        listeners_removed:first.input_listeners===0&&first.end_listeners===0&&second.input_listeners===0&&second.end_listeners===0,
        child_returned_guest_write:stopped.parent_has_marker,
        expected_disk_result:first.marker_in_disk===(!counterexample&&!args['flush-fault']),
        expected_cold_guest_readback:second.marker_in_serial===!counterexample,
        expected_completion_order:counterexample?first.return_ms<stopped.ms:first.return_ms>=stopped.ms,
        inputs_unchanged:Object.entries(inputs).every(([name,file])=>sha(file)===before[name])};
    if(args['flush-fault'])Object.assign(checks,{
        partial_write_fault_observed:faultFired,
        previous_complete_image_preserved:diskAfterFirst===initialDisk,
        failed_temporary_image_removed:temporaryFiles.length===0,
        failure_reported:logs.some(row=>row.msg==='v86 image flush failed'&&row.imageCommitted===false&&row.error.includes('modeled ENOSPC')),
        retry_persisted_retained_guest_write:fs.readFileSync(image).includes(Buffer.from(marker)),
    });
    const result={passed:Object.values(checks).every(Boolean),classification:counterexample?'verified data-loss counterexample':'controlled input-error disk acceptance',checks,
        marker,first,second,modeled_flush_fault:args['flush-fault']||null,initial_disk_sha256:initialDisk,
        disk_after_first_sha256:diskAfterFirst,events,logs,input_hashes:before,
        scope:'Actual owned door/isolated IPC/v86/FreeDOS file write and cold guest readback; synthetic client, Config and logger; one deliberate 65537-byte input. No live BBS, live image, physical modem or abrupt process-crash claim.'};
    fs.writeFileSync(path.join(out,'shutdown-checks.json'),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify({passed:result.passed,classification:result.classification,checks},null,2));
    process.exitCode=result.passed?0:1;
})().catch(error=>{fs.writeFileSync(path.join(out,'failure.txt'),error.stack+'\n');console.error(error);process.exit(1);});
