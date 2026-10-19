"""Búsqueda geométrica de tarjetas y estabilización de predicciones en video."""
import time
import base64
import binascii
import io
import json
from pathlib import Path
from functools import lru_cache
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .inference import classify_frame


def detect_card(frame):
    """Devuelve contorno cuadrilateral; es una heurística, no detector entrenado."""
    rgb=np.asarray(frame.convert('RGB'))
    height,width=rgb.shape[:2]
    scale=min(1.,640/max(height,width))
    small=cv2.resize(rgb,(max(1,round(width*scale)),max(1,round(height*scale))))
    gray=cv2.cvtColor(small,cv2.COLOR_RGB2GRAY)
    edges=cv2.Canny(cv2.GaussianBlur(gray,(5,5),0),40,140)
    edges=cv2.morphologyEx(edges,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    contours,_=cv2.findContours(edges,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    candidates=[]
    for contour in contours:
        area=cv2.contourArea(contour)
        fraction=area/(small.shape[0]*small.shape[1])
        if not .015<=fraction<=.85:continue
        polygon=cv2.approxPolyDP(contour,.025*cv2.arcLength(contour,True),True)
        if len(polygon)!=4 or not cv2.isContourConvex(polygon):continue
        x,y,w,h=cv2.boundingRect(polygon)
        if not .6<=w/h<=1.65 or area/(w*h)<.65:continue
        center_distance=((x+w/2-small.shape[1]/2)/small.shape[1])**2+((y+h/2-small.shape[0]/2)/small.shape[0])**2
        rank=fraction/(1+center_distance)
        points=(polygon.reshape(4,2)/scale).round().astype(int).tolist()
        box=[round(x/scale),round(y/scale),round((x+w)/scale),round((y+h)/scale)]
        candidates.append((rank,dict(points=points,box=box)))
    if not candidates:
        # Fallback para bordes interrumpidos por manos, sombras o laminado.
        hsv=cv2.cvtColor(small,cv2.COLOR_RGB2HSV)
        mask=cv2.inRange(hsv,np.array([0,0,130]),np.array([179,70,255]))
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
        surfaces,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for contour in surfaces:
            area=cv2.contourArea(contour);fraction=area/(small.shape[0]*small.shape[1])
            if not .015<=fraction<=.8:continue
            rect=cv2.minAreaRect(contour);rw,rh=rect[1]
            if min(rw,rh)<12 or not .6<=rw/rh<=1.65 or area/(rw*rh)<.72:continue
            polygon=cv2.boxPoints(rect)
            x,y,w,h=cv2.boundingRect(polygon)
            if x<0 or y<0 or x+w>=small.shape[1] or y+h>=small.shape[0]:continue
            center_distance=((x+w/2-small.shape[1]/2)/small.shape[1])**2+((y+h/2-small.shape[0]/2)/small.shape[0])**2
            points=(polygon/scale).round().astype(int).tolist()
            box=[round(x/scale),round(y/scale),round((x+w)/scale),round((y+h)/scale)]
            candidates.append((fraction/(1+center_distance),dict(points=points,box=box)))
    return max(candidates,key=lambda item:item[0])[1] if candidates else None


def overlap(a,b):
    left=max(a[0],b[0]);top=max(a[1],b[1]);right=min(a[2],b[2]);bottom=min(a[3],b[3])
    intersection=max(0,right-left)*max(0,bottom-top)
    union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-intersection
    return intersection/union if union>0 else 0.


def advance_state(previous,label,box,now=None):
    now=time.monotonic() if now is None else now
    previous=previous or {}
    continuous=(previous.get('label')==label and 0<=now-previous.get('time',-100)<15
                and overlap(previous.get('box',[0,0,0,0]),box)>.25)
    count=min(3,previous.get('count',0)+1) if continuous else 1
    return dict(label=label,box=box,count=count,time=now),count>=3


def annotate(frame,card,text,accepted=False):
    display=frame.convert('RGB').copy()
    if max(display.size)>960:
        scale=960/max(display.size)
        display=display.resize((round(display.width*scale),round(display.height*scale)),Image.Resampling.LANCZOS)
        if card:
            card=dict(points=[[round(v*scale) for v in p] for p in card['points']],box=[round(v*scale) for v in card['box']])
    draw=ImageDraw.Draw(display)
    color='#16834a' if accepted else '#b66a00'
    if card:
        points=[tuple(p) for p in card['points']]
        draw.line(points+[points[0]],fill=color,width=max(3,display.width//180))
    font_size=max(18,min(36,display.width//22))
    try:font=ImageFont.truetype('segoeui.ttf',font_size)
    except OSError:font=ImageFont.load_default(size=font_size)
    length=draw.textbbox((0,0),text,font=font)
    width=min(display.width-12,length[2]-length[0]+24);height=font_size+22
    if card:
        x=min(max(6,card['box'][0]),max(6,display.width-width-6))
        y=max(6,card['box'][1]-height-8)
    else:x,y=6,6
    draw.rounded_rectangle((x,y,x+width,y+height),radius=12,fill=color)
    draw.text((x+12,y+5),text,font=font,fill='white')
    return display


def analyze_live_frame(frame,state,names):
    if frame is None:return dict(word='—',status='Activá la cámara para comenzar.',card=None,text='Buscando tarjeta',accepted=False),{}
    if not isinstance(frame,Image.Image):raise ValueError('Fotograma inválido.')
    frame=frame.convert('RGB');card=detect_card(frame)
    result=dict(word='—',status='Acercá una tarjeta al centro de la cámara.',card=card,text='Buscando tarjeta',accepted=False)
    if card is None:return result,{}
    try:
        prediction=classify_frame(frame)  # Se conserva el fotograma COMPLETO.
        if prediction['rejected']:
            result.update(status='Tarjeta detectada; pictograma no reconocido.',text='No reconocido')
            return result,{}
        label=prediction['label'];text=names[label]
        updated,stable=advance_state(state,label,card['box'])
        if not stable:
            result.update(text=f"Confirmando {updated['count']}/3",status=f"Candidata: {text} · confirmación {updated['count']}/3. Mantené la tarjeta visible.")
        else:
            result.update(word=text,text=text,accepted=True,status='Pictograma reconocido. Mostrá otra tarjeta para cambiar la palabra.')
        return result,updated
    except (ValueError,OSError) as error:
        result.update(status=str(error),text='Sin resultado')
        return result,{}


def process_live_frame(frame,state,names):
    if frame is None:return None,'—','Activá la cámara para comenzar.',{}
    if not isinstance(frame,Image.Image):return None,'—','Fotograma inválido.',{}
    result,updated=analyze_live_frame(frame,state,names)
    return annotate(frame,result['card'],result['text'],result['accepted']),result['word'],result['status'],updated


@lru_cache(maxsize=1)
def camera_names():
    project=json.loads((Path(__file__).resolve().parents[2]/'config/project.json').read_text(encoding='utf-8'))
    return {c['id']:c['display_name'] for c in project['classes']}


def analyze_camera(payload):
    """RPC de cámara: JPEG pequeño en memoria; respuesta JSON sin guardar video."""
    if payload is None:return dict(word='—',status='Cámara detenida.',card=None,state={},accepted=False,text='')
    if not isinstance(payload,dict):raise ValueError('Solicitud de cámara inválida.')
    data_uri=payload.get('frame');state=payload.get('state')
    if not isinstance(data_uri,str) or len(data_uri)>1_500_000 or not data_uri.startswith('data:image/jpeg;base64,'):
        raise ValueError('Fotograma JPEG inválido o demasiado grande.')
    try:
        data=base64.b64decode(data_uri.split(',',1)[1],validate=True)
        with Image.open(io.BytesIO(data)) as image:
            if image.format!='JPEG' or image.width*image.height>1280*1280:
                raise ValueError('Dimensiones de fotograma inválidas.')
            image.load();frame=image.convert('RGB')
    except (binascii.Error,OSError) as error:
        raise ValueError('No se pudo leer el fotograma.') from error
    # Solo se recibe el estado de confirmación de esta cámara; no rutas ni archivos.
    clean={}
    if isinstance(state,dict) and state.get('label') in camera_names():
        box=state.get('box');count=state.get('count');stamp=state.get('time')
        if isinstance(box,list) and len(box)==4 and all(isinstance(v,(int,float)) and np.isfinite(v) for v in box) and isinstance(count,int) and 1<=count<=3 and isinstance(stamp,(int,float)) and np.isfinite(stamp):
            clean=dict(label=state['label'],box=box,count=count,time=stamp)
    result,updated=analyze_live_frame(frame,clean,camera_names())
    result.update(state=updated,width=frame.width,height=frame.height)
    return result
