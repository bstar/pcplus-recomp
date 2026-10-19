'use strict';
// Actual owned search.js -> real FileEntry.findFiles and generated SQLite FTS.
// The selected synthetic file database is opened read-only; no SQL/provider
// function is substituted. Allowed areas are explicit fixture inputs.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(process.argv[2]);
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
require(path.join(root,'test/setup.js'));
const config=require(path.join(root,'core/config.js')).get();
config.fileBase=JSON.parse(fs.readFileSync(path.join(root,'config/config.hjson'),'utf8')).fileBase;
const Database=require(path.join(root,'node_modules/better-sqlite3'));
const db=new Database(path.join(root,'db/file.sqlite3'),{readonly:true});
require(path.join(root,'core/database.js')).dbs.file=db;
const {findRows}=require(path.join(root,'mods/black_flag_files/search.js'));
const names=Array.from({length:30},(_,i)=>`PCPLUS PROBE ${String(i).padStart(2,'0')} (1991).ZIP`);
const results=[];
async function check(name,criteria,allowed,expected,mode){
 const observed=await new Promise((resolve,reject)=>findRows(criteria,allowed,(err,rows,kind)=>err?reject(err):resolve({rows,kind})));
 assert.equal(observed.kind,mode,name);assert.deepEqual(observed.rows.map(r=>r.name),expected,name);
 assert.ok(observed.rows.every(r=>r.storage==='exodos_games'&&Number(r.size)>0),name);
 results.push({case:name,passed:true,count:observed.rows.length,mode:observed.kind});
}
async function run(){
 try{
  await check('browse-allowed-area',{},['pcplus_games'],names,'Browse');
  await check('title-multiple-tokens',{terms:'PCPLUS PROBE'},['pcplus_games'],names,'Titles / filenames');
  await check('case-and-punctuation',{terms:'pcplus-probe-02'},['pcplus_games'],[names[2]],'Titles / filenames');
  await check('unicode-folding',{terms:'PROBÉ 01'},['pcplus_games'],[names[1]],'Titles / filenames');
  await check('anchored-wildcard',{terms:'PCPLUS PROBE 0? (1991).ZIP'},['pcplus_games'],names.slice(0,10),'Titles / filenames');
  await check('wildcard-all-allowed',{terms:'*'},['pcplus_games'],names,'Titles / filenames');
  await check('fulltext-description',{terms:'text: Generated'},['pcplus_games'],names,'Full text');
  await check('no-results',{terms:'ZZZNOMATCH'},['pcplus_games'],[],'Titles / filenames');
  await check('explicit-area-intersection',{terms:'PCPLUS',areaTag:['pcplus_games','hidden']},['pcplus_games'],names,'Titles / filenames');
  await check('disallowed-area',{terms:'PCPLUS',areaTag:'hidden'},['pcplus_games'],[],'Titles / filenames');
  await check('no-allowed-areas',{terms:'PCPLUS'},[],[],'Titles / filenames');
  console.log(JSON.stringify({passed:true,checks:results.length,cases:results,node:process.version,checker_sha256:sha(__filename),
   search_sha256:sha(path.join(root,'mods/black_flag_files/search.js')),file_entry_sha256:sha(path.join(root,'core/file_entry.js')),
   scope:'Exact owned search module, real FileEntry query builder, read-only generated SQLite file/FTS tables. Explicit allowed-area inputs; no actual user ACS or DOS keyboard claim from these queries.'}));
 }finally{db.close();}
}
run().catch(err=>{console.error(err);process.exitCode=1;});
