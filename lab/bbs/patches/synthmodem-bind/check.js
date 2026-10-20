'use strict';
// Verify native RTP and allocation honor the same bind setting as CallSession.
const assert=require('assert/strict'),path=require('path'),fs=require('fs'),crypto=require('crypto'),dgram=require('dgram');
const root=path.resolve(process.argv[2]),cfg=require(path.join(root,'config.js'));
cfg.logging.level='error';
const {RtpSession,allocateRtpPort,releaseRtpPort}=require(path.join(root,'src/rtp/RtpSession.js'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function main(){
 const checks={default_preserves_LAN_wildcard:cfg.rtp.bindAddress==='0.0.0.0'};
 const other=dgram.createSocket('udp4'),rtp=new RtpSession();let port;
 try{
  // A wildcard bind would conflict with this reservation. A configured
  // 127.0.0.1 bind can share its port with this distinct loopback address.
  await new Promise(r=>other.bind(0,'127.0.0.2',r));port=other.address().port;
  cfg.rtp.bindAddress='127.0.0.1';cfg.rtp.portMin=port;cfg.rtp.portMax=port;
  checks.allocator_uses_selected_interface=await allocateRtpPort()===port;
  await rtp.open(port);
  checks.native_RTP_loopback=rtp._socket.address().address==='127.0.0.1';
  checks.independent_reservation_survives=other.address().address==='127.0.0.2' && rtp._socket.address().port===port;
 }finally{
  if(rtp._socket){const closed=new Promise(r=>rtp._socket.once('close',r));rtp.close();await closed;}
  if(port)releaseRtpPort(port);await new Promise(r=>other.close(r));
 }
 assert(Object.values(checks).every(Boolean));
 const result={passed:true,checks,node:process.version,checker_sha256:sha(__filename),
  patch_sha256:sha(path.join(__dirname,'bind.patch')),
  source_sha256:Object.fromEntries(['config.js','src/rtp/RtpSession.js','src/session/CallSession.js'].map(n=>[n,sha(path.join(root,n))])),
  scope:'Actual native RTP open and allocator on distinct loopback addresses; normal CallSession binding is verified by the separate full gateway test.'};
 if(process.argv[3]){
  const output=path.resolve(process.argv[3]),repo=path.resolve(__dirname,'../../../..');
  assert(output.startsWith(repo+'/build/'));fs.mkdirSync(output);
  fs.writeFileSync(path.join(output,'result.json'),JSON.stringify(result,null,2)+'\n');
 }
 console.log(JSON.stringify(result,null,2));
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
