"""
FAQ 시스템 메인 클래스
FAQ 검색, 관리, 통합 기능 제공
"""
from faq_search import FAQSearch
from typing import Dict, List, Optional
import config

class FAQSystem:
    def __init__(self, faq_data_file: str = "data/faq_data.json"):
        """
        FAQ 시스템 초기화
        
        Args:
            faq_data_file: FAQ 데이터 파일 경로
        """
        self.faq_search = FAQSearch(faq_data_file)
    
    def search_faq(self, query: str, top_k: int = None, confidence_threshold: float = 0.3) -> Dict:
        """
        FAQ 검색 수행
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 수
            confidence_threshold: 신뢰도 임계값
            
        Returns:
            검색 결과
        """
        try:
            # FAQ 검색 수행
            results = self.faq_search.search(query, top_k, confidence_threshold)
            
            if results:
                return {
                    'success': True,
                    'query': query,
                    'results': results,
                    'total_count': len(results),
                    'message': f'{len(results)}개의 FAQ를 찾았습니다.'
                }
            else:
                return {
                    'success': False,
                    'query': query,
                    'results': [],
                    'total_count': 0,
                    'message': '관련 FAQ를 찾을 수 없습니다.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'query': query,
                'results': [],
                'total_count': 0,
                'message': f'FAQ 검색 중 오류가 발생했습니다: {str(e)}'
            }
    
    def search_faq_by_category(self, category: str, query: str = "", top_k: int = None) -> Dict:
        """
        카테고리별 FAQ 검색
        
        Args:
            category: 검색할 카테고리
            query: 검색 쿼리 (빈 문자열이면 전체 검색)
            top_k: 반환할 상위 결과 수
            
        Returns:
            카테고리별 검색 결과
        """
        try:
            results = self.faq_search.search_by_category(category, query, top_k)
            
            if results:
                return {
                    'success': True,
                    'category': category,
                    'query': query,
                    'results': results,
                    'total_count': len(results),
                    'message': f'{category} 카테고리에서 {len(results)}개의 FAQ를 찾았습니다.'
                }
            else:
                return {
                    'success': False,
                    'category': category,
                    'query': query,
                    'results': [],
                    'total_count': 0,
                    'message': f'{category} 카테고리에서 관련 FAQ를 찾을 수 없습니다.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'category': category,
                'query': query,
                'results': [],
                'total_count': 0,
                'message': f'카테고리별 FAQ 검색 중 오류가 발생했습니다: {str(e)}'
            }
    
    def get_faq_by_id(self, faq_id: str) -> Dict:
        """
        ID로 FAQ 조회
        
        Args:
            faq_id: 조회할 FAQ ID
            
        Returns:
            FAQ 정보
        """
        try:
            faq = self.faq_search.get_faq_by_id(faq_id)
            
            if faq:
                return {
                    'success': True,
                    'faq': faq,
                    'message': 'FAQ를 성공적으로 조회했습니다.'
                }
            else:
                return {
                    'success': False,
                    'faq': None,
                    'message': f'FAQ ID를 찾을 수 없습니다: {faq_id}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'faq': None,
                'message': f'FAQ 조회 중 오류가 발생했습니다: {str(e)}'
            }
    
    def get_all_faqs(self) -> List[Dict]:
        """모든 FAQ 목록 반환"""
        return self.faq_search.data
    
    def get_categories(self) -> List[str]:
        """모든 카테고리 목록 반환"""
        return self.faq_search.get_categories()
    
    def add_faq(self, faq_data: Dict) -> Dict:
        """
        새 FAQ 추가
        
        Args:
            faq_data: 추가할 FAQ 데이터
            
        Returns:
            추가 결과
        """
        try:
            success = self.faq_search.add_faq(faq_data)
            
            if success:
                return {
                    'success': True,
                    'faq_id': faq_data.get('id'),
                    'message': f'FAQ "{faq_data.get("question", "")}"가 성공적으로 추가되었습니다.'
                }
            else:
                return {
                    'success': False,
                    'faq_id': faq_data.get('id'),
                    'message': 'FAQ 추가에 실패했습니다.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'faq_id': faq_data.get('id'),
                'message': f'FAQ 추가 중 오류가 발생했습니다: {str(e)}'
            }
    
    def update_faq(self, faq_id: str, update_data: Dict) -> Dict:
        """
        FAQ 수정
        
        Args:
            faq_id: 수정할 FAQ ID
            update_data: 수정할 데이터
            
        Returns:
            수정 결과
        """
        try:
            success = self.faq_search.update_faq(faq_id, update_data)
            
            if success:
                return {
                    'success': True,
                    'faq_id': faq_id,
                    'message': f'FAQ ID "{faq_id}"가 성공적으로 수정되었습니다.'
                }
            else:
                return {
                    'success': False,
                    'faq_id': faq_id,
                    'message': f'FAQ ID "{faq_id}" 수정에 실패했습니다.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'faq_id': faq_id,
                'message': f'FAQ 수정 중 오류가 발생했습니다: {str(e)}'
            }
    
    def delete_faq(self, faq_id: str) -> Dict:
        """
        FAQ 삭제
        
        Args:
            faq_id: 삭제할 FAQ ID
            
        Returns:
            삭제 결과
        """
        try:
            success = self.faq_search.delete_faq(faq_id)
            
            if success:
                return {
                    'success': True,
                    'faq_id': faq_id,
                    'message': f'FAQ ID "{faq_id}"가 성공적으로 삭제되었습니다.'
                }
            else:
                return {
                    'success': False,
                    'faq_id': faq_id,
                    'message': f'FAQ ID "{faq_id}" 삭제에 실패했습니다.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'faq_id': faq_id,
                'message': f'FAQ 삭제 중 오류가 발생했습니다: {str(e)}'
            }
    
    def get_related_codes(self, faq_id: str) -> List[str]:
        """FAQ와 관련된 결과코드 목록 반환"""
        return self.faq_search.get_related_codes(faq_id)
    
    def get_faq_statistics(self) -> Dict:
        """FAQ 통계 정보 반환"""
        try:
            all_faqs = self.get_all_faqs()
            
            # 카테고리별 통계
            category_stats = {}
            for faq in all_faqs:
                category = faq.get('category', '기타')
                category_stats[category] = category_stats.get(category, 0) + 1
            
            # 우선순위별 통계
            priority_stats = {}
            for faq in all_faqs:
                priority = faq.get('priority', 0)
                priority_stats[priority] = priority_stats.get(priority, 0) + 1
            
            # 태그 통계
            tag_stats = {}
            for faq in all_faqs:
                tags = faq.get('tags', [])
                for tag in tags:
                    tag_stats[tag] = tag_stats.get(tag, 0) + 1
            
            return {
                'total_faqs': len(all_faqs),
                'categories': category_stats,
                'priorities': priority_stats,
                'popular_tags': dict(sorted(tag_stats.items(), key=lambda x: x[1], reverse=True)[:10])
            }
            
        except Exception as e:
            return {
                'total_faqs': 0,
                'categories': {},
                'priorities': {},
                'popular_tags': {},
                'error': str(e)
            }
    
    def search_similar_faqs(self, faq_id: str, top_k: int = 5) -> List[Dict]:
        """
        특정 FAQ와 유사한 FAQ 검색
        
        Args:
            faq_id: 기준이 될 FAQ ID
            top_k: 반환할 상위 결과 수
            
        Returns:
            유사한 FAQ 목록
        """
        try:
            # 기준 FAQ 조회
            base_faq = self.faq_search.get_faq_by_id(faq_id)
            if not base_faq:
                return []
            
            # 기준 FAQ의 질문으로 검색
            query = base_faq['question']
            results = self.faq_search.search(query, top_k + 1)  # +1은 자기 자신 제외용
            
            # 자기 자신 제외
            similar_faqs = [faq for faq in results if faq['id'] != faq_id]
            
            return similar_faqs[:top_k]
            
        except Exception as e:
            print(f"유사 FAQ 검색 실패: {e}")
            return []
    
    def export_faqs(self, category: str = None) -> List[Dict]:
        """
        FAQ 데이터 내보내기
        
        Args:
            category: 특정 카테고리만 내보내기 (None이면 전체)
            
        Returns:
            내보낼 FAQ 목록
        """
        try:
            all_faqs = self.get_all_faqs()
            
            if category:
                filtered_faqs = [faq for faq in all_faqs if faq.get('category') == category]
                return filtered_faqs
            else:
                return all_faqs
                
        except Exception as e:
            print(f"FAQ 내보내기 실패: {e}")
            return []
    
    def import_faqs(self, faq_list: List[Dict], overwrite: bool = False) -> Dict:
        """
        FAQ 데이터 가져오기
        
        Args:
            faq_list: 가져올 FAQ 목록
            overwrite: 기존 FAQ 덮어쓰기 여부
            
        Returns:
            가져오기 결과
        """
        try:
            imported_count = 0
            skipped_count = 0
            error_count = 0
            
            for faq_data in faq_list:
                try:
                    # 필수 필드 검증
                    if 'id' not in faq_data or 'question' not in faq_data or 'answer' not in faq_data:
                        error_count += 1
                        continue
                    
                    # 중복 체크
                    existing_faq = self.faq_search.get_faq_by_id(faq_data['id'])
                    if existing_faq and not overwrite:
                        skipped_count += 1
                        continue
                    
                    # FAQ 추가/수정
                    if existing_faq and overwrite:
                        success = self.faq_search.update_faq(faq_data['id'], faq_data)
                    else:
                        success = self.faq_search.add_faq(faq_data)
                    
                    if success:
                        imported_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    print(f"FAQ 가져오기 실패 (ID: {faq_data.get('id', 'unknown')}): {e}")
                    error_count += 1
            
            return {
                'success': True,
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'error_count': error_count,
                'total_count': len(faq_list),
                'message': f'{imported_count}개 가져오기 성공, {skipped_count}개 건너뛰기, {error_count}개 오류'
            }
            
        except Exception as e:
            return {
                'success': False,
                'imported_count': 0,
                'skipped_count': 0,
                'error_count': len(faq_list),
                'total_count': len(faq_list),
                'message': f'FAQ 가져오기 중 오류가 발생했습니다: {str(e)}'
            }
    
    def reload_data(self) -> bool:
        """FAQ 데이터 재로드"""
        return self.faq_search.reload_data()


