"""
엑셀 데이터 파싱 및 결과코드 추출 모듈
"""
import pandas as pd
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class ExcelCode:
    """엑셀에서 추출된 결과코드 정보"""
    code: str
    description: str
    category: str = "기타"
    confidence: float = 0.0

class ExcelParser:
    """엑셀 데이터 파싱 및 결과코드 추출 클래스"""
    
    def __init__(self):
        """엑셀 파서 초기화"""
        self.required_columns = ['code', 'description']  # 필수 컬럼
        self.optional_columns = ['category', '설명', '코드', '카테고리']  # 선택적 컬럼
        
    def parse_excel_data(self, excel_text: str) -> List[ExcelCode]:
        """
        엑셀 붙여넣기 텍스트에서 결과코드 추출
        
        Args:
            excel_text: 엑셀에서 복사한 텍스트 데이터
            
        Returns:
            추출된 결과코드 리스트
        """
        try:
            # 텍스트를 DataFrame으로 변환
            df = self._text_to_dataframe(excel_text)
            
            if df.empty:
                return []
            
            # 컬럼 매핑
            df = self._map_columns(df)
            
            # 데이터 검증 및 정리
            df = self._validate_and_clean_data(df)
            
            # 결과코드 객체 생성
            codes = []
            for _, row in df.iterrows():
                if pd.notna(row['code']) and pd.notna(row['description']):
                    code = ExcelCode(
                        code=str(row['code']).strip(),
                        description=str(row['description']).strip(),
                        category=row.get('category', '기타'),
                        confidence=self._calculate_confidence(row)
                    )
                    codes.append(code)
            
            return codes
            
        except Exception as e:
            print(f"엑셀 데이터 파싱 오류: {e}")
            return []
    
    def _text_to_dataframe(self, text: str) -> pd.DataFrame:
        """텍스트를 DataFrame으로 변환"""
        try:
            # 여러 줄로 분리
            lines = text.strip().split('\n')
            
            if not lines:
                return pd.DataFrame()
            
            # 첫 번째 줄을 헤더로 사용
            # 탭과 공백 모두 구분자로 사용
            if '\t' in lines[0]:
                headers = [col.strip() for col in lines[0].split('\t')]
                separator = '\t'
            else:
                # 공백으로 구분된 경우, 첫 번째 공백을 기준으로 분리
                first_space = lines[0].find(' ')
                if first_space > 0:
                    headers = [lines[0][:first_space].strip(), lines[0][first_space:].strip()]
                else:
                    headers = [lines[0].strip()]
                separator = ' '
            
            # 데이터 행들
            data_rows = []
            for line in lines[1:]:
                if line.strip():
                    if separator == '\t':
                        row_data = [cell.strip() for cell in line.split('\t')]
                    else:
                        # 공백으로 구분된 경우, 첫 번째 공백을 기준으로 분리
                        first_space = line.find(' ')
                        if first_space > 0:
                            row_data = [line[:first_space].strip(), line[first_space:].strip()]
                        else:
                            row_data = [line.strip()]
                    
                    # 컬럼 수에 맞춰 조정
                    while len(row_data) < len(headers):
                        row_data.append('')
                    data_rows.append(row_data[:len(headers)])
            
            # DataFrame 생성
            df = pd.DataFrame(data_rows, columns=headers)
            return df
            
        except Exception as e:
            print(f"텍스트를 DataFrame으로 변환 실패: {e}")
            return pd.DataFrame()
    
    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """컬럼명을 표준화"""
        column_mapping = {}
        
        for col in df.columns:
            col_lower = col.lower().strip()
            
            # 코드 컬럼 매핑
            if any(keyword in col_lower for keyword in ['코드', 'code', '번호', 'id']):
                column_mapping[col] = 'code'
            # 설명 컬럼 매핑
            elif any(keyword in col_lower for keyword in ['설명', 'description', '내용', '메모', 'comment']):
                column_mapping[col] = 'description'
            # 카테고리 컬럼 매핑
            elif any(keyword in col_lower for keyword in ['카테고리', 'category', '분류', 'type']):
                column_mapping[col] = 'category'
        
        # 컬럼명 변경
        df = df.rename(columns=column_mapping)
        
        # 필수 컬럼이 없으면 첫 번째, 두 번째 컬럼을 사용
        if 'code' not in df.columns and len(df.columns) >= 1:
            df = df.rename(columns={df.columns[0]: 'code'})
        if 'description' not in df.columns and len(df.columns) >= 2:
            df = df.rename(columns={df.columns[1]: 'description'})
        
        return df
    
    def _validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 검증 및 정리"""
        # 필수 컬럼 확인
        if 'code' not in df.columns or 'description' not in df.columns:
            return pd.DataFrame()
        
        # 빈 행 제거
        df = df.dropna(subset=['code', 'description'])
        
        # 코드 정리 (숫자 추출, 음수 포함)
        df['code'] = df['code'].astype(str).str.extract(r'(-?\d+)')[0]
        
        # 설명 정리
        df['description'] = df['description'].astype(str).str.strip()
        
        # 빈 값 제거
        df = df[(df['code'] != '') & (df['code'] != 'nan') & 
                (df['description'] != '') & (df['description'] != 'nan')]
        
        # 카테고리 기본값 설정
        if 'category' not in df.columns:
            df['category'] = '기타'
        else:
            df['category'] = df['category'].fillna('기타')
        
        return df
    
    def _calculate_confidence(self, row: pd.Series) -> float:
        """추출된 코드의 신뢰도 계산"""
        confidence = 0.5  # 기본 신뢰도
        
        # 코드가 숫자인지 확인 (음수 포함)
        try:
            int(row['code'])
            confidence += 0.2
        except (ValueError, TypeError):
            pass
        
        # 설명이 충분한 길이인지 확인
        if len(str(row['description'])) > 5:
            confidence += 0.2
        
        # 설명에 한국어가 포함되어 있는지 확인
        if re.search(r'[가-힣]', str(row['description'])):
            confidence += 0.1
        
        # 특정 키워드가 포함되어 있는지 확인
        keywords = ['알림톡', 'rcs', 'RCS', '일반', 'sms', 'SMS', '메시지', '톡']
        if any(keyword in str(row['description']) for keyword in keywords):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_preview_data(self, excel_text: str) -> List[Dict]:
        """엑셀 데이터 미리보기"""
        codes = self.parse_excel_data(excel_text)
        
        preview_data = []
        for code in codes:
            preview_data.append({
                'code': code.code,
                'description': code.description,
                'category': code.category,
                'confidence': code.confidence
            })
        
        return preview_data
    
    def validate_excel_format(self, excel_text: str) -> Tuple[bool, str]:
        """엑셀 형식 검증"""
        try:
            df = self._text_to_dataframe(excel_text)
            
            if df.empty:
                return False, "데이터가 비어있습니다."
            
            # 최소 2개 컬럼 필요
            if len(df.columns) < 2:
                return False, "최소 2개 컬럼(코드, 설명)이 필요합니다."
            
            # 데이터 행 확인
            if len(df) == 0:
                return False, "데이터 행이 없습니다."
            
            return True, "유효한 엑셀 형식입니다."
            
        except Exception as e:
            return False, f"엑셀 형식 오류: {str(e)}"
    
    def get_sample_format(self) -> str:
        """샘플 엑셀 형식 반환"""
        return """코드	설명	카테고리
4007	서비스 요청한 클라이언트가 permission이 없는 경우	인증
5000	내부 서버 오류	서버
6000	요청 데이터 형식 오류	데이터
7000	서비스 일시 중단	서비스"""
