import sys
import os

# 프로젝트 경로 추가
sys.path.insert(0, '/upload/kpuProject01')

# 가상환경 경로 설정
activate_this = '/upload/kpuProject01/seoroApi.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

from app import app as application
