'use strict';
// Model a rejected deletion provider in one process; use real owned temp data.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const root=path.resolve(__dirname,'../../../..');
const candidate=fs.realpathSync(process.argv[2]),out=path.resolve(process.argv[3]);
assert(candidate.startsWith(root+'/build/')&&out.startsWith(root+'/build/'));
fs.mkdirSync(path.dirname(out),{recursive:true});fs.mkdirSync(out);fs.mkdirSync(out+'/tmp');
process.env.TMPDIR=out+'/tmp';process.env.TMP=out+'/tmp';process.env.TEMP=out+'/tmp';
const delPath=require.resolve('del',{paths:[candidate]});const original=require(delPath);
const fault=Object.assign(new Error('modeled cleanup denial'),{code:'EACCES'});
const rejected=()=>Promise.reject(fault);rejected.sync=original.sync;
require.cache[delPath].exports=rejected;
const Session=require(candidate+'/node_modules/temptmp');
const Transfer=require(candidate+'/core/file_transfer').getModule;
const owner=Session.createTrackedSession('owned-rejection-probe');
let rejection=null;process.on('unhandledRejection',err=>{rejection=err;});
owner.mkdir({prefix:'probe-'},(err,dir)=>{
 if(err)throw err;const file=path.join(dir,'PART.BIN');fs.writeFileSync(file,Buffer.from([0,26,255]));
 let depth=0,calls=0;const receiveError=new Error('receiver failed');
 const fake={client:{beginFreeTime:()=>++depth,endFreeTime:()=>--depth},uploadTempSession:owner,recvFiles:cb=>cb(receiveError)};
 Transfer.prototype.recvFilesFreeOfCharge.call(fake,()=>{++calls;});
 setTimeout(()=>{
  assert(calls===0&&depth===0&&rejection===fault&&fs.existsSync(file));
  const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
  const result={reproduced:true,completion_callbacks:calls,free_time_depth:depth,unhandled_rejection_code:rejection.code,partial_retained:true,
   checker_sha256:hash(__filename),transfer_sha256:hash(candidate+'/core/file_transfer.js'),temptmp_sha256:hash(candidate+'/node_modules/temptmp/index.js'),
   scope:'Actual staged-v1 receive/cleanup wrapper and tracked-session dependency. Rejected deletion provider is modeled; temporary files are real. No live board or DOS session claim.'};
  fs.writeFileSync(out+'/checks.json',JSON.stringify(result,null,2)+'\n');
  console.log('Reproduced: cleanup callback missing after EACCES rejection');process.exit(0);
 },100);
});
