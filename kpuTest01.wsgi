import sys
import os

# 프로젝트 경로 추가
sys.path.insert(0, '/upload/kpuProject01')

# 가상환경의 site-packages 경로 설정
venv_path = '/upload/kpuProject01/myprojectenv/lib/python3.9/site-packages'
sys.path.insert(0, venv_path)

# Flask 애플리케이션 가져오기
from app import app as application

# 루트 경로 명시적으로 설정
application.root_path = os.path.dirname(os.path.abspath(__file__))