"""Collect observed HTTP statuses and model states, without request secrets."""
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
import unittest
from unittest.mock import patch
from django.conf import settings
from django.db import connections
from django.test import Client
from django.test.runner import DiscoverRunner

RECORDS=[]

class CaptureResult(unittest.TextTestResult):
    def startTest(self,test):
        self.started=time.perf_counter();self.http=Counter()
        original=Client.request
        observed=self.http
        def request(client,**kwargs):
            response=original(client,**kwargs)
            path=re.sub(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}','UUID',kwargs.get('PATH_INFO','/'))
            observed[(kwargs.get('REQUEST_METHOD','GET'),path,response.status_code)]+=1
            return response
        self.patcher=patch.object(Client,'request',request)
        self.patcher.start();super().startTest(test)

    def stopTest(self,test):
        self.patcher.stop();super().stopTest(test)

    def capture(self,test,status):
        from app.models import Appointment,Payment,Refund,Representation
        state={}
        try:
            state={'citas':dict(Counter(Appointment.objects.values_list('status',flat=True))),'pagos':dict(Counter(Payment.objects.values_list('status',flat=True))),'reembolsos':Refund.objects.count(),'vinculos_verificados':Representation.objects.filter(verified_at__isnull=False).count()}
        except Exception:
            state={'snapshot':'no disponible al finalizar este caso'}
        RECORDS.append({'test':test.id(),'status':status,'seconds':round(time.perf_counter()-self.started,3),'http':[{'method':method,'path':path,'status':code,'count':count} for (method,path,code),count in self.http.items()],'state':state,'details':getattr(test,'presentation_details',{})})

    def addSuccess(self,test):
        super().addSuccess(test);self.capture(test,'passed')
    def addFailure(self,test,err):
        super().addFailure(test,err);self.capture(test,'failed')
    def addError(self,test,err):
        super().addError(test,err);self.capture(test,'error')

class CaptureRunner(DiscoverRunner):
    def setup_databases(self,**kwargs):
        name='test_consultas_presentacion'
        settings.DATABASES['default']['TEST']['NAME']=name
        connections['default'].settings_dict['TEST']['NAME']=name
        return super().setup_databases(**kwargs)
    def get_resultclass(self):return CaptureResult
    def suite_result(self,suite,result,**kwargs):
        path=Path(os.environ['PRESENTATION_REPORT_PATH'])
        path.parent.mkdir(exist_ok=True,parents=True)
        path.write_text(json.dumps({'passed':result.wasSuccessful(),'database':'PostgreSQL en Docker · test_consultas_presentacion','run_at':datetime.now(timezone.utc).isoformat(),'records':RECORDS},indent=2,ensure_ascii=False))
        return super().suite_result(suite,result,**kwargs)
