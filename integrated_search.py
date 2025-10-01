"""
결과코드와 FAQ 통합 검색 시스템
"""
from typing import Dict, List, Optional
from rag_system import RAGSystem
from faq_system import FAQSystem
import config

class IntegratedSearch:
    def __init__(self, rag_system: RAGSystem = None, faq_system: FAQSystem = None):
        """
        통합 검색 시스템 초기화
        
        Args:
            rag_system: 결과코드 RAG 시스템
            faq_system: FAQ 시스템
        """
        self.rag_system = rag_system or RAGSystem()
        self.faq_system = faq_system or FAQSystem()
    
    def search_all(self, query: str, top_k: int = None) -> Dict:
        """
        결과코드와 FAQ를 모두 검색하여 통합 결과 반환
        
        Args:
            query: 검색 쿼리
            top_k: 각 시스템별 반환할 상위 결과 수
            
        Returns:
            통합 검색 결과
        """
        try:
            top_k = top_k or config.TOP_K_RESULTS
            
            # 결과코드 검색
            code_results = self.rag_system.get_detailed_results(query, top_k)
            
            # FAQ 검색
            faq_results = self.faq_system.search_faq(query, top_k)
            
            # 결과 통합
            integrated_results = {
                'success': True,
                'query': query,
                'total_count': len(code_results) + len(faq_results.get('results', [])),
                'code_results': {
                    'count': len(code_results),
                    'results': code_results
                },
                'faq_results': {
                    'count': len(faq_results.get('results', [])),
                    'results': faq_results.get('results', [])
                },
                'message': f'결과코드 {len(code_results)}개, FAQ {len(faq_results.get("results", []))}개를 찾았습니다.'
            }
            
            return integrated_results
            
        except Exception as e:
            return {
                'success': False,
                'query': query,
                'total_count': 0,
                'code_results': {'count': 0, 'results': []},
                'faq_results': {'count': 0, 'results': []},
                'message': f'통합 검색 중 오류가 발생했습니다: {str(e)}'
            }
    
    def search_smart(self, query: str, top_k: int = None) -> Dict:
        """
        스마트 검색: 쿼리 유형을 분석하여 적절한 시스템에서 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 수
            
        Returns:
            스마트 검색 결과
        """
        try:
            top_k = top_k or config.TOP_K_RESULTS
            
            # 쿼리 유형 분석
            query_type = self._analyze_query_type(query)
            
            if query_type == 'code':
                # 결과코드 검색
                code_results = self.rag_system.get_detailed_results(query, top_k)
                return {
                    'success': True,
                    'query': query,
                    'query_type': query_type,
                    'results': code_results,
                    'total_count': len(code_results),
                    'message': f'결과코드 검색 결과 {len(code_results)}개를 찾았습니다.'
                }
            
            elif query_type == 'faq':
                # FAQ 검색
                faq_result = self.faq_system.search_faq(query, top_k)
                return {
                    'success': faq_result['success'],
                    'query': query,
                    'query_type': query_type,
                    'results': faq_result.get('results', []),
                    'total_count': len(faq_result.get('results', [])),
                    'message': faq_result['message']
                }
            
            else:
                # 통합 검색
                return self.search_all(query, top_k)
                
        except Exception as e:
            return {
                'success': False,
                'query': query,
                'query_type': 'unknown',
                'results': [],
                'total_count': 0,
                'message': f'스마트 검색 중 오류가 발생했습니다: {str(e)}'
            }
    
    def _analyze_query_type(self, query: str) -> str:
        """
        쿼리 유형 분석
        
        Args:
            query: 검색 쿼리
            
        Returns:
            쿼리 유형 ('code', 'faq', 'mixed')
        """
        import re
        
        query_lower = query.lower()
        
        # 결과코드 관련 키워드
        code_keywords = [
            '결과코드', '코드', '에러코드', '오류코드', '상태코드',
            'result code', 'error code', 'status code',
            '4007', '5000', '6000'  # 실제 코드 번호들
        ]
        
        # FAQ 관련 키워드
        faq_keywords = [
            '어떻게', '방법', '해결', '문제', '오류', '실패', '안돼', '못해',
            '왜', '이유', '원인', '확인', '체크', '설정', '등록',
            'how', 'why', 'what', 'solution', 'problem', 'error', 'help'
        ]
        
        # 숫자 패턴 (결과코드)
        has_code_number = bool(re.search(r'\b\d{3,5}\b', query))
        
        # 키워드 점수 계산
        code_score = sum(1 for keyword in code_keywords if keyword in query_lower)
        faq_score = sum(1 for keyword in faq_keywords if keyword in query_lower)
        
        # 점수 기반 판단
        if has_code_number or code_score > faq_score:
            return 'code'
        elif faq_score > 0 and code_score == 0:
            return 'faq'
        else:
            return 'mixed'
    
    def get_related_content(self, code: str = None, faq_id: str = None) -> Dict:
        """
        특정 결과코드나 FAQ와 관련된 내용 검색
        
        Args:
            code: 결과코드
            faq_id: FAQ ID
            
        Returns:
            관련 내용 검색 결과
        """
        try:
            results = {
                'success': True,
                'related_codes': [],
                'related_faqs': [],
                'message': ''
            }
            
            if code:
                # 결과코드로 관련 FAQ 검색
                all_faqs = self.faq_system.get_all_faqs()
                related_faqs = []
                
                for faq in all_faqs:
                    if code in faq.get('related_codes', []):
                        related_faqs.append(faq)
                
                results['related_faqs'] = related_faqs
                results['message'] += f'결과코드 {code}와 관련된 FAQ {len(related_faqs)}개를 찾았습니다. '
            
            if faq_id:
                # FAQ ID로 관련 결과코드 검색
                related_codes = self.faq_system.get_related_codes(faq_id)
                results['related_codes'] = related_codes
                results['message'] += f'FAQ {faq_id}와 관련된 결과코드 {len(related_codes)}개를 찾았습니다.'
            
            if not code and not faq_id:
                results['success'] = False
                results['message'] = '결과코드 또는 FAQ ID를 제공해주세요.'
            
            return results
            
        except Exception as e:
            return {
                'success': False,
                'related_codes': [],
                'related_faqs': [],
                'message': f'관련 내용 검색 중 오류가 발생했습니다: {str(e)}'
            }
    
    def search_by_category(self, category: str, query: str = "", search_type: str = "all") -> Dict:
        """
        카테고리별 통합 검색
        
        Args:
            category: 검색할 카테고리
            query: 검색 쿼리 (빈 문자열이면 전체 검색)
            search_type: 검색 타입 ('all', 'code', 'faq')
            
        Returns:
            카테고리별 검색 결과
        """
        try:
            results = {
                'success': True,
                'category': category,
                'query': query,
                'code_results': {'count': 0, 'results': []},
                'faq_results': {'count': 0, 'results': []},
                'total_count': 0,
                'message': ''
            }
            
            if search_type in ['all', 'code']:
                # 결과코드 카테고리 검색
                all_codes = self.rag_system.get_all_codes()
                filtered_codes = [code for code in all_codes if code.get('category') == category]
                
                if query:
                    # 쿼리가 있으면 필터링된 결과에서 검색
                    filtered_results = []
                    for code in filtered_codes:
                        if (query.lower() in code.get('code', '').lower() or 
                            query.lower() in code.get('description', '').lower()):
                            filtered_results.append(code)
                    results['code_results']['results'] = filtered_results
                else:
                    results['code_results']['results'] = filtered_codes
                
                results['code_results']['count'] = len(results['code_results']['results'])
            
            if search_type in ['all', 'faq']:
                # FAQ 카테고리 검색
                faq_result = self.faq_system.search_faq_by_category(category, query)
                results['faq_results'] = {
                    'count': len(faq_result.get('results', [])),
                    'results': faq_result.get('results', [])
                }
            
            results['total_count'] = results['code_results']['count'] + results['faq_results']['count']
            results['message'] = f'{category} 카테고리에서 결과코드 {results["code_results"]["count"]}개, FAQ {results["faq_results"]["count"]}개를 찾았습니다.'
            
            return results
            
        except Exception as e:
            return {
                'success': False,
                'category': category,
                'query': query,
                'code_results': {'count': 0, 'results': []},
                'faq_results': {'count': 0, 'results': []},
                'total_count': 0,
                'message': f'카테고리별 검색 중 오류가 발생했습니다: {str(e)}'
            }
    
    def get_search_suggestions(self, query: str, max_suggestions: int = 5) -> List[str]:
        """
        검색 제안 생성
        
        Args:
            query: 검색 쿼리
            max_suggestions: 최대 제안 수
            
        Returns:
            검색 제안 리스트
        """
        try:
            suggestions = []
            query_lower = query.lower()
            
            # 결과코드 제안
            all_codes = self.rag_system.get_all_codes()
            for code in all_codes:
                code_str = code.get('code', '')
                description = code.get('description', '')
                
                if (query_lower in code_str.lower() or 
                    query_lower in description.lower()):
                    suggestions.append(f"결과코드 {code_str}: {description}")
                    
                    if len(suggestions) >= max_suggestions:
                        break
            
            # FAQ 제안
            if len(suggestions) < max_suggestions:
                all_faqs = self.faq_system.get_all_faqs()
                for faq in all_faqs:
                    question = faq.get('question', '')
                    if query_lower in question.lower():
                        suggestions.append(f"FAQ: {question}")
                        
                        if len(suggestions) >= max_suggestions:
                            break
            
            return suggestions[:max_suggestions]
            
        except Exception as e:
            print(f"검색 제안 생성 실패: {e}")
            return []
    
    def get_popular_searches(self, limit: int = 10) -> Dict:
        """
        인기 검색어 반환
        
        Args:
            limit: 반환할 검색어 수
            
        Returns:
            인기 검색어 정보
        """
        try:
            # 결과코드 통계
            all_codes = self.rag_system.get_all_codes()
            code_categories = {}
            for code in all_codes:
                category = code.get('category', '기타')
                code_categories[category] = code_categories.get(category, 0) + 1
            
            # FAQ 통계
            faq_stats = self.faq_system.get_faq_statistics()
            
            # 인기 검색어 (우선순위 기반)
            popular_faqs = []
            all_faqs = self.faq_system.get_all_faqs()
            for faq in all_faqs:
                if faq.get('priority', 0) >= 2:  # 우선순위 2 이상
                    popular_faqs.append(faq['question'])
            
            return {
                'success': True,
                'popular_faq_questions': popular_faqs[:limit],
                'code_categories': code_categories,
                'faq_categories': faq_stats.get('categories', {}),
                'total_codes': len(all_codes),
                'total_faqs': faq_stats.get('total_faqs', 0)
            }
            
        except Exception as e:
            return {
                'success': False,
                'popular_faq_questions': [],
                'code_categories': {},
                'faq_categories': {},
                'total_codes': 0,
                'total_faqs': 0,
                'error': str(e)
            }


