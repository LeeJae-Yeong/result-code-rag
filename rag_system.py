"""
RAG 시스템 메인 로직
규칙에 따른 결과코드 검색 및 설명 반환
"""
from hybrid_search import HybridSearch
from pdf_parser import PDFParser
from excel_parser import ExcelParser
from typing import Dict, List
import config

class RAGSystem:
    def __init__(self):
        """RAG 시스템 초기화"""
        self.hybrid_search = HybridSearch()
        self.pdf_parser = PDFParser()
        self.excel_parser = ExcelParser()
    
    def process_query(self, query: str) -> Dict:
        """
        사용자 쿼리 처리 (규칙에 따른 출력 형식)
        
        Args:
            query: 사용자 입력 쿼리
            
        Returns:
            규칙에 따른 출력 형식
        """
        # 쿼리 전처리
        processed_query = self._preprocess_query(query)
        
        # Hybrid Search 수행
        result = self.hybrid_search.find_code_description(processed_query)
        
        return result
    
    def process_query_with_duplicates(self, query: str) -> Dict:
        """
        사용자 쿼리 처리 (중복 코드 모두 반환)
        
        Args:
            query: 사용자 입력 쿼리
            
        Returns:
            중복 코드를 포함한 결과
        """
        # 쿼리 전처리
        processed_query = self._preprocess_query(query)
        
        # 코드 추출
        import re
        code_match = re.search(r'(\d+)', processed_query)
        if not code_match:
            return {
                'code': query,
                'descriptions': [],
                'confidence': 0.0,
                'message': '코드를 찾을 수 없습니다.'
            }
        
        target_code = code_match.group(1)
        
        # 해당 코드의 모든 설명 찾기
        matching_codes = []
        for item in self.hybrid_search.data:
            if item['code'] == target_code:
                matching_codes.append({
                    'description': item['description'],
                    'category': item.get('category', '기타')
                })
        
        if matching_codes:
            return {
                'code': target_code,
                'descriptions': matching_codes,
                'confidence': 1.0,
                'count': len(matching_codes)
            }
        else:
            return {
                'code': target_code,
                'descriptions': [],
                'confidence': 0.0,
                'message': '해당 코드에 대한 정의가 없습니다.'
            }
    
    def _preprocess_query(self, query: str) -> str:
        """쿼리 전처리"""
        query = query.strip()
        
        # "결과코드 4007" 형태로 정규화
        if not query.startswith("결과코드"):
            # 숫자가 포함된 경우 "결과코드" 추가
            import re
            if re.search(r'\d+', query):
                query = f"결과코드 {query}"
        
        return query
    
    def get_detailed_results(self, query: str, top_k: int = None) -> List[Dict]:
        """
        상세 검색 결과 반환 (디버깅 및 분석용)
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 수
            
        Returns:
            상세 검색 결과 리스트
        """
        processed_query = self._preprocess_query(query)
        return self.hybrid_search.search(processed_query, top_k)
    
    def get_all_codes(self) -> List[Dict]:
        """모든 결과코드 반환"""
        return self.hybrid_search.data
    
    def delete_code(self, code: str) -> bool:
        """
        특정 결과코드 삭제
        
        Args:
            code: 삭제할 결과코드
            
        Returns:
            삭제 성공 여부
        """
        try:
            # 코드 찾기
            original_length = len(self.hybrid_search.data)
            self.hybrid_search.data = [
                item for item in self.hybrid_search.data 
                if item['code'] != code
            ]
            
            # 삭제되었는지 확인
            if len(self.hybrid_search.data) < original_length:
                # 인덱스 재구축
                self.hybrid_search.bm25 = self.hybrid_search._build_bm25()
                self.hybrid_search.embeddings = self.hybrid_search._build_embeddings()
                
                # 데이터 저장
                self.save_data()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"코드 삭제 실패: {e}")
            return False
    
    def delete_all_codes(self) -> bool:
        """
        모든 결과코드 삭제
        
        Returns:
            삭제 성공 여부
        """
        try:
            # 데이터 삭제
            self.hybrid_search.data = []
            
            # 빈 인덱스 생성 (데이터가 비어있어도 안전하게 처리)
            self.hybrid_search.bm25 = self.hybrid_search._build_bm25()
            self.hybrid_search.embeddings = self.hybrid_search._build_embeddings()
            
            # 데이터 저장
            self.save_data()
            return True
            
        except Exception as e:
            print(f"전체 데이터 삭제 실패: {e}")
            return False
    
    def delete_codes_by_category(self, category: str) -> int:
        """
        특정 카테고리의 모든 결과코드 삭제
        
        Args:
            category: 삭제할 카테고리
            
        Returns:
            삭제된 코드 수
        """
        try:
            original_length = len(self.hybrid_search.data)
            self.hybrid_search.data = [
                item for item in self.hybrid_search.data 
                if item.get('category', '기타') != category
            ]
            
            deleted_count = original_length - len(self.hybrid_search.data)
            
            if deleted_count > 0:
                # 인덱스 재구축 (데이터가 비어있어도 안전하게 처리)
                self.hybrid_search.bm25 = self.hybrid_search._build_bm25()
                self.hybrid_search.embeddings = self.hybrid_search._build_embeddings()
                
                # 데이터 저장
                self.save_data()
            
            return deleted_count
            
        except Exception as e:
            print(f"카테고리별 삭제 실패: {e}")
            return 0
    
    def add_code(self, code: str, description: str, category: str = "기타", allow_duplicate: bool = False) -> bool:
        """
        새로운 결과코드 추가
        
        Args:
            code: 결과코드
            description: 설명
            category: 카테고리
            allow_duplicate: 중복 허용 여부
            
        Returns:
            성공 여부
        """
        try:
            # 기존 데이터에 추가
            new_code = {
                "code": code,
                "description": description,
                "category": category
            }
            
            # 중복 체크 (allow_duplicate가 False인 경우만)
            if not allow_duplicate:
                for item in self.hybrid_search.data:
                    if item['code'] == code:
                        return False
            
            self.hybrid_search.data.append(new_code)
            
            # 인덱스 재구축
            self.hybrid_search.bm25 = self.hybrid_search._build_bm25()
            self.hybrid_search.embeddings = self.hybrid_search._build_embeddings()
            
            return True
        except Exception as e:
            print(f"코드 추가 실패: {e}")
            return False
    
    def save_data(self) -> bool:
        """데이터 저장"""
        try:
            import json
            with open(config.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.hybrid_search.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"데이터 저장 실패: {e}")
            return False
    
    def upload_pdf(self, pdf_file, allow_duplicate: bool = False, manual_category: str = None) -> Dict:
        """
        PDF 파일 업로드 및 결과코드 추출
        
        Args:
            pdf_file: Streamlit UploadedFile 객체
            allow_duplicate: 중복 허용 여부
            manual_category: 선택된 카테고리 (None이면 '기타')
            
        Returns:
            업로드 결과 정보
        """
        try:
            # PDF에서 결과코드 추출
            extracted_codes = self.pdf_parser.parse_pdf(pdf_file)
            
            if not extracted_codes:
                return {
                    'success': False,
                    'message': 'PDF에서 결과코드를 찾을 수 없습니다.',
                    'extracted_count': 0
                }
            
            # 기존 데이터에 추가
            added_count = 0
            duplicate_count = 0
            
            for code in extracted_codes:
                # 중복 체크 (allow_duplicate가 False인 경우만)
                is_duplicate = False
                if not allow_duplicate:
                    is_duplicate = any(
                        item['code'] == code.code for item in self.hybrid_search.data
                    )
                
                if not is_duplicate:
                    # 수동 선택된 카테고리 사용
                    new_code = {
                        'code': code.code,
                        'description': code.description,
                        'category': manual_category or '기타'
                    }
                    self.hybrid_search.data.append(new_code)
                    added_count += 1
                else:
                    duplicate_count += 1
            
            # 인덱스 재구축
            self.hybrid_search.bm25 = self.hybrid_search._build_bm25()
            self.hybrid_search.embeddings = self.hybrid_search._build_embeddings()
            
            # 데이터 저장
            self.save_data()
            
            return {
                'success': True,
                'message': f'PDF에서 {len(extracted_codes)}개의 결과코드를 추출했습니다.',
                'extracted_count': len(extracted_codes),
                'added_count': added_count,
                'duplicate_count': duplicate_count,
                'extracted_codes': [
                    {
                        'code': code.code,
                        'description': code.description,
                        'page': code.page_number,
                        'confidence': code.confidence
                    } for code in extracted_codes
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'PDF 업로드 중 오류가 발생했습니다: {str(e)}',
                'extracted_count': 0
            }
    
    def get_pdf_preview(self, pdf_file, allow_duplicate: bool = False, manual_category: str = None) -> List[Dict]:
        """
        PDF 미리보기 (추출될 결과코드 미리보기)
        
        Args:
            pdf_file: Streamlit UploadedFile 객체
            allow_duplicate: 중복 허용 여부
            manual_category: 선택된 카테고리 (None이면 '기타')
            
        Returns:
            추출될 결과코드 리스트
        """
        try:
            extracted_codes = self.pdf_parser.parse_pdf(pdf_file)
            
            preview_data = []
            for code in extracted_codes:
                is_duplicate = False
                if not allow_duplicate:
                    is_duplicate = any(
                        item['code'] == code.code for item in self.hybrid_search.data
                    )
                
                # 수동 선택된 카테고리 사용
                category = manual_category or '기타'
                
                preview_data.append({
                    'code': code.code,
                    'description': code.description,
                    'page': code.page_number,
                    'confidence': code.confidence,
                    'category': category,
                    'is_duplicate': is_duplicate
                })
            
            return preview_data
            
        except Exception as e:
            print(f"PDF 미리보기 오류: {e}")
            return []
    
    def upload_excel_data(self, excel_text: str, allow_duplicate: bool = False, manual_category: str = None) -> Dict:
        """
        엑셀 데이터 업로드 및 결과코드 추출
        
        Args:
            excel_text: 엑셀에서 복사한 텍스트 데이터
            allow_duplicate: 중복 허용 여부
            manual_category: 수동 선택된 카테고리 (None이면 자동 분류)
            
        Returns:
            업로드 결과 정보
        """
        try:
            # 엑셀 데이터에서 결과코드 추출
            extracted_codes = self.excel_parser.parse_excel_data(excel_text)
            
            if not extracted_codes:
                return {
                    'success': False,
                    'message': '엑셀 데이터에서 결과코드를 찾을 수 없습니다.',
                    'extracted_count': 0
                }
            
            # 기존 데이터에 추가
            added_count = 0
            duplicate_count = 0
            
            for code in extracted_codes:
                # 중복 체크 (allow_duplicate가 False인 경우만)
                is_duplicate = False
                if not allow_duplicate:
                    is_duplicate = any(
                        item['code'] == code.code for item in self.hybrid_search.data
                    )
                
                if not is_duplicate:
                    # 카테고리 결정
                    if manual_category:
                        category = manual_category
                    else:
                        category = code.category
                    
                    new_code = {
                        'code': code.code,
                        'description': code.description,
                        'category': category
                    }
                    self.hybrid_search.data.append(new_code)
                    added_count += 1
                else:
                    duplicate_count += 1
            
            # 인덱스 재구축
            self.hybrid_search.bm25 = self.hybrid_search._build_bm25()
            self.hybrid_search.embeddings = self.hybrid_search._build_embeddings()
            
            # 데이터 저장
            self.save_data()
            
            return {
                'success': True,
                'message': f'엑셀 데이터에서 {len(extracted_codes)}개의 결과코드를 추출했습니다.',
                'extracted_count': len(extracted_codes),
                'added_count': added_count,
                'duplicate_count': duplicate_count,
                'extracted_codes': [
                    {
                        'code': code.code,
                        'description': code.description,
                        'category': code.category,
                        'confidence': code.confidence
                    } for code in extracted_codes
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'엑셀 데이터 업로드 중 오류가 발생했습니다: {str(e)}',
                'extracted_count': 0
            }
    
    def get_excel_preview(self, excel_text: str, allow_duplicate: bool = False, manual_category: str = None) -> List[Dict]:
        """
        엑셀 데이터 미리보기 (추출될 결과코드 미리보기)
        
        Args:
            excel_text: 엑셀에서 복사한 텍스트 데이터
            allow_duplicate: 중복 허용 여부
            manual_category: 수동 선택된 카테고리 (None이면 자동 분류)
            
        Returns:
            추출될 결과코드 리스트
        """
        try:
            preview_data = self.excel_parser.get_preview_data(excel_text)
            
            # 중복 체크 및 카테고리 적용
            for item in preview_data:
                is_duplicate = False
                if not allow_duplicate:
                    is_duplicate = any(
                        existing_item['code'] == item['code'] 
                        for existing_item in self.hybrid_search.data
                    )
                item['is_duplicate'] = is_duplicate
                
                # 카테고리 결정
                if manual_category:
                    item['category'] = manual_category
            
            return preview_data
            
        except Exception as e:
            print(f"엑셀 미리보기 오류: {e}")
            return []
    
    def validate_excel_data(self, excel_text: str) -> Dict:
        """
        엑셀 데이터 형식 검증
        
        Args:
            excel_text: 엑셀에서 복사한 텍스트 데이터
            
        Returns:
            검증 결과
        """
        try:
            is_valid, message = self.excel_parser.validate_excel_format(excel_text)
            
            return {
                'is_valid': is_valid,
                'message': message
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'message': f'검증 중 오류가 발생했습니다: {str(e)}'
            }
    
    def update_code_category(self, code: str, new_category: str) -> bool:
        """
        특정 결과코드의 카테고리 수정
        
        Args:
            code: 수정할 결과코드
            new_category: 새로운 카테고리
            
        Returns:
            수정 성공 여부
        """
        try:
            updated = False
            for item in self.hybrid_search.data:
                if item['code'] == code:
                    item['category'] = new_category
                    updated = True
            
            if updated:
                # 데이터 저장
                self.save_data()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"카테고리 수정 실패: {e}")
            return False
