"""Vista de cámara móvil: un fotograma por solicitud, sin cola de video."""
HTML = """
<div class="camera-live">
  <div class="camera-controls"><button type="button" data-start>Iniciar cámara</button><button type="button" data-stop disabled>Detener y limpiar</button></div>
  <div class="camera-view"><video aria-label="Vista de la cámara" playsinline muted autoplay></video><canvas data-overlay aria-hidden="true"></canvas></div>
  <div class="camera-word" data-word aria-live="polite">—</div>
  <p data-status aria-live="polite">Tocá Iniciar cámara y permití el acceso.</p>
  <small data-timing></small>
</div>
"""
CSS = """
.camera-controls {display:flex; gap:12px; flex-wrap:wrap; margin:12px 0;}
button {padding:12px 18px; border-radius:10px; border:2px solid #475569; font-family:Verdana,Arial,sans-serif; font-size:1.125rem; line-height:1.5; min-height:48px; white-space:normal; cursor:pointer;}
button[data-start] {background:#1E40AF; color:white;}
button:disabled {background:#E2E8F0; color:#475569; cursor:default;}
button:focus-visible {outline:3px solid #1E40AF; outline-offset:4px; box-shadow:0 0 0 4px white;}
.camera-live {font-family:Verdana,Arial,sans-serif; color:#0F172A; background:#FFFFFF;}
button[data-stop] {background:#FFFFFF; color:#1E40AF;}
.camera-view {position:relative; width:100%; max-width:720px; margin:auto; background:#171717; border-radius:12px; overflow:hidden;min-height:180px;}
video {width:100%; display:block; height:auto; object-fit:contain;}
canvas {position:absolute; inset:0; width:100%; height:100%;pointer-events:none;}
.camera-word {font-size:2rem; overflow-wrap:anywhere; font-weight:700; margin:12px 0; text-align:center;}
p {font-size:1.125rem; line-height:1.5; margin:8px 0;}
small {color:#475569; font-size:1rem;}
"""
JS = """
const root=element.querySelector('.camera-live');
const video=root.querySelector('video'), overlay=root.querySelector('[data-overlay]');
const start=root.querySelector('[data-start]'), stopButton=root.querySelector('[data-stop]');
const word=root.querySelector('[data-word]'), status=root.querySelector('[data-status]'), timing=root.querySelector('[data-timing]');
const capture=document.createElement('canvas'), ctx=overlay.getContext('2d');
let media=null, active=false, generation=0, state={}, result=null, received=0, frameNumber=0;
let busy=false;
function clearResult(){result=null;state={};word.textContent='—';ctx.clearRect(0,0,overlay.width,overlay.height);}
function stop(){active=false;generation++;if(media)media.getTracks().forEach(t=>t.stop());media=null;video.srcObject=null;clearResult();start.disabled=false;stopButton.disabled=true;status.textContent='Cámara detenida.';timing.textContent='';}
function draw(){
 if(active && video.videoWidth){
  if(overlay.width!==video.videoWidth || overlay.height!==video.videoHeight){overlay.width=video.videoWidth;overlay.height=video.videoHeight;}
  ctx.clearRect(0,0,overlay.width,overlay.height);
  if(result && performance.now()-received<15000){
   const sx=overlay.width/result.width, sy=overlay.height/result.height;
   ctx.strokeStyle=result.accepted?'#00d481':'#ffb340';ctx.fillStyle=result.accepted?'#1E40AF':'#78350F';ctx.lineWidth=4;
   if(result.card){const points=result.card.points;ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p[0]*sx,p[1]*sy):ctx.moveTo(p[0]*sx,p[1]*sy));ctx.closePath();ctx.stroke();}
   const text=result.text || '';const font=Math.max(20,Math.round(overlay.width/23));ctx.font=`bold ${font}px sans-serif`;
   const width=Math.min(overlay.width-16,ctx.measureText(text).width+24),height=font+22;
   let x=result.card?result.card.box[0]*sx:8,y=result.card?result.card.box[1]*sy-height-8:8;
   x=Math.max(8,Math.min(x,overlay.width-width-8));y=Math.max(8,y);
   ctx.fillRect(x,y,width,height);ctx.fillStyle='white';ctx.fillText(text,x+12,y+font+3);
  }else if(result){clearResult();status.textContent='Sin respuesta reciente. Volvé a iniciar la cámara.';}
 }
 if(element.isConnected)requestAnimationFrame(draw);else stop();
}
async function nextFrame(token){
 if(!active || token!==generation)return;
 if(busy){setTimeout(()=>nextFrame(token),200);return;}
 if(video.readyState<2){setTimeout(()=>nextFrame(token),200);return;}
 busy=true;const begin=performance.now();
 try{
  const scale=Math.min(1,640/Math.max(video.videoWidth,video.videoHeight));
  capture.width=Math.round(video.videoWidth*scale);capture.height=Math.round(video.videoHeight*scale);
  capture.getContext('2d').drawImage(video,0,0,capture.width,capture.height);
  status.textContent='Analizando tarjeta…';
  const response=await server.analyze_camera({frame:capture.toDataURL('image/jpeg',0.75),state});
  if(!active || token!==generation)return;
  state=response.state || {};result=response;received=performance.now();frameNumber++;
  word.textContent=response.word;status.textContent=response.status;
  timing.textContent=`Imagen ${frameNumber} · respuesta en ${((received-begin)/1000).toFixed(1)} s`;
 }catch(error){
  if(active && token===generation){clearResult();status.textContent='No se pudo analizar: '+(error.message || String(error));}
 }finally{busy=false;if(active && token===generation)setTimeout(()=>nextFrame(token),700);}
}
start.addEventListener('click',async()=>{
 if(active)return;
 if(!window.isSecureContext || !navigator.mediaDevices?.getUserMedia){status.textContent='Para usar la cámara abrí el enlace HTTPS en Chrome o Safari.';return;}
 start.disabled=true;status.textContent='Solicitando permiso de cámara…';
 const token=++generation;
 try{
  const stream=await navigator.mediaDevices.getUserMedia({audio:false,video:{facingMode:{ideal:'environment'},width:{ideal:640},height:{ideal:480}}});
  if(token!==generation){stream.getTracks().forEach(t=>t.stop());return;}
  media=stream;video.srcObject=stream;await video.play();active=true;state={};result=null;frameNumber=0;stopButton.disabled=false;nextFrame(token);
 }catch(error){stop();status.textContent='No se pudo iniciar la cámara. Revisá el permiso del navegador: '+(error.message || String(error));}
});
stopButton.addEventListener('click',stop);
window.addEventListener('pagehide',stop);
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
requestAnimationFrame(draw);
"""
