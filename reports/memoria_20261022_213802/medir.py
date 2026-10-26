"""Medición local de Windows; no entrena ni usa s007 ni solicita audio a Google."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import platform
import socket
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'

class Counters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in (
            'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
            'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]

kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.GetCurrentProcess.restype = wintypes.HANDLE
psapi = ctypes.WinDLL('psapi', use_last_error=True)
psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
stages = []
started = time.perf_counter()
report = {'platform': platform.platform(), 'python': sys.version, 'pid': os.getpid(),
          'scope': 'Un proceso local Windows, servidor Gradio e inferencia secuencial; sin gTTS ni s007',
          'stages': stages}

def snapshot(stage):
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    result = dict(stage=stage, elapsed_seconds=round(time.perf_counter()-started, 2),
                  working_set_mib=round(counters.WorkingSetSize/2**20, 2),
                  peak_working_set_mib=round(counters.PeakWorkingSetSize/2**20, 2),
                  private_commit_mib=round(counters.PrivateUsage/2**20, 2),
                  peak_commit_mib=round(counters.PeakPagefileUsage/2**20, 2))
    stages.append(result)
    Path(__file__).with_name('resultado.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False), flush=True)

snapshot('python_inicial')
from reconocimiento_pictogramas import ui
snapshot('importar_interfaz')
app = ui.build_app()
snapshot('construir_gradio')
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
options = dict(theme=ui.accessible_theme(), css=ui.ACCESSIBLE_CSS, head=ui.APP_HEAD) if ui.GRADIO_MAJOR >= 6 else {}
try:
    app.launch(server_name='127.0.0.1', server_port=port, prevent_thread_lock=True, quiet=True, **options)
    snapshot('servidor_gradio_iniciado')
    from reconocimiento_pictogramas.inference import load_selected_model, load_selected_detector, classify_frame
    load_selected_model()
    snapshot('modelo_cargado')
    load_selected_detector()
    snapshot('detector_cargado')
    from PIL import Image
    config = json.loads((ROOT/'config/application.json').read_text(encoding='utf-8'))
    samples = [next((ROOT/'data/raw/known'/name).glob(f'{name}_s001_*.jpg')) for name in config['classes']]
    report['sample_paths'] = [p.relative_to(ROOT).as_posix() for p in samples]
    durations = []
    for repeat in range(3):
        for path in samples:
            tick = time.perf_counter()
            with Image.open(path) as image:
                result = classify_frame(image)
            durations.append(time.perf_counter()-tick)
            if len(durations) == 1:
                snapshot('primera_prediccion')
        snapshot(f'predicciones_{len(durations)}')
    report['prediction_seconds'] = durations
    time.sleep(5)
    snapshot('reposo_5_segundos')
    report['completed'] = True
finally:
    app.close()
    snapshot('servidor_cerrado')
