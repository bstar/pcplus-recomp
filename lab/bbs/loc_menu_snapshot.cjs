'use strict';
const fs=require('fs'),path=require('path'),Module=require('module'),assert=require('assert');
const base=process.argv[2];
const iconv=require(base+'/node_modules/iconv-lite');
const target=base+'/mods/loc_main_menu/loc_main_menu.js';
const out=process.argv[3];
function capture(source,height,browser){
 const m=new Module(target,module);m.filename=target;m.paths=Module._nodeModulePaths(path.dirname(target));m._compile(source,target);
 const c=Object.create(m.exports.getModule.prototype);let wire='',prompt,finished=false;
 c.menuConfig={config:{}};
 c.client={term:{termHeight:height,termWidth:80,termClient:browser?'vtx':'ansi',outputEncoding:'cp437',rawWrite:s=>{wire+=s},write:s=>{wire+=s}},log:{error:()=>{throw Error('menu failed')}}};
 c.mciReady=(value,cb)=>{prompt=value.prompt.ET2.position;cb(null)};c.finishedLoading=()=>{finished=true};
 c.initSequence();assert(finished);
 return {wire,prompt,bytes:iconv.encode(wire,'cp437')};
}
const before=fs.readFileSync(out+'/loc_main_menu.before.js','utf8'),after=fs.readFileSync(target,'utf8');
const old=capture(before,25,false),fixed25=capture(after,25,false),fixed24=capture(after,24,false);
assert(capture(before,25,true).bytes.equals(capture(after,25,true).bytes),'Browser25 output changed');
for(const c of [fixed25,fixed24])assert(!/\x1b\[(?:9[0-7])m/.test(c.wire));
assert.deepEqual(fixed24.prompt,[24,46]);assert.deepEqual(fixed25.prompt,[25,46]);
assert(!/\x1b\[25;1H/.test(fixed24.wire));assert(/\x1b\[24;1H/.test(fixed24.wire));
for(const [name,c] of [['old',old],['fixed25',fixed25],['fixed24',fixed24]])fs.writeFileSync(out+'/'+name+'.bin',c.bytes);
const layout=JSON.parse(fs.readFileSync(base+'/mods/loc_main_menu/classic-pillars.json'));
fs.writeFileSync(out+'/layout.json',JSON.stringify(layout));
fs.writeFileSync(out+'/capture-result.json',JSON.stringify({passed:true,browser25Unchanged:true,classicColors:true,prompt24:fixed24.prompt,prompt25:fixed25.prompt},null,2));
console.log('PASS: browser25 byte-identical; DOS uses classic colors; 24-row prompt retained.');
