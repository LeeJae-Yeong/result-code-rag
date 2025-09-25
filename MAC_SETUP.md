# 🍎 Mac에서 결과코드 RAG 시스템 사용하기

## 📋 사전 요구사항

- **Python 3.8 이상** 설치 필요
- **Git** 설치 필요
- **터미널** 앱 사용

## 🚀 설치 및 실행 방법

### 1단계: 저장소 클론하기
```bash
# 터미널에서 실행
git clone https://github.com/LeeJae-Yeong/result-code-rag.git
cd result-code-rag
```

### 2단계: 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate
```

### 3단계: 필요한 패키지 설치
```bash
# requirements.txt의 패키지들 설치
pip install -r requirements.txt
```

### 4단계: 애플리케이션 실행
```bash
# Streamlit 앱 실행
streamlit run app.py
```

### 5단계: 웹브라우저에서 확인
- 터미널에 표시되는 URL로 접속 (보통 `http://localhost:8501`)
- 결과코드 질답 시스템 사용 시작!

## 🛠️ 문제 해결

### Python이 설치되지 않은 경우
```bash
# Homebrew로 Python 설치
brew install python3
```

### Git이 설치되지 않은 경우
```bash
# Homebrew로 Git 설치
brew install git
```

### 가상환경 활성화가 안 되는 경우
```bash
# 가상환경 비활성화 후 재활성화
deactivate
source venv/bin/activate
```

### 패키지 설치 오류가 발생하는 경우
```bash
# pip 업그레이드 후 재시도
pip install --upgrade pip
pip install -r requirements.txt
```

## 📁 프로젝트 구조

```
result-code-rag/
├── app.py                 # 메인 웹 애플리케이션
├── config.py              # 설정 파일
├── rag_system.py          # RAG 시스템 핵심 로직
├── hybrid_search.py       # 하이브리드 검색 엔진
├── pdf_parser.py          # PDF 파싱 모듈
├── excel_parser.py        # 엑셀 데이터 파싱 모듈
├── requirements.txt       # 필요한 Python 패키지 목록
├── run.sh                 # Mac/Linux 실행 스크립트
├── data/
│   └── result_codes.json  # 결과코드 데이터베이스
└── README.md              # 프로젝트 설명서
```

## 🎯 주요 기능

1. **결과코드 검색**: 코드 번호로 설명 검색
2. **PDF 업로드**: PDF에서 자동으로 결과코드 추출
3. **엑셀 데이터**: 엑셀에서 복사한 데이터 일괄 추가
4. **수동 추가**: 직접 코드와 설명 입력
5. **데이터 관리**: 기존 데이터 수정/삭제

## 🔧 개발자용 추가 명령어

### 가상환경 비활성화
```bash
deactivate
```

### 새로운 패키지 추가 후 requirements.txt 업데이트
```bash
pip freeze > requirements.txt
```

### Git 상태 확인
```bash
git status
```

### 변경사항 커밋
```bash
git add .
git commit -m "변경사항 설명"
git push origin main
```

## 📞 지원

문제가 발생하면 GitHub Issues에 문의해주세요!
- 저장소: https://github.com/LeeJae-Yeong/result-code-rag
- Issues: https://github.com/LeeJae-Yeong/result-code-rag/issues

---

**즐거운 결과코드 검색 되세요! 🎉**
