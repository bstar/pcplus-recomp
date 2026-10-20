'use strict';
// Isolated test preload: fail only the first owned upload-directory removal.
const fs=require('fs'),path=require('path');
const report=process.env.PCPLUS_ENIGMA_FAULT_LOG,temporary=process.env.TMPDIR;
const root=path.resolve(__dirname,'../../../..');
if(!report||!temporary||!path.resolve(report).startsWith(root+'/build/')||path.dirname(path.resolve(temporary))!==path.dirname(path.resolve(report)))throw new Error('Owned fault environment required');
const original=fs.rm;let injected=false;
fs.rm=function(target,options,cb){
 if(!injected&&typeof target==='string'&&typeof cb==='function'&&path.dirname(path.resolve(target))===path.resolve(temporary)&&path.basename(target).startsWith('enigul-')){
  injected=true;
  fs.appendFileSync(report,JSON.stringify({injected:true,operation:'rm',code:'EACCES',target:path.basename(target)})+'\n');
  return queueMicrotask(()=>cb(Object.assign(new Error('modeled upload cleanup denial'),{code:'EACCES'})));
 }
 return original.apply(this,arguments);
};
