"""Build a direct deck: vulnerability, defense, command, action and evidence."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches,Pt
from PIL import Image,ImageFont
from presentation_cases import CASES

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'presentacion'
W,H=14.222222,8.0
PAPER,INK,TEAL,MUTED,PALE,WHITE,LINE='F7F9F6','19362F','174C3C','52655E','E6F0E9','FFFFFF','D6E0D8'
FONT,MONO='Noto Sans','DejaVu Sans Mono'
FONTS={}
ISSUES=[]

def color(value):return RGBColor.from_string(value)
def rect(slide,x,y,w,h,fill):
    shape=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
    shape.fill.solid();shape.fill.fore_color.rgb=color(fill);shape.line.fill.background()
    shape._element.spPr.append(OxmlElement('a:effectLst'))
    for element in shape._element.iter():
        if element.tag.endswith('effectRef'):element.set('idx','0')
    return shape

def font(face,size,bold):
    key=(face,size,bold)
    if key not in FONTS:
        path=subprocess.check_output(['fc-match','-f','%{file}',face+(':style=Bold' if bold else ':style=Regular')],text=True).strip()
        FONTS[key]=ImageFont.truetype(path,round(size*2))
    return FONTS[key]

def wrap(value,width,size,face,bold):
    f=font(face,size,bold);out=[]
    for line in str(value).split('\n'):
        current=''
        for word in line.split(' '):
            proposed=(current+' '+word).strip()
            if current and f.getlength(proposed)>width*144:
                out.append(current);current=word
            else:current=proposed
        out.append(current)
    return out

def text(slide,x,y,w,h,value,size=21,bold=False,fill=INK,face=FONT,minimum=None,align=PP_ALIGN.LEFT):
    minimum=minimum if minimum is not None else size-2
    lines=wrap(value,w,size,face,bold)
    while len(lines)*size*1.22/72+.03>h and size>minimum:
        size-=.5;lines=wrap(value,w,size,face,bold)
    if len(lines)*size*1.22/72+.03>h:ISSUES.append({'text':str(value)[:100],'font':size,'height':h,'lines':len(lines)})
    box=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
    tf=box.text_frame;tf.clear();tf.word_wrap=False
    tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    for index,line in enumerate(lines):
        p=tf.paragraphs[0] if index==0 else tf.add_paragraph()
        p.text=line;p.font.name=face;p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=color(fill)
        p.line_spacing=Pt(size*1.22);p.space_before=p.space_after=Pt(0);p.alignment=align
    return box

def picture(slide,path,x,y,w,h):
    with Image.open(path) as image:iw,ih=image.size
    factor=min(w/iw,h/ih);pw,ph=iw*factor,ih*factor
    slide.shapes.add_picture(str(path),Inches(x+(w-pw)/2),Inches(y+(h-ph)/2),width=Inches(pw),height=Inches(ph))

def base(prs,title,number,ref):
    slide=prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid();slide.background.fill.fore_color.rgb=color(PAPER)
    text(slide,.62,.45,13,.7,title,size=34,bold=True,minimum=30)
    text(slide,.66,1.19,12.7,.3,ref,size=12,fill=MUTED)
    rect(slide,.62,7.64,12.98,.012,LINE)
    text(slide,.65,7.76,11.5,.21,'CONSULTA CLARA · Datos sintéticos · Pruebas en base separada · Capturas de salida automatizada',size=9,minimum=9,fill=MUTED)
    text(slide,12.63,7.72,.95,.26,f'{number:02d}/21',size=11,minimum=11,fill=MUTED,align=PP_ALIGN.RIGHT)
    return slide

def section(slide,label,y,value,h=.78,size=20):
    text(slide,.68,y,5.95,.28,label,size=12,bold=True,fill=TEAL,minimum=12)
    text(slide,.68,y+.37,5.95,h,value,size=size,minimum=18)

def main():
    OUT.mkdir(exist_ok=True)
    captures=json.loads((OUT/'capturas/fuentes.json').read_text())
    images={item['case']:item for item in captures}
    report=json.loads((ROOT/'evidence/presentacion/resumen.json').read_text())
    assert report['passed'] and len(report['cases'])==20
    prs=Presentation();prs.slide_width=Inches(W);prs.slide_height=Inches(H)
    prs.core_properties.title='Consulta Clara · Vulnerabilidad, defensa, comando y captura'
    prs.core_properties.author='Consulta Clara · Defensa académica'
    prs.core_properties.subject='Veinte casos reproducibles con capturas de salida real'
    slide=base(prs,'Seguridad del aplicativo: prueba por prueba',1,'ESPE · Ingeniería de la Seguridad de Software')
    text(slide,.72,1.95,11.95,1.45,'Vulnerabilidad. Defensa.\nComando. Resultado. Captura.',size=40,bold=True,minimum=37)
    text(slide,.8,3.92,11.8,.85,'20 casos concretos para ejecutar y explicar.\nCada comando repite únicamente la prueba indicada.',size=25,minimum=23)
    rect(slide,.75,5.47,12.5,.92,TEAL)
    text(slide,1.02,5.67,11.95,.5,'.venv/bin/python scripts/demo_case.py NOMBRE_DEL_CASO',size=21,face=MONO,fill=WHITE,minimum=19)
    text(slide,.8,6.69,11.9,.5,'Docker debe estar abierto. Las capturas se generaron de las ejecuciones reales guardadas.',size=17,minimum=16,fill=MUTED)
    slide.notes_slide.notes_text_frame.text='Formato directo solicitado. Los casos se ejecutan en test_consultas_presentacion, una base de pruebas distinta de la aplicación. Los textos y estados de las capturas provienen de la ejecución real; se muestran como capturas del resultado automatizado, no como imágenes de ventanas del aplicativo. Los controles de privacidad y recuperación también forman parte de los 20 casos, aunque no son ataques directos.'
    guide=['# Pruebas de seguridad: comandos directos','\nAbre Docker Desktop. Desde la carpeta del proyecto ejecuta el comando del caso. Cada prueba usa datos sintéticos y otra base; no borra tus citas. La recuperación crea además una base restore_ nueva. Las capturas son imágenes de la salida real del comando, no de la interfaz del aplicativo.\n','```bash\n.venv/bin/python scripts/demo_case.py all\n```\nEste comando repite los 20 casos. Para exponer, utiliza uno a la vez.\n']
    for index,case in enumerate(CASES,2):
        capture=images[case['key']]
        data=json.loads((ROOT/f'evidence/presentacion/{case["key"]}.json').read_text())
        assert data['passed']
        stamp=datetime.fromisoformat(data['run_at']).astimezone().strftime('%d/%m/%Y %H:%M')
        slide=base(prs,case['title'],index,case['ref'])
        section(slide,'VULNERABILIDAD',1.63,case['vulnerability'],h=.74)
        section(slide,'CÓMO SE DEFENDIÓ',2.89,case['defense'],h=.77)
        text(slide,.68,4.16,5.95,.29,'COMANDO A EJECUTAR',size=12,bold=True,fill=TEAL,minimum=12)
        rect(slide,.65,4.56,6.0,.9,TEAL)
        command='.venv/bin/python \\\n  scripts/demo_case.py '+case['key']
        text(slide,.87,4.72,5.57,.62,command,size=18,face=MONO,fill=WHITE,minimum=17)
        section(slide,'QUÉ HARÁ',5.78,case['action'],h=.79,size=19)
        if case.get('limit'):text(slide,.7,7.12,5.9,.38,case['limit'],size=10.5,minimum=10,fill=MUTED)
        text(slide,7.03,1.63,6.52,.29,'CAPTURA DEL RESULTADO · '+stamp,size=12,bold=True,fill=TEAL,minimum=11)
        rect(slide,7.02,2.02,6.55,4.66,WHITE)
        picture(slide,OUT/'capturas'/capture['capture'],7.02,2.02,6.55,4.66)
        rect(slide,7.02,6.84,6.55,.72,PALE)
        text(slide,7.2,6.95,6.2,.56,case['expected'],size=16,bold=True,minimum=15)
        plain_command=f'.venv/bin/python scripts/demo_case.py {case["key"]}'
        note=f'Vulnerabilidad: {case["vulnerability"]}\nDefensa: {case["defense"]}\n\nCOMANDO:\n{plain_command}\n\nQUÉ HARÁ:\n{case["action"]}\n\nRESULTADO:\n{case["expected"]}\n\nCAPTURA: {capture["capture"]}\nFUENTE: {capture["source"]}\nFecha: {stamp}\n\n{case.get("limit", "")}'
        if case.get('manual'):note+='\n\nSi prefieres hacerlo en el aplicativo:\n'+case['manual']
        slide.notes_slide.notes_text_frame.text=note
        guide += [f'\n## {index-1:02d}. {case["title"]}',f'\n**Vulnerabilidad:** {case["vulnerability"]}',f'\n**Defensa:** {case["defense"]}',f'\n```bash\n{plain_command}\n```',f'\n**Qué hará:** {case["action"]}',f'\n**Qué observar:** {case["expected"]}',f'\n**Captura:** [ver imagen](capturas/{capture["capture"]}).']
        if case.get('manual'):guide+=[f'\n**Alternativa manual:** {case["manual"]}']
        if case.get('limit'):guide+=[f'\n**Alcance:** {case["limit"]}']
    pptx=OUT/'Pruebas_Seguridad.pptx';prs.save(pptx)
    (OUT/'COMANDOS_Y_PASOS.md').write_text('\n'.join(guide))
    (OUT/'verificacion.json').write_text(json.dumps({'slides':len(prs.slides),'cases':len(CASES),'screenshots':len(images),'all_cases_passed':report['passed'],'every_slide_has_notes':all(s.notes_slide.notes_text_frame.text for s in prs.slides),'layout_issues':ISSUES,'captured_at':report['run_at']},indent=2,ensure_ascii=False))
    print(json.dumps({'pptx':str(pptx),'slides':len(prs.slides),'capturas':len(images),'layout_issues':ISSUES},indent=2,ensure_ascii=False))

if __name__=='__main__':main()
