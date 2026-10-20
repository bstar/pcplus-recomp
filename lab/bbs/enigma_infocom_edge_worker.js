'use strict';
// Actual owned VM worker and filesystem, without a BBS or DOS assertion.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{Worker}=require('worker_threads');
const root=path.resolve(__dirname,'../..'),candidate=fs.realpathSync(process.argv[2]),out=path.resolve(process.argv[3]);
const repo=path.resolve(__dirname,'../..');
if(!candidate.startsWith(repo+'/build/')||!out.startsWith(repo+'/build/'))throw new Error('Owned build paths required');
fs.mkdirSync(out,{recursive:false});fs.mkdirSync(out+'/saves');
const meta=JSON.parse(fs.readFileSync(candidate+'/infocom-save-instance.json'));
const story=Object.keys(meta.fixture_inputs).find(p=>p.startsWith('local/infocom/'));
const worker=new Worker(candidate+'/core/zmachine_door/zmachine_worker.js',{
 workerData:{gamePath:candidate+'/'+story,saveDirectory:out+'/saves',preloadedAutosave:null}});
let output='',line=0,terminal=false;const messages=[],errors=[],steps=[];
worker.on('message',message=>{messages.push(message);if(message.type==='output')output+=message.data;if(message.type==='input_mode'&&message.mode==='line')++line;if(message.type==='error')errors.push(message.message);});
worker.on('error',e=>{errors.push(e.message);terminal=true;});worker.on('exit',code=>{messages.push({type:'exit',code});terminal=true;});
const clean=s=>s.replace(/\x1b\[[0-?]*[ -/]*[@-~]/g,'');
async function wait(predicate,name){const until=Date.now()+5000;while(Date.now()<until){if(predicate())return;if(terminal)throw new Error('Worker ended while waiting for '+name);await new Promise(r=>setTimeout(r,10));}throw new Error('Deadline: '+name);}
function input(text){steps.push({input:text});worker.postMessage({type:'input',data:text+'\n'});}
async function command(text){const before=line;input(text);await wait(()=>line>before,'line input after '+text);}
async function dialog(commandName,answer){const before=output.length;input(commandName);await wait(()=>clean(output.slice(before)).includes(commandName==='save'?'Save name [save]':'Restore name [save]'),'dialog');const count=line;input(answer);await wait(()=>line>count,'dialog completion');}
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function run(){
 await wait(()=>line>0,'initial game');
 await dialog('save','CANCEL');steps.push({cancel_created_files:fs.readdirSync(out+'/saves').length});
 const at=output.length;input('save');await wait(()=>clean(output.slice(at)).includes('Save name [save]'),'save dialog');
 const invalidAt=output.length;input('../outside');await wait(()=>clean(output.slice(invalidAt)).includes('Use letters, numbers'),'invalid-name rejection');
 let before=line;input('CANCEL');await wait(()=>line>before,'invalid-name cancellation');
 await dialog('restore','missing');await command('look');
 await command('north');await dialog('save','locprobe');fs.copyFileSync(out+'/saves/locprobe.glksave',out+'/north.glksave');
 input('restart');await new Promise(r=>setTimeout(r,100));before=line;input('y');await wait(()=>line>before,'restart');
 await dialog('save','locprobe');fs.copyFileSync(out+'/saves/locprobe.glksave',out+'/west.glksave');
 await command('north');await dialog('restore','locprobe');await command('look');
 fs.writeFileSync(out+'/saves/broken.glksave',Buffer.from('not a Quetzal save\n'));
 const badAt=output.length;input('restore');await wait(()=>clean(output.slice(badAt)).includes('Restore name [save]'),'corrupt restore dialog');
 before=line;input('broken');
 const until=Date.now()+2000;while(Date.now()<until&&!terminal&&line===before)await new Promise(r=>setTimeout(r,10));
 const survived=!terminal&&line>before&&errors.length===0;
 if(survived)await command('look');
 const result={completed_control_paths:true,corrupt_restore_survived:survived,errors,
  overwrite_changed_save:hash(out+'/north.glksave')!==hash(out+'/west.glksave'),
  source_hashes:Object.fromEntries(['zmachine_worker.js','save_dialog.js'].map(n=>['core/zmachine_door/'+n,hash(candidate+'/core/zmachine_door/'+n)])),
  runner_sha256:hash(__filename),scope:'Actual isolated owned worker, story and save files; no live board, BBS connection or DOS claim.'};
 fs.writeFileSync(out+'/checks.json',JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify(result,null,2));
}
run().catch(e=>{fs.writeFileSync(out+'/failure.txt',String(e.stack));process.exitCode=1;}).finally(async()=>{
 fs.writeFileSync(out+'/output.txt',output);fs.writeFileSync(out+'/events.json',JSON.stringify({steps,messages},null,2)+'\n');await worker.terminate();
});
