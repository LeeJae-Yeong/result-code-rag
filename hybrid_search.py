"""
Hybrid Search 구현 (임베딩 + BM25)
"""
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
import config

class HybridSearch:
    def __init__(self, data_file: str = None):
        """
        Hybrid Search 초기화
        
        Args:
            data_file: 결과코드 데이터 파일 경로
        """
        self.data_file = data_file or config.DATA_FILE # file 경로 
        self.data = self._load_data() # json load data/result_codes.json 읽기(없으면 빈 리스트 반환)
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL) # 임베딩 백터 생성
        self.bm25 = self._build_bm25() # 각 데이터 항목을 "결과코드 {code} {description}" 문자열로 합친 뒤 토큰화하여 BM25 인덱스 생성
        self.embeddings = self._build_embeddings() # 임베딩 백터 생성 (각 항목 문자열을 임베딩 모델로 인코딩하여 self.embeddings 에 저장)
        
    def _load_data(self) -> List[Dict]:
        """데이터 로드"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"데이터 파일을 찾을 수 없습니다: {self.data_file}")
            return []
    
    def _build_bm25(self) -> BM25Okapi:
        """BM25 인덱스 구축"""
        # 검색 가능한 텍스트 생성 (코드 + 설명)
        corpus = []
        for item in self.data:
            text = f"결과코드 {item['code']} {item['description']}"
            corpus.append(text)
        
        # 빈 데이터 처리
        if not corpus:
            # 빈 리스트로 BM25 인덱스 생성
            try:
                return BM25Okapi([[]])
            except Exception as e:
                print(f"빈 BM25 인덱스 생성 실패: {e}")
                # 더미 데이터로 인덱스 생성
                return BM25Okapi([["dummy"]])
        
        # 토큰화 (한국어, 영어, 숫자 혼합 처리)
        tokenized_corpus = [self._tokenize(text) for text in corpus]
        return BM25Okapi(tokenized_corpus)
    
    def _tokenize(self, text: str) -> List[str]:
        """텍스트 토큰화 (한국어, 영어, 숫자 혼합 처리)"""
        import re
        # 한국어, 영어, 숫자, 특수문자 분리
        tokens = re.findall(r'[가-힣]+|[a-zA-Z]+|\d+|[^\s]', text)
        return [token.lower() for token in tokens if token.strip()]
    
    def _build_embeddings(self) -> np.ndarray:
        """임베딩 벡터 구축"""
        texts = []
        for item in self.data:
            text = f"결과코드 {item['code']} {item['description']}"
            texts.append(text)
        
        # 빈 데이터 처리
        if not texts:
            # 빈 배열 반환
            return np.array([])
        
        return self.embedding_model.encode(texts)
    
    def search(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Hybrid Search 수행
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 수
            
        Returns:
            검색 결과 리스트 (score 내림차순 정렬)
        """
        if not self.data or len(self.data) == 0:
            return []
        
        top_k = top_k or config.TOP_K_RESULTS
        
        # 쿼리 전처리
        processed_query = self._preprocess_query(query)
        
        # BM25 점수 계산
        bm25_scores = self._get_bm25_scores(processed_query)
        
        # 임베딩 유사도 계산
        embedding_scores = self._get_embedding_scores(processed_query)
        
        # Hybrid 점수 계산 (가중 평균)
        hybrid_scores = self._calculate_hybrid_scores(bm25_scores, embedding_scores)
        
        # 결과 생성 및 정렬 (bm25/embedding 점수 접근 안전화)
        results = []
        bm25_len = len(bm25_scores)
        emb_len = len(embedding_scores)
        for i, score in enumerate(hybrid_scores):
            data_item = self.data[i] if i < len(self.data) else None
            if data_item:
                results.append({
                    'code': data_item['code'],
                    'description': data_item['description'],
                    'category': data_item.get('category', '기타'),
                    'score': float(score),
                    'bm25_score': float(bm25_scores[i]) if bm25_len > i else 0.0,
                    'embedding_score': float(embedding_scores[i]) if emb_len > i else 0.0
                })
        
        # score 내림차순 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 신뢰도 임계값 필터링
        filtered_results = [result for result in results if result['score'] >= config.CONFIDENCE_THRESHOLD]
        
        # 필터링된 결과가 있으면 그것을 반환, 없으면 상위 결과 반환
        if filtered_results:
            return filtered_results[:top_k]
        else:
            # 임계값을 만족하는 결과가 없으면 상위 1개라도 반환
            return results[:1] if results else []
    
    def _preprocess_query(self, query: str) -> str:
        """쿼리 전처리"""
        query = query.strip()
        
        # 숫자만 입력된 경우 (예: "4202")
        if query.isdigit():
            return f"결과코드 {query}"
        
        # "결과코드"가 포함된 짧은 쿼리 확장
        if len(query) < 15 and "결과코드" in query:
            return f"{query} 설명"
        
        # 특정 키워드가 포함된 경우 정확한 매칭을 위해 강화
        if any(keyword in query for keyword in ["트래픽", "초과", "인증", "실패", "시스템", "장애", "스팸"]):
            return query  # 정확한 키워드는 그대로 유지
        
        return query
    
    def _get_bm25_scores(self, query: str) -> np.ndarray:
        """BM25 점수 계산"""
        if len(self.data) == 0:
            return np.array([])
        
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        # 정규화 (0-1 범위)
        if len(scores) > 0 and scores.max() > 0:
            scores = scores / scores.max()
        return scores
    
    def _get_embedding_scores(self, query: str) -> np.ndarray:
        """임베딩 유사도 점수 계산"""
        if len(self.data) == 0 or len(self.embeddings) == 0:
            return np.array([])
        
        query_embedding = self.embedding_model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        return similarities
    
    def _calculate_hybrid_scores(self, bm25_scores: np.ndarray, embedding_scores: np.ndarray) -> np.ndarray:
        """Hybrid 점수 계산 (가중 평균)"""
        if len(bm25_scores) == 0 and len(embedding_scores) == 0:
            return np.array([])
        
        # 빈 배열 처리
        if len(bm25_scores) == 0:
            return embedding_scores
        if len(embedding_scores) == 0:
            return bm25_scores
        
        return (config.BM25_WEIGHT * bm25_scores + 
                config.EMBEDDING_WEIGHT * embedding_scores)
    
    def find_code_description(self, query: str) -> Dict:
        """
        결과코드 설명 검색 (규칙에 따른 출력 형식)
        
        Args:
            query: 검색 쿼리 (예: "결과코드 4007")
            
        Returns:
            규칙에 따른 출력 형식
        """
        results = self.search(query, top_k=1)
        
        if not results or results[0]['score'] < config.CONFIDENCE_THRESHOLD:
            # 코드 추출 시도
            code = self._extract_code_from_query(query)
            return {
                'code': code,
                'description': '해당 코드에 대한 정의가 없습니다.',
                'confidence': 0.0
            }
        
        best_result = results[0]
        return {
            'code': best_result['code'],
            'description': best_result['description'],
            'confidence': best_result['score']
        }
    
    def _extract_code_from_query(self, query: str) -> str:
        """쿼리에서 코드 추출"""
        import re
        # "결과코드 -4007" -> "-4007", "결과코드 4007" -> "4007"
        match = re.search(r'결과코드\s*(-?\d+)', query)
        if match:
            return match.group(1)
        
        # 숫자만 추출 (음수 기호 포함)
        numbers = re.findall(r'-?\d+', query)
        if numbers:
            return numbers[0]
        
        return query.strip()
