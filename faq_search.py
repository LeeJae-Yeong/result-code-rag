"""
FAQ 전용 Hybrid Search 엔진
질문-답변 매칭을 위한 검색 시스템
"""
import json
import numpy as np
import re
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import config

class FAQSearch:
    def __init__(self, faq_data_file: str = "data/faq_data.json"):
        """
        FAQ 검색 엔진 초기화
        
        Args:
            faq_data_file: FAQ 데이터 파일 경로
        """
        self.faq_data_file = faq_data_file
        self.data = self._load_faq_data()
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        
        # 검색 인덱스 구축
        self.bm25 = self._build_bm25_index()
        self.embeddings = self._build_embeddings()
    
    def _load_faq_data(self) -> List[Dict]:
        """FAQ 데이터 로드"""
        try:
            with open(self.faq_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"FAQ 데이터 파일을 찾을 수 없습니다: {self.faq_data_file}")
            return []
        except Exception as e:
            print(f"FAQ 데이터 로드 실패: {e}")
            return []
    
    def _build_bm25_index(self) -> BM25Okapi:
        """BM25 인덱스 구축"""
        if not self.data:
            return None
        
        # FAQ 텍스트 토큰화
        faq_texts = []
        for item in self.data:
            # 질문 + 답변 + 태그를 하나의 텍스트로 결합
            combined_text = f"{item['question']} {item['answer']} {' '.join(item.get('tags', []))}"
            tokens = self._tokenize(combined_text)
            faq_texts.append(tokens)
        
        return BM25Okapi(faq_texts)
    
    def _build_embeddings(self) -> np.ndarray:
        """임베딩 벡터 구축"""
        if not self.data:
            return np.array([])
        
        # FAQ 텍스트 임베딩
        texts = []
        for item in self.data:
            # 질문과 답변을 결합하여 임베딩
            combined_text = f"{item['question']} {item['answer']}"
            texts.append(combined_text)
        
        embeddings = self.embedding_model.encode(texts)
        return embeddings
    
    def _tokenize(self, text: str) -> List[str]:
        """텍스트 토큰화 (한글, 영어, 숫자 지원) - 개선된 버전"""
        tokens = []
        
        # 1. 공백으로 먼저 분리
        words = text.split()
        
        for word in words:
            # 한글 단어 처리 (2글자 이상)
            if re.match(r'^[가-힣]{2,}$', word):
                tokens.append(word)
                
                # 3글자 이상인 경우 2글자 조합도 추가 (예: "스팸차단" -> "스팸차단", "스팸", "차단")
                if len(word) >= 3:
                    for i in range(len(word) - 1):
                        sub_word = word[i:i+2]
                        if sub_word not in tokens:
                            tokens.append(sub_word)
            
            # 영어 단어는 소문자로 변환
            elif re.match(r'^[a-zA-Z]{2,}$', word):
                tokens.append(word.lower())
            
            # 숫자는 그대로 유지
            elif re.match(r'^\d+$', word):
                tokens.append(word)
            # 혼합된 경우 더 세분화
            else:
                # 한글, 영어, 숫자로 분리
                mixed_tokens = re.findall(r'[가-힣]+|[a-zA-Z]+|\d+', word)
                tokens.extend([token.lower() if token.isalpha() else token for token in mixed_tokens if len(token) >= 2])
        
        return tokens
    
    def search(self, query: str, top_k: int = None, confidence_threshold: float = 0.3) -> List[Dict]:
        """
        FAQ 검색 수행
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 수
            confidence_threshold: 신뢰도 임계값 (이 값보다 낮은 결과는 제외)
            
        Returns:
            검색 결과 리스트
        """
        if not self.data:
            return []
        
        top_k = top_k or config.TOP_K_RESULTS
        
        # 쿼리 전처리
        processed_query = self._preprocess_query(query)
        
        # 빈 쿼리나 너무 짧은 쿼리 처리
        if not processed_query or len(processed_query.strip()) < 2:
            return []
        
        # BM25 검색
        bm25_scores = self._get_bm25_scores(processed_query)
        
        # 임베딩 검색
        embedding_scores = self._get_embedding_scores(processed_query)
        
        # 하이브리드 점수 계산
        hybrid_scores = self._calculate_hybrid_scores(bm25_scores, embedding_scores)
        
        # 디버깅 정보 출력
        print(f"[FAQ 검색] 쿼리: '{processed_query}'")
        print(f"[FAQ 검색] 토큰: {self._tokenize(processed_query)}")
        print(f"[FAQ 검색] BM25 점수 범위: {bm25_scores.min():.3f} ~ {bm25_scores.max():.3f}")
        print(f"[FAQ 검색] 임베딩 점수 범위: {embedding_scores.min():.3f} ~ {embedding_scores.max():.3f}")
        print(f"[FAQ 검색] 하이브리드 점수 범위: {hybrid_scores.min():.3f} ~ {hybrid_scores.max():.3f}")
        print(f"[FAQ 검색] 임계값: {confidence_threshold}")
        
        # 결과 생성 및 임계값 필터링
        results = []
        for i, score in enumerate(hybrid_scores):
            if i < len(self.data) and score >= confidence_threshold:
                item = self.data[i]
                
                # 키워드 정확도 필터링 추가
                if self._is_relevant_result(query, item):
                    results.append({
                        'id': item['id'],
                        'question': item['question'],
                        'answer': item['answer'],
                        'category': item['category'],
                        'tags': item.get('tags', []),
                        'related_codes': item.get('related_codes', []),
                        'priority': item.get('priority', 0),
                        'score': float(score),
                        'bm25_score': float(bm25_scores[i]) if len(bm25_scores) > i else 0.0,
                        'embedding_score': float(embedding_scores[i]) if len(embedding_scores) > i else 0.0
                    })
        
        # 점수 기준으로 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:top_k]
    
    def _preprocess_query(self, query: str) -> str:
        """쿼리 전처리"""
        # 기본 전처리
        query = query.strip()
        
        # 자연어 쿼리를 FAQ 검색에 적합하게 변환
        query = query.replace('?', '').replace('!', '')
        
        # 키워드 강화는 제거 (일반적인 검색 방식 사용)
        
        return query
    
    def _is_relevant_result(self, original_query: str, item: dict) -> bool:
        """검색 결과가 원본 쿼리와 관련이 있는지 확인 (개선된 버전)"""
        original_query = original_query.lower().strip()
        
        # 검색할 텍스트 (질문 + 답변 + 태그)
        search_text = f"{item['question']} {item['answer']} {' '.join(item.get('tags', []))}".lower()
        
        # 쿼리 토큰화
        query_tokens = set(self._tokenize(original_query))
        search_tokens = set(self._tokenize(search_text))
        
        # 최소 1개 이상의 토큰이 매칭되어야 함
        common_tokens = query_tokens.intersection(search_tokens)
        
        # 의미있는 토큰이 1개 이상 매칭되면 관련성이 있다고 판단
        if len(common_tokens) > 0:
            return True
        
        # 추가: 부분 문자열 매칭 (공백 없는 경우 대비)
        # 예: "스팸차단" -> "스팸", "차단" 각각이 검색 텍스트에 있는지 확인
        for query_token in query_tokens:
            if len(query_token) >= 2:
                # 토큰의 2글자 조합이 검색 텍스트에 포함되어 있는지 확인
                for i in range(len(query_token) - 1):
                    sub_token = query_token[i:i+2]
                    if sub_token in search_text:
                        return True
        
        return False
    
    def _get_bm25_scores(self, query: str) -> np.ndarray:
        """BM25 점수 계산"""
        if not self.bm25:
            return np.array([])
        
        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)
        
        # 점수 정규화 (Min-Max 정규화)
        if len(scores) > 0:
            min_score = np.min(scores)
            max_score = np.max(scores)
            if max_score > min_score:
                scores = (scores - min_score) / (max_score - min_score)
            else:
                scores = np.zeros_like(scores)
        
        return scores
    
    def _get_embedding_scores(self, query: str) -> np.ndarray:
        """임베딩 기반 유사도 점수 계산"""
        if len(self.embeddings) == 0:
            return np.array([])
        
        # 쿼리 임베딩
        query_embedding = self.embedding_model.encode([query])
        
        # 코사인 유사도 계산
        similarities = np.dot(self.embeddings, query_embedding.T).flatten()
        
        # Min-Max 정규화로 0-1 범위로 변환
        if len(similarities) > 0:
            min_sim = np.min(similarities)
            max_sim = np.max(similarities)
            if max_sim > min_sim:
                similarities = (similarities - min_sim) / (max_sim - min_sim)
            else:
                similarities = np.zeros_like(similarities)
        
        return similarities
    
    def _calculate_hybrid_scores(self, bm25_scores: np.ndarray, embedding_scores: np.ndarray) -> np.ndarray:
        """하이브리드 점수 계산 (BM25 + 임베딩)"""
        if len(bm25_scores) == 0 and len(embedding_scores) == 0:
            return np.array([])
        elif len(bm25_scores) == 0:
            return embedding_scores
        elif len(embedding_scores) == 0:
            return bm25_scores
        
        # 가중 평균 계산
        hybrid_scores = (config.BM25_WEIGHT * bm25_scores + 
                        config.EMBEDDING_WEIGHT * embedding_scores)
        
        return hybrid_scores
    
    def search_by_category(self, category: str, query: str = "", top_k: int = None) -> List[Dict]:
        """
        카테고리별 FAQ 검색
        
        Args:
            category: 검색할 카테고리
            query: 검색 쿼리 (빈 문자열이면 전체 검색)
            top_k: 반환할 상위 결과 수
            
        Returns:
            카테고리별 검색 결과
        """
        if not self.data:
            return []
        
        # 카테고리 필터링
        filtered_data = [item for item in self.data if item['category'] == category]
        
        if not filtered_data:
            return []
        
        # 임시로 필터링된 데이터로 검색 수행
        original_data = self.data
        self.data = filtered_data
        
        try:
            # 인덱스 재구축
            self.bm25 = self._build_bm25_index()
            self.embeddings = self._build_embeddings()
            
            # 검색 수행
            if query:
                results = self.search(query, top_k)
            else:
                # 쿼리가 없으면 우선순위 순으로 정렬
                results = []
                for item in filtered_data:
                    results.append({
                        'id': item['id'],
                        'question': item['question'],
                        'answer': item['answer'],
                        'category': item['category'],
                        'tags': item.get('tags', []),
                        'related_codes': item.get('related_codes', []),
                        'priority': item.get('priority', 0),
                        'score': float(item.get('priority', 0)) / 3.0,  # 우선순위를 점수로 변환
                        'bm25_score': 0.0,
                        'embedding_score': 0.0
                    })
                results.sort(key=lambda x: x['score'], reverse=True)
                if top_k:
                    results = results[:top_k]
            
            return results
            
        finally:
            # 원본 데이터 복원
            self.data = original_data
            self.bm25 = self._build_bm25_index()
            self.embeddings = self._build_embeddings()
    
    def get_faq_by_id(self, faq_id: str) -> Optional[Dict]:
        """ID로 FAQ 조회"""
        for item in self.data:
            if item['id'] == faq_id:
                return item
        return None
    
    def get_categories(self) -> List[str]:
        """모든 카테고리 목록 반환"""
        categories = set()
        for item in self.data:
            categories.add(item['category'])
        return sorted(list(categories))
    
    def get_related_codes(self, faq_id: str) -> List[str]:
        """FAQ와 관련된 결과코드 목록 반환"""
        faq = self.get_faq_by_id(faq_id)
        if faq:
            return faq.get('related_codes', [])
        return []
    
    def _generate_next_faq_id(self) -> str:
        """
        다음 FAQ ID 자동 생성
        
        Returns:
            새로운 FAQ ID (faq_XXX 형식)
        """
        if not self.data:
            return "faq_001"
        
        # 기존 ID에서 최대 번호 찾기
        max_num = 0
        for item in self.data:
            if item['id'].startswith('faq_'):
                try:
                    num = int(item['id'][4:])  # 'faq_' 이후 부분을 숫자로 변환
                    max_num = max(max_num, num)
                except ValueError:
                    continue
        
        # 다음 번호 생성
        next_num = max_num + 1
        return f"faq_{next_num:03d}"

    def add_faq(self, faq_data: Dict) -> bool:
        """
        새 FAQ 추가
        
        Args:
            faq_data: 추가할 FAQ 데이터
            
        Returns:
            추가 성공 여부
        """
        try:
            # ID가 없으면 자동 생성
            if 'id' not in faq_data or not faq_data['id']:
                faq_data['id'] = self._generate_next_faq_id()
            
            # 필수 필드 검증 (ID 제외)
            required_fields = ['question', 'answer', 'category']
            for field in required_fields:
                if field not in faq_data:
                    print(f"필수 필드 누락: {field}")
                    return False
            
            # 중복 ID 체크
            for item in self.data:
                if item['id'] == faq_data['id']:
                    print(f"중복된 FAQ ID: {faq_data['id']}")
                    return False
            
            # 기본값 설정
            if 'tags' not in faq_data:
                faq_data['tags'] = []
            if 'related_codes' not in faq_data:
                faq_data['related_codes'] = []
            if 'priority' not in faq_data:
                faq_data['priority'] = 0
            if 'created_date' not in faq_data:
                from datetime import datetime
                faq_data['created_date'] = datetime.now().strftime('%Y-%m-%d')
            if 'updated_date' not in faq_data:
                faq_data['updated_date'] = faq_data['created_date']
            
            # FAQ 추가
            self.data.append(faq_data)
            
            # 인덱스 재구축
            self.bm25 = self._build_bm25_index()
            self.embeddings = self._build_embeddings()
            
            # 데이터 저장
            self.save_faq_data()
            
            return True
            
        except Exception as e:
            print(f"FAQ 추가 실패: {e}")
            return False
    
    def update_faq(self, faq_id: str, update_data: Dict) -> bool:
        """
        FAQ 수정
        
        Args:
            faq_id: 수정할 FAQ ID
            update_data: 수정할 데이터
            
        Returns:
            수정 성공 여부
        """
        try:
            for i, item in enumerate(self.data):
                if item['id'] == faq_id:
                    # 업데이트 날짜 설정
                    from datetime import datetime
                    update_data['updated_date'] = datetime.now().strftime('%Y-%m-%d')
                    
                    # 기존 데이터 업데이트
                    self.data[i].update(update_data)
                    
                    # 인덱스 재구축
                    self.bm25 = self._build_bm25_index()
                    self.embeddings = self._build_embeddings()
                    
                    # 데이터 저장
                    self.save_faq_data()
                    
                    return True
            
            print(f"FAQ ID를 찾을 수 없습니다: {faq_id}")
            return False
            
        except Exception as e:
            print(f"FAQ 수정 실패: {e}")
            return False
    
    def delete_faq(self, faq_id: str) -> bool:
        """
        FAQ 삭제
        
        Args:
            faq_id: 삭제할 FAQ ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            original_length = len(self.data)
            self.data = [item for item in self.data if item['id'] != faq_id]
            
            if len(self.data) < original_length:
                # 인덱스 재구축
                self.bm25 = self._build_bm25_index()
                self.embeddings = self._build_embeddings()
                
                # 데이터 저장
                self.save_faq_data()
                return True
            else:
                print(f"FAQ ID를 찾을 수 없습니다: {faq_id}")
                return False
                
        except Exception as e:
            print(f"FAQ 삭제 실패: {e}")
            return False
    
    def save_faq_data(self) -> bool:
        """FAQ 데이터 저장"""
        try:
            with open(self.faq_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"FAQ 데이터 저장 실패: {e}")
            return False
    
    def reload_data(self) -> bool:
        """FAQ 데이터 재로드"""
        try:
            self.data = self._load_faq_data()
            self.bm25 = self._build_bm25_index()
            self.embeddings = self._build_embeddings()
            return True
        except Exception as e:
            print(f"FAQ 데이터 재로드 실패: {e}")
            return False


