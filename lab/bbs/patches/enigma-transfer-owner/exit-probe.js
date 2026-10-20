'use strict';
const fs=require('fs'),path=require('path');
const candidate=fs.realpathSync(process.argv[2]),out=path.resolve(process.argv[3]);
fs.mkdirSync(out);fs.mkdirSync(out+'/tmp');process.env.TMPDIR=out+'/tmp';process.env.TMP=out+'/tmp';process.env.TEMP=out+'/tmp';
const Owner=require(candidate+'/core/transfer_temp_owner');
Owner.createUpload((err,a)=>{
 if(err)throw err;
 Owner.createList((err,b)=>{
  if(err)throw err;fs.writeFileSync(a.path+'/PART.BIN','failed');fs.writeFileSync(b.path+'/files.txt','healthy');
  fs.writeFileSync(out+'/paths.json',JSON.stringify({failed:a.path,healthy:b.path})+'\n');
  const original=fs.rmSync;fs.rmSync=(p,opts)=>{
   if(p===a.path)throw Object.assign(new Error('modeled exit cleanup denial'),{code:'EACCES'});
   return original(p,opts);
  };
  process.exit(0);
 });
});
