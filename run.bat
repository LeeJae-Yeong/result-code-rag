@echo off
echo 결과코드 RAG 시스템 실행 중...
echo.

REM 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

REM 의존성 설치
echo 의존성 설치 중...
pip install -r requirements.txt

echo.
echo Streamlit 애플리케이션 시작...
streamlit run app.py

pause
