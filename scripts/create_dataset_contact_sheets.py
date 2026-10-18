"""Hojas de contacto de desarrollo para revisión humana, sin tocar s007."""
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[1]

def thumb(path):
    with Image.open(path) as im:
        im.draft('RGB',(256,256))
        return ImageOps.contain(ImageOps.exif_transpose(im).convert('RGB'),(120,120))

def main():
    classes=[c['id'] for c in json.loads((ROOT/'config/project.json').read_text(encoding='utf-8'))['classes']]
    dest=ROOT/'reports/dataset_10_audit/contact_sheets';dest.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for session in [f's{i:03d}' for i in range(1,7)]:
            for group in range(2):
                canvas=Image.new('RGB',(1280,2270),'white');draw=ImageDraw.Draw(canvas)
                draw.text((5,2),f'{session} - originales reducidos para inspeccion',fill='black')
                for ci,cls in enumerate(classes[group*5:(group+1)*5]):
                    top=22+ci*448;draw.text((5,top),cls,fill='black')
                    paths=sorted((ROOT/f'data/raw/known/{cls}').glob(f'{cls}_{session}_*'))
                    for i,(path,im) in enumerate(zip(paths,pool.map(thumb,paths))):
                        x=(i%10)*128;y=top+15+(i//10)*143
                        canvas.paste(im,(x,y));draw.text((x,y+121),path.stem.split('_')[-1],fill='black')
                canvas.save(dest/f'{session}_group{group+1}.jpg',quality=92)
            print(f'Hojas {session} generadas',flush=True)
        for group in range(2):
            sessions=[f's{i:03d}' for i in range(group*3+1,group*3+4)]
            paths=[p for s in sessions for p in sorted((ROOT/'data/raw/unknown').glob(f'unknown_{s}_*'))]
            canvas=Image.new('RGB',(1280,((len(paths)+9)//10)*145+20),'white');draw=ImageDraw.Draw(canvas)
            draw.text((5,2),'unknown: '+','.join(sessions),fill='black')
            for i,(path,im) in enumerate(zip(paths,pool.map(thumb,paths))):
                x=(i%10)*128;y=20+(i//10)*145;canvas.paste(im,(x,y));draw.text((x,y+121),path.stem.replace('unknown_',''),fill='black')
            canvas.save(dest/f'unknown_group{group+1}.jpg',quality=92)
if __name__=='__main__':main()
