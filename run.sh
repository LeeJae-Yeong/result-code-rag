#!/bin/bash

echo "결과코드 RAG 시스템 실행 중..."
echo

# 가상환경 활성화 (있는 경우)
if [ -f "venv/bin/activate" ]; then
    echo "가상환경 활성화 중..."
    source venv/bin/activate
fi

# 의존성 설치
echo "의존성 설치 중..."
pip install -r requirements.txt

echo
echo "Streamlit 애플리케이션 시작..."
streamlit run app.py
