"""Run one named security case in an isolated PostgreSQL test database."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
from presentation_cases import CASES,CASE_BY_KEY

ROOT=Path(__file__).resolve().parent.parent

def receipt(case,records):
    good=sum(record['status']=='passed' for record in records)
    lines=[f'CASO: {case["title"]}',f'$ .venv/bin/python scripts/demo_case.py {case["key"]}',
           'Base separada: test_consultas_presentacion',
           f'Pruebas aprobadas: {good}/{len(records)}','']
    http=Counter()
    for record in records:
        for item in record['http']:http[(item['method'],item['path'],item['status'])]+=item['count']
    if http:
        lines.append('HTTP OBSERVADOS:')
        for (method,path,status),count in http.items():lines.append(f'  {method} {path} -> {status}  ({count})')
    if case['key'] in ['webhook','monto','cobros','concurrencia']:
        lines.append('ESTADOS FINALES OBSERVADOS:')
        for record in records:
            state=record['state']
            lines.append('  Citas: '+json.dumps(state.get('citas',{}),ensure_ascii=False))
            lines.append('  Pagos: '+json.dumps(state.get('pagos',{}),ensure_ascii=False))
            if case['key']=='cobros':lines.append(f'  Reembolsos: {state.get("reembolsos")}')
    for record in records:
        for key,value in record['details'].items():
            lines.append(f'{key}: '+(json.dumps(value,ensure_ascii=False) if isinstance(value,(dict,list)) else str(value)))
    if good==len(records) and records:
        lines+=['','RESULTADO: VERIFICADO',case['expected']]
    else:lines+=['','RESULTADO: HAY FALLOS. REVISAR EL LOG.']
    return '\n'.join(lines)+'\n'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case',choices=['all',*CASE_BY_KEY])
    args=parser.parse_args()
    selected=CASES if args.case=='all' else [CASE_BY_KEY[args.case]]
    output=ROOT/'evidence/presentacion'
    output.mkdir(exist_ok=True,parents=True)
    report_path=output/'ultima_ejecucion.json'
    env=dict(os.environ,DB_USER=os.environ.get('OWNER_USER','postgres'),DB_PASSWORD=os.environ.get('OWNER_PASSWORD',(ROOT/'.local/db-owner-password').read_text().strip()),PRESENTATION_REPORT_PATH=str(report_path))
    labels=list(dict.fromkeys(label for case in selected for label in case['tests']))
    command=[sys.executable,'manage.py','test',*labels,'--noinput','--testrunner','app.presentation_runner.CaptureRunner','-v','2']
    print('Ejecutando pruebas aisladas; conserva la base de citas. Espera el resultado...',flush=True)
    run=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True)
    log=output/f'ejecucion_{args.case}.log'
    log.write_text(run.stdout+'\n'+run.stderr)
    if run.returncode:
        print((run.stdout+'\n'+run.stderr)[-7000:])
        raise SystemExit(run.returncode)
    report=json.loads(report_path.read_text())
    manifest=[]
    for case in selected:
        records=[record for record in report['records'] if record['test'] in case['tests']]
        assert len(records)==len(case['tests']),case['key']
        actual=receipt(case,records)
        (output/f'{case["key"]}.txt').write_text(actual)
        detail={**case,'records':records,'run_at':report['run_at'],'passed':all(record['status']=='passed' for record in records),'receipt':actual}
        (output/f'{case["key"]}.json').write_text(json.dumps(detail,indent=2,ensure_ascii=False))
        manifest.append({'case':case['key'],'passed':detail['passed'],'tests':len(records)})
        print('\n'+actual)
    if args.case=='all':(output/'resumen.json').write_text(json.dumps({'run_at':report['run_at'],'cases':manifest,'passed':all(item['passed'] for item in manifest)},indent=2,ensure_ascii=False))

if __name__=='__main__':main()
