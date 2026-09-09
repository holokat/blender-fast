const $ = id => document.getElementById(id);
const root = new URL(new URL(location.href).searchParams.get('data') || './shape-output/', location.href);
if (!root.pathname.endsWith('/')) root.pathname += '/';
const names = { interactive: 'Eevee 4', optNEW: 'Cycles 8', opt1: 'Cycles 64', eevee: 'Eevee 16' };
let result;
let displayRevision = 0;
async function display() {
  const revision = ++displayRevision;
  const frame = result.renders.find(r => r.profile === $('quality').value);
  if (!frame) return;
  const img = new Image();
  img.src = new URL(frame.file, root).href;
  await img.decode();
  if (revision !== displayRevision) return;
  $('render').src = img.src;
  $('render').hidden = false;
  $('render').alt = `Blender render of ${result.title}, ${names[frame.profile]}`;
  $('frame-timing').textContent = `${frame.render_seconds.toFixed(2)} s to render and write this frame`;
  $('frame-config').textContent = `${names[frame.profile]} · ${frame.resolution.join(' × ')}`;
}
function row(label, seconds, elapsed) {
  const tr = document.createElement('tr');
  for (const value of [label, `${seconds.toFixed(3)} s`, `${elapsed.toFixed(3)} s`]) {
    const td = document.createElement('td'); td.textContent = value; tr.append(td);
  }
  $('timings').append(tr);
}
async function load() {
  const response = await fetch(new URL('result.json', root), { cache: 'no-store' });
  if (!response.ok) throw new Error('Scene measurements are not available yet.');
  result = await response.json();
  $('title').textContent = result.title;
  document.title = `${result.title} · Blender fast`;
  $('scope').textContent = result.timing_scope;
  $('program').href = new URL('program.json', root).href;
  $('blend').href = new URL('scene.blend', root).href;
  $('timings').replaceChildren();
  row('Validate and construct geometry', result.build.apply_seconds, result.build.apply_seconds);
  for (const frame of result.renders) row(names[frame.profile], frame.render_seconds, frame.elapsed_seconds);
  if (result.save_seconds !== undefined) row('Save editable scene', result.save_seconds, result.total_seconds);
  const inv = result.inventory;
  $('inventory').textContent = `${inv.assemblies} assemblies · ${inv.objects.toLocaleString()} objects · ${inv.faces.toLocaleString()} mesh faces · ${inv.mesh_datablocks} shared mesh datablocks`;
  for (const option of $('quality').options) option.disabled = !result.renders.some(r => r.profile === option.value);
  if (!result.renders.some(r => r.profile === $('quality').value)) $('quality').value = result.renders.at(-1)?.profile || 'interactive';
  $('quality').disabled = !result.renders.length;
  $('status').textContent = result.total_seconds === undefined ? 'Rendering the next quality' : `${result.renders.length} rendered ${result.renders.length === 1 ? 'quality' : 'qualities'} ready`;
  await display();
  if (result.total_seconds === undefined) setTimeout(() => load().catch(showError), 2000);
}
function showError(error) { $('status').textContent = error.message; }
$('quality').addEventListener('change', () => display().catch(showError));
load().catch(showError);
