"""Additional evidence for slides; explicit tests, isolated from the live app DB."""
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlencode
from django.conf import settings
from django.test import TestCase, TransactionTestCase, override_settings
from app.tests import Fixtures
from app.services import sandbox_pay

@override_settings(SECURE_SSL_REDIRECT=False)
class EntryChecks(TestCase):
    def test_sql_login(self):
        response=self.client.post('/login/',urlencode({'username':"' OR 1=1--",'password':'synthetic-invalid-input'}),content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code,400)
        self.assertEqual(response.json()['error'],'Entrada bloqueada por el filtro de seguridad.')
        self.presentation_details={'mensaje':response.json()['error']}

    def test_xss_login(self):
        response=self.client.post('/login/',urlencode({'username':"<script>alert('XSS')</script>",'password':'synthetic-invalid-input'}),content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code,400)
        self.assertEqual(response.json()['error'],'Entrada bloqueada por el filtro de seguridad.')
        self.presentation_details={'mensaje':response.json()['error']}

    def test_rate_limit_301_requests(self):
        statuses=[]
        for _ in range(301):
            response=self.client.get('/login/')
            statuses.append(response.status_code)
        self.assertEqual(statuses.count(200),300)
        self.assertEqual(statuses[-1],429)
        self.assertEqual(response['Retry-After'],'60')
        self.presentation_details={'primeras_301':{'200':statuses.count(200),'429':statuses.count(429)},'Retry-After':response['Retry-After']}

    def test_secret_files_and_source(self):
        root=settings.BASE_DIR
        values={}
        for line in (root/'.env').read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key,value=line.split('=',1)
                if key in ['SECRET_KEY','FIELD_KEY','AUDIT_KEY','PSP_KEY','DB_PASSWORD'] or key.startswith('PARTNER_KEY_'):
                    self.assertGreater(len(value),20)
                    values[key]=value
        self.assertGreaterEqual(len(values),5)
        private=[root/'.env',root/'.local/db-owner-password',root/'.local/backup.key',root/'.local/tls-key.pem']
        for path in private:self.assertEqual(path.stat().st_mode & 0o077,0)
        gitignore=(root/'.gitignore').read_text()
        self.assertIn('.env',gitignore);self.assertIn('.local/',gitignore)
        matches=[];files=0
        for directory in ['app','config','templates','static','scripts']:
            for path in (root/directory).rglob('*'):
                if not path.is_file() or path.suffix not in ['.py','.html','.js','.css','.json','.txt']:continue
                files+=1
                body=path.read_text(errors='replace')
                for name,value in values.items():
                    if value in body:matches.append((str(path.relative_to(root)),name))
        self.assertEqual(matches,[])
        self.presentation_details={'archivos_fuente_revisados':files,'coincidencias_secretos':len(matches),'archivos_privados_verificados':len(private)}

class RecoveryCheck(Fixtures,TransactionTestCase):
    def test_encrypted_backup_and_restore(self):
        self.data()
        appointment=self.book();sandbox_pay(self.a,appointment.pk)
        root=settings.BASE_DIR
        db=settings.DATABASES['default']
        self.assertTrue(db['NAME'].startswith('test_consultas_presentacion'))
        private=root/'.local/presentation-recovery'
        private.mkdir(exist_ok=True,mode=0o700)
        env=dict(os.environ,DB_NAME=db['NAME'],DB_USER=db['USER'],DB_PASSWORD=db['PASSWORD'],BACKUP_DIR=str(private/'backups'),EVIDENCE_DIR=str(private/'evidence'))
        outputs=[]
        for action in ['backup','restore-drill']:
            result=subprocess.run([sys.executable,'scripts/backup.py',action],cwd=root,env=env,capture_output=True,text=True,timeout=90)
            self.assertEqual(result.returncode,0,result.stderr[-800:])
            outputs.append(json.loads(result.stdout))
        result=outputs[-1]
        self.assertTrue(result['checksum_verified']);self.assertTrue(result['audit_verified']);self.assertTrue(result['sessions_revoked'])
        self.assertEqual(result['mode'],'docker')
        self.assertEqual(result['restored_rows']['app_appointment'],1)
        self.assertEqual(result['restored_rows']['app_payment'],1)
        self.presentation_details={'checksum_verificado':True,'auditoria_verificada':True,'sesiones_revocadas':True,'citas_restauradas':1,'pagos_restaurados':1,'tiempo_restauracion_s':result['rto_seconds'],'modo':'Docker · base nueva'}
