"""
RAG 시스템 설정 파일
"""
import os

# 모델 설정
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
BM25_WEIGHT = 0.5  # BM25 가중치 (0.5~0.7 권장)
EMBEDDING_WEIGHT = 0.5  # 임베딩 가중치

# 검색 설정
TOP_K_RESULTS = 10  # 상위 K개 결과 반환
CONFIDENCE_THRESHOLD = 0.5  # 신뢰도 임계값

# 데이터 파일 경로
DATA_FILE = "data/result_codes.json"
