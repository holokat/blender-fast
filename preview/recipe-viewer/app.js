const $ = (id) => document.getElementById(id);
const base = await fetch('/recipe.json').then((r) => r.json());
let yaw = 0, elevation = 0, jobId, latestSequence = 0, submittedAt = 0, drag, timer;
const selected = new Set(['orrery','reactor','telescope','desk','treasury','throne','alchemy','hoist','ritual']);

function recipe() {
  const r = structuredClone(base);
  r.lighting.key = Number($('light').value);
  const [x,y,z] = base.camera.at;
  r.camera.at = [x*Math.cos(yaw)-y*Math.sin(yaw), x*Math.sin(yaw)+y*Math.cos(yaw), z+elevation];
  if ($('layout').checked) for (const a of r.assemblies) if (selected.has(a.id)) {
    a.yaw = (a.yaw || 0) + 16;
    a.at[0] += .55;
    a.at[1] -= .35;
  }
  return r;
}

async function submit(save=false, interactionStarted=performance.now()) {
  const sequence = ++latestSequence;
  const started = interactionStarted;
  $('updating').hidden = false;
  $('state').textContent = 'Queued';
  try {
    const response = await fetch('/api/render', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({recipe:recipe(),profile:$('quality').value,save})});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    if (sequence !== latestSequence) return;
    jobId = result.id; submittedAt = started;
  } catch (error) { $('state').textContent = error.message; $('updating').hidden = true; }
}

const events = new EventSource('/api/events');
events.onmessage = async ({data}) => {
  const result = JSON.parse(data);
  if (result.id !== jobId) return;
  if (result.status === 'error') { $('state').textContent = result.message; $('updating').hidden = true; return; }
  if (result.status !== 'complete') { $('state').textContent = 'Rendering'; return; }
  const current = jobId;
  const image = new Image();
  image.src = `/frames/${result.frame}?id=${result.id}`;
  try { await image.decode(); } catch { return; }
  if (current !== jobId) return;
  $('live').src = image.src;
  $('state').textContent = 'Up to date';
  $('updating').hidden = true;
  $('latency').textContent = `${((performance.now()-submittedAt)/1000).toFixed(2)} s input to decoded image · ${result.worker_seconds.toFixed(2)} s in worker`;
  $('engine').textContent = `${result.settings.engine==='CYCLES'?'Cycles':'Eevee'} · ${result.settings.resolution.join(' × ')} · ${result.settings.samples} samples`;
  if (result.saved) $('download').hidden = false;
};
events.onerror = () => { $('state').textContent = 'Reconnecting to preview server'; };
function schedule() { const started=performance.now(); clearTimeout(timer); timer = setTimeout(() => submit(false, started), 80); }
for (const id of ['quality','layout']) $(id).addEventListener('change', () => submit());
$('light').addEventListener('input', schedule);
$('reset').addEventListener('click', () => {yaw=0;elevation=0;submit();});
$('save').addEventListener('click', () => submit(true));
$('live').addEventListener('pointerdown', (e) => {drag={x:e.clientX,y:e.clientY,yaw,elevation};$('live').setPointerCapture(e.pointerId);});
$('live').addEventListener('pointermove', (e) => {
  if (!drag) return;
  yaw=drag.yaw+(e.clientX-drag.x)*.005;
  elevation=Math.max(-20,Math.min(45,drag.elevation-(e.clientY-drag.y)*.10));schedule();
});
$('live').addEventListener('pointerup', () => {drag=null;clearTimeout(timer);submit();});
$('live').addEventListener('pointercancel', () => {drag=null;});
$('live').addEventListener('keydown', (e) => {
  if (!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)) return;
  e.preventDefault();
  if(e.key==='ArrowLeft')yaw-=.12;if(e.key==='ArrowRight')yaw+=.12;
  if(e.key==='ArrowUp')elevation=Math.min(45,elevation+3);if(e.key==='ArrowDown')elevation=Math.max(-20,elevation-3);
  submit();
});
try {
  const summary=await fetch('/summary.json').then(r=>r.json());
  $('results').replaceChildren();
  for(const row of summary.lanes || []) {
    const tr=document.createElement('tr');
    for(const value of [row.label,`${row.median_seconds.toFixed(3)} s`,`${row.speedup_opt1.toFixed(2)}×`,`${row.speedup_optNEW.toFixed(2)}×`]) {
      const td=document.createElement('td');td.textContent=value;tr.append(td);
    }
    $('results').append(tr);
  }
} catch { $('results').textContent='Measurements are unavailable.'; }
submit();
