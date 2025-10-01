"""
RAG 시스템 설정 파일
"""
import os

# 모델 설정
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
BM25_WEIGHT = 0.6  # BM25 가중치 (키워드 매칭과 의미 검색 균형)
EMBEDDING_WEIGHT = 0.4  # 임베딩 가중치

# 검색 설정
TOP_K_RESULTS = 10  # 상위 K개 결과 반환
CONFIDENCE_THRESHOLD = 0.7  # 신뢰도 임계값 (더 정확한 관련성 필터링)

# 데이터 파일 경로
DATA_FILE = "data/result_codes.json"
