"""
PDF 파싱 및 결과코드 추출 모듈
"""
import io
import re
import json
from typing import List
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from dataclasses import dataclass

@dataclass
class ExtractedCode:
    """추출된 결과코드 정보"""
    code: str
    description: str
    page_number: int
    confidence: float = 0.0

class PDFParser:
    """PDF 파싱 및 결과코드 추출 클래스"""
    
    def __init__(self):
        """PDF 파서 초기화"""
        # 코드와 설명을 동시에 뽑는 단일 패턴
        self.code_patterns = [
            # r'(\d{4,5})\s*[:：]?\s*(.+)',  # "4007 : 설명" 또는 "4007 설명"
            r'(\d+)\s*[:：]?\s*(.+)',  # "4007 : 설명" 또는 "4007 설명"
        ]
    
    def parse_pdf(self, pdf_file) -> List[ExtractedCode]:
        """
        PDF 파일에서 결과코드 추출
        
        Args:
            pdf_file: 업로드된 PDF 파일 (Streamlit UploadedFile)
            
        Returns:
            추출된 결과코드 리스트
        """
        extracted_codes = []
        
        try:
            # PDF 파일을 바이트로 읽기
            pdf_bytes = pdf_file.read()
            
            # 여러 방법으로 PDF 파싱 시도
            methods = [
                self._parse_with_pdfplumber,
                self._parse_with_pymupdf,
                self._parse_with_pypdf2
            ]
            
            for method in methods:
                try:
                    codes = method(pdf_bytes)
                    if codes:
                        extracted_codes.extend(codes)
                        print(f"PDF 파싱 성공: {len(codes)}개 코드 추출")
                        break
                except Exception as e:
                    print(f"PDF 파싱 방법 실패: {e}")
                    continue
            
            # 중복 제거 및 정리
            extracted_codes = self._deduplicate_codes(extracted_codes)
            
            # 디버깅 정보 출력
            if not extracted_codes:
                print("PDF에서 결과코드를 찾을 수 없습니다.")
                self._debug_pdf_content(pdf_bytes)
            
        except Exception as e:
            print(f"PDF 파싱 오류: {e}")
        
        return extracted_codes
    
    def _parse_with_pdfplumber(self, pdf_bytes: bytes) -> List[ExtractedCode]:
        """pdfplumber를 사용한 PDF 파싱"""
        codes = []
        
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    page_codes = self._extract_codes_from_text(text, page_num)
                    codes.extend(page_codes)
        
        return codes
    
    def _parse_with_pymupdf(self, pdf_bytes: bytes) -> List[ExtractedCode]:
        """PyMuPDF를 사용한 PDF 파싱"""
        codes = []
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text:
                page_codes = self._extract_codes_from_text(text, page_num + 1)
                codes.extend(page_codes)
        doc.close()
        
        return codes
    
    def _parse_with_pypdf2(self, pdf_bytes: bytes) -> List[ExtractedCode]:
        """PyPDF2를 사용한 PDF 파싱"""
        codes = []
        
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()
            if text:
                page_codes = self._extract_codes_from_text(text, page_num)
                codes.extend(page_codes)
        
        return codes
    
    def _extract_codes_from_text(self, text: str, page_num: int) -> List[ExtractedCode]:
        """텍스트에서 결과코드 추출"""
        codes = []
        lines = text.split('\n')
        
        print(f"페이지 {page_num}에서 {len(lines)}줄 처리 중...")
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # PDF 줄에 여러 코드가 붙어 있을 수 있어서 탭 기준 분리
            parts = line.split("\t")
            for part in parts:
                part = part.strip()
                if not part:
                    continue

                # 각 패턴으로 코드 추출 시도
                for pattern_idx, pattern in enumerate(self.code_patterns):
                    match = re.match(pattern, part)
                    if match:
                        code, description = match.groups()
                        if code and description:
                            confidence = self._calculate_confidence(code, description, part)
                            codes.append(ExtractedCode(
                                code=code,
                                description=description.strip(),
                                page_number=page_num,
                                confidence=confidence
                            ))
                            print(f"코드 추출: {code} - {description[:30]}... (패턴 {pattern_idx+1})")
        
        print(f"페이지 {page_num}에서 {len(codes)}개 코드 추출")
        return codes
    
    def _calculate_confidence(self, code: str, description: str, line: str) -> float:
        """추출된 코드의 신뢰도 계산"""
        confidence = 0.5  # 기본 신뢰도
        
        if code.isdigit():
            confidence += 0.2
        if len(description) > 5:
            confidence += 0.2
        if re.search(r'[가-힣]', description):
            confidence += 0.1
        
        keywords = ['오류', '에러', '실패', '장애', '인증', '권한', '네트워크', '시스템']
        if any(keyword in description for keyword in keywords):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _deduplicate_codes(self, codes: List[ExtractedCode]) -> List[ExtractedCode]:
        """중복된 코드 제거"""
        seen_codes = set()
        unique_codes = []
        
        for code in codes:
            code_key = (code.code, code.description)
            if code_key not in seen_codes:
                seen_codes.add(code_key)
                unique_codes.append(code)
        
        unique_codes.sort(key=lambda x: x.confidence, reverse=True)
        return unique_codes
    
    def extract_codes_to_json(self, pdf_file) -> str:
        """
        PDF에서 추출한 결과코드를 JSON 형식으로 반환
        """
        extracted_codes = self.parse_pdf(pdf_file)
        
        json_data = []
        for code in extracted_codes:
            json_data.append({
                "code": code.code,
                "description": code.description,
                "category": self._categorize_code(code.description),
                "page_number": code.page_number,
                "confidence": code.confidence
            })
        
        return json.dumps(json_data, ensure_ascii=False, indent=2)
    
    def _categorize_code(self, description: str) -> str:
        """설명을 기반으로 카테고리 분류"""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ['알림톡', 'kakao', '카카오', 'talk', '톡']):
            return '알림톡'
        elif any(keyword in description_lower for keyword in ['rcs', '리치', 'rich', '메시지']):
            return 'RCS'
        elif any(keyword in description_lower for keyword in ['일반', 'sms', '문자']):
            return '일반'
        else:
            return '기타'
    
    def _debug_pdf_content(self, pdf_bytes: bytes):
        """PDF 내용 디버깅"""
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                print(f"PDF 페이지 수: {len(pdf.pages)}")
                if pdf.pages:
                    first_page_text = pdf.pages[0].extract_text()
                    if first_page_text:
                        print("첫 페이지 텍스트 샘플:")
                        print("-" * 50)
                        print(first_page_text[:500])
                        print("-" * 50)
                        
                        numbers = re.findall(r'\d{4,5}', first_page_text)
                        if numbers:
                            print(f"발견된 코드 숫자: {numbers[:10]}")
                        else:
                            print("코드 숫자를 찾지 못함")
                    else:
                        print("첫 페이지 텍스트 없음")
        except Exception as e:
            print(f"PDF 디버깅 오류: {e}")
