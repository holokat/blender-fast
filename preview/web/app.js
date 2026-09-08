import {JetView} from './model.js';
import {laneAt,median} from './timeline.js';
const $=s=>document.querySelector(s),ids=['baseline','optimized'];
let state=null,asset=null,views={},mode='live',replayT=0,playing=false,lastFrame=performance.now(),forceGeometry=false,receivedAt=0;
let replayMax=0,pollBusy=false,objectCount=0;
const labels={setup:'Preparing',build:'Building',verify:'Verifying',save:'Saving',start_renderer:'Starting renderer',first_render:'First render',repeat_1:'Warm repeat 1',repeat_2:'Warm repeat 2',repeat_3:'Warm repeat 3',done:'Complete'};
const seconds=n=>Number.isFinite(n)?`${n.toFixed(2)} s`:'Pending';
function duration(id){return state?.lanes?.[id]?.total_seconds??state?.lanes?.[id]?.elapsed??0}
function updateLane(id){
 const current=state?.lanes?.[id];
 let t=mode==='replay'?replayT:current?.elapsed??0;
 if(mode==='live'&&state?.status==='running'&&current&&!current.done)t=Math.max(t,state.server_epoch-current.started_epoch+(performance.now()-receivedAt)/1000);
 const lane=laneAt(state?.events,id,t),root=$(`#${id}`),img=root.querySelector('img');
 root.querySelector('.phase').textContent=current?(labels[lane.phase]||lane.phase):'Waiting';
 root.querySelector('.elapsed').replaceChildren(document.createTextNode(lane.elapsed.toFixed(2)),Object.assign(document.createElement('span'),{textContent:' s'}));
 root.querySelector('.calls').textContent=lane.calls||0;
 root.querySelector('.objects').textContent=`${lane.created} / ${objectCount} objects`;
 root.querySelector('.progress').style.width=`${objectCount?lane.created/objectCount*100:0}%`;
 let build=lane.build_seconds;
 if(lane.phase==='build'&&lane.buildStart!==undefined)build=Math.max(build||0,t-lane.buildStart);
 root.querySelector('.build-time').textContent=seconds(build);
 const first=lane.renders.find(r=>r.phase==='first_render');
 root.querySelector('.first-time').textContent=seconds(first?.seconds??(lane.phase==='first_render'&&lane.phaseStart!==undefined?t-lane.phaseStart:null));
 root.querySelector('.warm-time').textContent=seconds(median(lane.renders.filter(r=>r.phase.startsWith('repeat_')).map(r=>r.seconds)));
 const showImage=lane.image&&!forceGeometry;
 img.hidden=!showImage;root.querySelector('canvas').hidden=!!showImage;
 if(showImage&&img.getAttribute('src')!==lane.image)img.src=lane.image;
 root.querySelector('.view-label').textContent=showImage?'Completed Cycles render':mode==='replay'?'Recorded build progress':'Live geometry preview';
 views[id]?.draw(lane.created);
}
function render(){
 const now=performance.now(),dt=(now-lastFrame)/1000;lastFrame=now;
 if(playing){replayT=Math.min(replayMax,replayT+dt*Number($('#speed').value));if(replayT>=replayMax){playing=false;$('#replay').textContent='Play replay'}}
 if(state){for(const id of ids)updateLane(id);$('#scrub').value=mode==='replay'?replayT:0;$('#replay-time').textContent=seconds(mode==='replay'?replayT:0)}
 requestAnimationFrame(render);
}
function controls(){
 const running=state.status==='running';$('#run').disabled=running||!!state.requires_inspection;$('#stop').hidden=!running;$('#replay').disabled=running||state.status!=='complete';$('#scrub').disabled=running||state.status!=='complete';
 $('#message').textContent=state.message;$('#mode').textContent=mode==='replay'?'Recorded replay':'Live monitor';
 replayMax=Math.max(...ids.map(duration),1);$('#scrub').max=replayMax;
 const rows=state.results||[];
 if(rows.length===2&&state.status==='complete'){
  const a=rows.find(r=>r.lane==='baseline'),b=rows.find(r=>r.lane==='optimized'),ratio=a.total_seconds/b.total_seconds,saved=a.total_seconds-b.total_seconds;
  $('#advantage').textContent=ratio>=1?`${ratio.toFixed(2)}× faster across the measured pipeline`:`Optimized pipeline took ${(1/ratio).toFixed(2)}× as long`;
  $('#saving').textContent=`${Math.abs(saved).toFixed(2)} s ${saved>=0?'saved':'added'} · Build: ${(a.build_seconds/b.build_seconds).toFixed(1)}× · Warm renders: ${(a.warm_median_seconds/b.warm_median_seconds).toFixed(2)}×`;
  $('#validation').textContent=state.fingerprints_match?`${objectCount} objects · Geometry and materials match · Polling restored: ${state.polling_restored?'yes':'unconfirmed'}`:'Fingerprint verification failed';
  $('#download').href=`/runs/${state.run_id}/comparison.json`;$('#download').hidden=false;
 }else{$('#advantage').textContent=running?'Measuring both pipelines':'Waiting for both runs';$('#saving').textContent='Build, first render, and warm repeats are reported separately.';$('#validation').textContent='Geometry verification pending';$('#download').hidden=true}
 const settings=Object.values(state.lanes||{}).find(l=>l.settings)?.settings;
 if(settings)$('#hardware').textContent=`Blender ${settings.blender_version} · ${settings.devices.join(', ')} · 64 samples · 1400 × 1000`;
}
async function poll(){
 if(pollBusy)return;pollBusy=true;
 try{const response=await fetch('/api/state');if(!response.ok)throw Error('Server unavailable');const data=await response.json();const changed=data.revision!==state?.revision||data.run_id!==state?.run_id;
 state=data;receivedAt=performance.now();$('#connection').textContent='Local server connected';if(changed)controls();
 }catch(error){$('#connection').textContent='Connection lost';$('#message').textContent=error.message;$('#run').disabled=true}finally{pollBusy=false}
}
async function action(path){const response=await fetch(path,{method:'POST'});const data=await response.json();if(!response.ok)throw Error(data.error||'Action failed');await poll()}
$('#run').addEventListener('click',async()=>{try{mode='live';playing=false;replayT=0;$('#run').disabled=true;await action('/api/run')}catch(error){$('#message').textContent=error.message}});
$('#stop').addEventListener('click',async()=>{try{await action('/api/stop')}catch(error){$('#message').textContent=error.message}});
$('#replay').addEventListener('click',()=>{mode='replay';if(replayT>=replayMax)replayT=0;playing=!playing;$('#replay').textContent=playing?'Pause replay':'Play replay';controls()});
$('#scrub').addEventListener('input',()=>{mode='replay';replayT=Number($('#scrub').value);playing=false;$('#replay').textContent='Play replay';controls()});
$('#live').addEventListener('click',()=>{mode='live';playing=false;$('#replay').textContent='Play replay';controls()});
$('#view').addEventListener('click',()=>{forceGeometry=!forceGeometry;$('#view').textContent=forceGeometry?'Show rendered images':'Show geometry';for(const view of Object.values(views))view.dirty=true});
try{
 const response=await fetch('/asset/preview.json');if(!response.ok)throw Error('Preview geometry is unavailable');asset=await response.json();objectCount=asset.objects.length;
 const orbit=(dx,dy)=>{for(const view of Object.values(views)){view.angle+=dx;view.tilt=Math.max(.1,Math.min(1.4,view.tilt+dy));view.dirty=true}};
 for(const id of ids){try{views[id]=new JetView($(`#${id} canvas`),asset,orbit)}catch(error){$('#message').textContent=error.message}}
 await poll();setInterval(poll,250);requestAnimationFrame(render);
}catch(error){$('#message').textContent=error.message}
