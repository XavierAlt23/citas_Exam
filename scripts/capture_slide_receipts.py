"""Capture the actual CLI output of completed checks as legible slide images."""
from datetime import datetime
import html
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from presentation_cases import CASES

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'evidence/presentacion'
OUT=ROOT/'presentacion/capturas'
VIEWS=ROOT/'.local/presentation-receipts'

def main():
    OUT.mkdir(exist_ok=True,parents=True);VIEWS.mkdir(exist_ok=True,parents=True)
    manifest=[]
    with sync_playwright() as playwright:
        options={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
        brave=Path('/opt/brave.com/brave/brave')
        if brave.exists():options['executable_path']=str(brave)
        browser=playwright.chromium.launch(**options)
        context=browser.new_context(viewport={'width':1480,'height':960},offline=True,device_scale_factor=1)
        page=context.new_page()
        for number,case in enumerate(CASES,1):
            record=json.loads((SOURCE/f'{case["key"]}.json').read_text())
            assert record['passed'],case['key']
            output=(SOURCE/f'{case["key"]}.txt').read_text()
            stamp=datetime.fromisoformat(record['run_at']).astimezone().strftime('%d/%m/%Y %H:%M')
            markup='''<!doctype html><html lang="es"><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;padding:34px;background:#101f22;color:#edf5ef;font-family:"DejaVu Sans Mono",monospace}
header{display:flex;justify-content:space-between;gap:20px;border-bottom:1px solid #476269;padding-bottom:23px;color:#b7d4cc;font:24px "Noto Sans",sans-serif}
pre{margin:28px 0 0;white-space:pre-wrap;overflow-wrap:anywhere;font:27px/1.42 "DejaVu Sans Mono",monospace}
footer{margin-top:28px;border-top:1px solid #476269;padding-top:18px;color:#bdd4ca;font:20px "Noto Sans",sans-serif}
</style><header><span>Salida real del comando · Prueba automatizada</span><span>'''+html.escape(stamp)+'''</span></header><pre>'''+html.escape(output)+'''</pre><footer>Datos sintéticos · Base separada de la aplicación · El texto proviene de la ejecución guardada.</footer></html>'''
            view=VIEWS/f'{case["key"]}.html';view.write_text(markup)
            page.goto(view.as_uri(),wait_until='load')
            size=page.evaluate('({width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight})')
            assert size['width']==1480
            filename=f'{number:02d}_{case["key"]}.png'
            page.screenshot(path=str(OUT/filename),full_page=True)
            manifest.append({'case':case['key'],'capture':filename,'source':f'evidence/presentacion/{case["key"]}.txt','run_at':record['run_at'],'kind':'Captura de salida real de prueba automatizada; no es una captura de la ventana del aplicativo.'})
        context.close();browser.close()
    (OUT/'fuentes.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
    print(f'{len(manifest)} capturas generadas desde resultados reales.')

if __name__=='__main__':main()
