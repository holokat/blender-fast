const vs=`attribute vec3 aPosition;attribute vec3 aNormal;attribute vec3 aColor;uniform mat4 uMatrix;varying vec3 vColor;void main(){gl_Position=uMatrix*vec4(aPosition,1.);float light=.48+.52*max(dot(normalize(aNormal),normalize(vec3(-.4,-.5,1.))),0.);vColor=aColor*light;}`;
const fs=`precision mediump float;varying vec3 vColor;void main(){gl_FragColor=vec4(vColor,1.);}`;
const sub=(a,b)=>a.map((x,i)=>x-b[i]);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const norm=a=>{const l=Math.hypot(...a)||1;return a.map(v=>v/l)};

export class JetView{
 constructor(canvas,asset,onOrbit){
  this.canvas=canvas;this.created=-1;this.dirty=true;this.angle=.615;this.tilt=.57;this.gl=canvas.getContext('webgl',{alpha:true,antialias:true});
  if(!this.gl)throw Error('WebGL is unavailable. Rendered images remain available after a run.');
  const gl=this.gl,program=gl.createProgram();
  for(const [type,source] of [[gl.VERTEX_SHADER,vs],[gl.FRAGMENT_SHADER,fs]]){const shader=gl.createShader(type);gl.shaderSource(shader,source);gl.compileShader(shader);if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(shader));gl.attachShader(program,shader)}
  gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);this.program=program;this.matrix=gl.getUniformLocation(program,'uMatrix');
  const vertices=[];this.ends=[0];
  for(const obj of asset.objects){
   const color=[1,3,5].map(i=>parseInt(obj.color.slice(i,i+2),16)/255);
   for(const triangle of obj.triangles){const pts=triangle.map(i=>obj.vertices[i]);const normal=norm(cross(sub(pts[1],pts[0]),sub(pts[2],pts[0])));for(const p of pts)vertices.push(...p,...normal,...color)}
   this.ends.push(vertices.length/9);
  }
  const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(vertices),gl.STATIC_DRAW);
  for(const [i,name] of ['aPosition','aNormal','aColor'].entries()){const loc=gl.getAttribLocation(program,name);gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,3,gl.FLOAT,false,36,i*12)}
  gl.enable(gl.DEPTH_TEST);gl.clearColor(0,0,0,0);
  let previous=null;
  canvas.addEventListener('pointerdown',e=>{previous=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId)});
  canvas.addEventListener('pointermove',e=>{if(!previous)return;onOrbit((e.clientX-previous[0])*.009,(e.clientY-previous[1])*.006);previous=[e.clientX,e.clientY]});
  const end=()=>{previous=null};canvas.addEventListener('pointerup',end);canvas.addEventListener('pointercancel',end);
  new ResizeObserver(()=>this.dirty=true).observe(canvas);
 }
 draw(created){
  if(created===this.created&&!this.dirty)return;this.created=created;this.dirty=false;
  const gl=this.gl;const dpr=Math.min(devicePixelRatio,2),w=Math.round(this.canvas.clientWidth*dpr),h=Math.round(this.canvas.clientHeight*dpr);if(!w||!h)return;
  this.canvas.width=w;this.canvas.height=h;gl.viewport(0,0,w,h);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
  const eye=[Math.sin(this.angle)*Math.cos(this.tilt)*22,-Math.cos(this.angle)*Math.cos(this.tilt)*22,Math.sin(this.tilt)*22];
  const center=[0,-.5,.15],z=norm(sub(eye,center)),x=norm(cross([0,0,1],z)),y=cross(z,x),width=18.8,height=width*h/w;
  const sx=2/width,sy=2/height,sz=-2/100;
  const matrix=[sx*x[0],sy*y[0],sz*z[0],0,sx*x[1],sy*y[1],sz*z[1],0,sx*x[2],sy*y[2],sz*z[2],0,-sx*dot(x,center),-sy*dot(y,center),0,1];
  gl.uniformMatrix4fv(this.matrix,false,new Float32Array(matrix));gl.drawArrays(gl.TRIANGLES,0,this.ends[Math.min(Math.max(created,0),this.ends.length-1)]);
 }
}
