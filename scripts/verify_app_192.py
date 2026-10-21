"""Comprueba paquete seleccionado, foto yRPC de cámara con imágenes de desarrollo."""
import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
os.environ.setdefault('GRADIO_ANALYTICS_ENABLED','False')
from pathlib import Path
import sys,json,io,base64,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from reconocimiento_pictogramas.artifacts import read_json,read_csv,save_json,contained

def main():
 import tensorflow as tf
 tf.config.threading.set_intra_op_parallelism_threads(4);tf.config.threading.set_inter_op_parallelism_threads(2)
 from PIL import Image,ImageOps
 from reconocimiento_pictogramas.inference import load_selected_model,load_selected_detector,classify_frame
 from reconocimiento_pictogramas import ui,live
 report=ROOT/'reports/mobilenet_app_192_20261020';selected=read_json(ROOT/'config/application.json')
 assert selected['model_path']=='models/mobilenet_app_192_20261020/best.keras' and selected['image_size']==[192,192]
 model,cfg=load_selected_model();load_selected_detector();rows=read_csv(report/'calibration_predictions.csv');names={c['id']:c['display_name'] for c in read_json(ROOT/'config/project.json')['classes']}
 tests=[];camera=None
 for cls in names:
  row=next(r for r in rows if r['class_id']==cls and r['predicted_class']==cls and r['rejected']=='0')
  result=ui.recognize_image(str(contained(row['raw_path'])));assert result[0].size==(192,192) and result[2]==names[cls];assert ui.prepare_image(str(contained(row['raw_path']))).size==(192,192)
  tests.append(dict(class_id=cls,photo_accepted=True,preview_size=[192,192],raw_path=row['raw_path']))
  if camera is None:
   with Image.open(contained(row['raw_path'])) as im:frame=ImageOps.exif_transpose(im).convert('RGB');frame.thumbnail((640,640))
   if live.detect_card(frame) is not None:
    prediction=classify_frame(frame)
    if not prediction['rejected'] and prediction['label']==cls:
     stream=io.BytesIO();frame.save(stream,format='JPEG',quality=75);uri='data:image/jpeg;base64,'+base64.b64encode(stream.getvalue()).decode('ascii');state={};responses=[]
     for _ in range(3):
      response=live.analyze_camera(dict(frame=uri,state=state));state=response['state'];responses.append(response)
     if responses[-1]['accepted'] and responses[-1]['word']==names[cls]:camera=dict(class_id=cls,confirmed_after=3,word=names[cls],counts=[r['state'].get('count') for r in responses])
 unknown=next(r for r in rows if r['class_id']=='unknown' and r['rejected']=='1');result=ui.recognize_image(str(contained(unknown['raw_path'])));assert result[2]=='Pictograma no reconocido' and result[0].size==(192,192)
 assert camera is not None,'Ninguna muestra confirmó cámara: revisar integración'
 assert live.analyze_camera(None)['word']=='—'
 save_json(report/'app_smoke_test.json',dict(selected_model=selected['model_path'],ten_classes=tests,unknown_photo_rejected=True,camera_rpc=camera,clear_camera_verified=True,real_phone_tested=False,scope='Integracion local con imágenes internas, no métricas independientes ni cámara física',test_used=False))
 print('Verificadas diez clases por foto, desconocido yconfirmacion de tres fotogramas porRPC. No prueba de cámara física.',flush=True)
if __name__=='__main__':main()
