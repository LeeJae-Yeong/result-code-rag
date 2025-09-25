"""
Streamlit RAG 시스템 UI
"""
import streamlit as st
import pandas as pd
from rag_system import RAGSystem
import config

# 페이지 설정
st.set_page_config(
    page_title="결과코드 RAG 시스템",
    page_icon="🔍",
    layout="wide"
)

# 세션 상태 초기화
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = RAGSystem()

# 메인 타이틀
st.title("🔍 결과코드 RAG 시스템")
st.markdown("**Hybrid Search 기반 결과코드 검색 및 설명 시스템**")

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 가중치 조정
    st.subheader("검색 가중치")
    bm25_weight = st.slider("BM25 가중치", 0.0, 1.0, config.BM25_WEIGHT, 0.1)
    embedding_weight = st.slider("임베딩 가중치", 0.0, 1.0, config.EMBEDDING_WEIGHT, 0.1)
    
    # 임계값 설정
    confidence_threshold = st.slider("신뢰도 임계값", 0.0, 1.0, config.CONFIDENCE_THRESHOLD, 0.1)
    
    # 결과 수 설정
    top_k = st.slider("상위 결과 수", 1, 20, config.TOP_K_RESULTS, 1)
    
    st.divider()
    
    # 통계 정보
    st.subheader("📊 데이터 통계")
    all_codes = st.session_state.rag_system.get_all_codes()
    st.metric("총 결과코드 수", len(all_codes))
    
    # 카테고리별 통계
    if all_codes:
        categories = {}
        for code in all_codes:
            cat = code.get('category', '기타')
            categories[cat] = categories.get(cat, 0) + 1
        
        st.write("**카테고리별 분포:**")
        for cat, count in categories.items():
            st.write(f"- {cat}: {count}개")

# 메인 컨텐츠
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🔍 검색", "📋 전체 목록", "➕ 코드 추가", "📄 PDF 업로드", "📊 엑셀 붙여넣기", "🗑️ 데이터 관리"])

with tab1:
    st.header("결과코드 검색")
    
    # 검색 입력
    query = st.text_input(
        "검색할 결과코드를 입력하세요:",
        placeholder="예: 결과코드 4007, 1, 5000 등",
        help="'결과코드'를 포함하거나 숫자만 입력해도 됩니다."
    )
    
    # 검색 버튼
    search_button = st.button("🔍 검색", type="primary")
    
    # 검색 결과
    if search_button and query:
        with st.spinner("검색 중..."):
            # 중복 코드 포함 검색 결과
            result = st.session_state.rag_system.process_query_with_duplicates(query)
            
            # 결과 표시
            st.subheader("📋 검색 결과")
            
            # 신뢰도에 따른 색상 표시
            confidence = result['confidence']
            if confidence >= 0.8:
                confidence_color = "🟢"
            elif confidence >= 0.5:
                confidence_color = "🟡"
            else:
                confidence_color = "🔴"
            
            # 결과 카드
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.metric("결과코드", result['code'])
                if 'count' in result:
                    st.metric("발견된 설명", f"{result['count']}개")
                st.metric("신뢰도", f"{confidence:.3f}", help=f"{confidence_color} 신뢰도: {confidence:.1%}")
            
            with col2:
                if result['descriptions']:
                    st.write("**설명:**")
                    for i, desc in enumerate(result['descriptions'], 1):
                        with st.container():
                            st.write(f"**{i}. {desc['description']}**")
                            st.caption(f"카테고리: {desc['category']}")
                            if i < len(result['descriptions']):
                                st.divider()
                elif 'message' in result:
                    st.error(result['message'])
                else:
                    st.warning("설명을 찾을 수 없습니다.")
            
            # 상세 검색 결과 (확장 가능)
            with st.expander("🔍 상세 검색 결과 (Top 10)"):
                detailed_results = st.session_state.rag_system.get_detailed_results(query, 10)
                
                if detailed_results:
                    # 데이터프레임으로 표시
                    df_data = []
                    for i, res in enumerate(detailed_results, 1):
                        df_data.append({
                            "순위": i,
                            "코드": res['code'],
                            "설명": res['description'],
                            "카테고리": res['category'],
                            "전체 점수": f"{res['score']:.3f}",
                            "BM25 점수": f"{res['bm25_score']:.3f}",
                            "임베딩 점수": f"{res['embedding_score']:.3f}"
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("검색 결과가 없습니다.")

with tab2:
    st.header("전체 결과코드 목록")
    
    if all_codes:
        # 필터링 옵션
        col1, col2 = st.columns(2)
        
        with col1:
            categories = list(set(code.get('category', '기타') for code in all_codes))
            selected_category = st.selectbox("카테고리 필터", ["전체"] + sorted(categories))
        
        with col2:
            search_term = st.text_input("코드/설명 검색", placeholder="검색어 입력...")
        
        # 카테고리 수정 모드 토글
        edit_mode = st.checkbox("카테고리 수정 모드", help="체크하면 각 결과코드의 카테고리를 수정할 수 있습니다.")
        
        # 필터링된 데이터
        filtered_codes = all_codes
        if selected_category != "전체":
            filtered_codes = [code for code in filtered_codes if code.get('category') == selected_category]
        
        if search_term:
            filtered_codes = [code for code in filtered_codes 
                            if search_term.lower() in code.get('code', '').lower() 
                            or search_term.lower() in code.get('description', '').lower()]
        
        # 결과 표시
        st.write(f"**총 {len(filtered_codes)}개의 결과코드**")
        
        # 카드 형태로 표시
        for i, code in enumerate(filtered_codes):
            if edit_mode:
                # 수정 모드: 카테고리 선택 가능
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    st.write(f"**결과코드 {code['code']}**")
                
                with col2:
                    current_category = code.get('category', '기타')
                    new_category = st.selectbox(
                        f"카테고리 {i}",
                        ["알림톡", "RCS", "일반", "기타"],
                        index=["알림톡", "RCS", "일반", "기타"].index(current_category) if current_category in ["알림톡", "RCS", "일반", "기타"] else 3,
                        key=f"category_{code['code']}_{i}"
                    )
                    
                    if new_category != current_category:
                        if st.button(f"수정", key=f"update_{code['code']}_{i}"):
                            if st.session_state.rag_system.update_code_category(code['code'], new_category):
                                st.success(f"카테고리가 '{new_category}'로 변경되었습니다!")
                                st.rerun()
                            else:
                                st.error("카테고리 수정에 실패했습니다.")
                
                with col3:
                    st.write(f"**설명:** {code['description']}")
            else:
                # 일반 모드: 기존 방식
                with st.expander(f"결과코드 {code['code']} - {code.get('category', '기타')}", expanded=False):
                    st.write(f"**설명:** {code['description']}")
                    if code.get('category'):
                        st.write(f"**카테고리:** {code['category']}")
    else:
        st.warning("데이터를 불러올 수 없습니다.")

with tab3:
    st.header("새 결과코드 추가")
    
    with st.form("add_code_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_code = st.text_input("결과코드", placeholder="예: 9999")
            new_category = st.selectbox("카테고리", ["알림톡", "RCS", "일반", "기타"])
        
        with col2:
            new_description = st.text_area("설명", placeholder="결과코드에 대한 상세 설명을 입력하세요.", height=100)
        
        # 중복 허용 옵션
        allow_duplicate = st.checkbox(
            "중복 허용", 
            help="같은 코드에 대해 다른 설명(유형)을 허용합니다. 체크하면 기존 코드와 중복되어도 추가됩니다.",
            key="duplicate_manual"
        )
        
        # 카테고리 선택 옵션
        st.write("**카테고리 설정:**")
        category_option = st.radio(
            "카테고리 설정 방법",
            ["자동 분류", "수동 선택"],
            help="자동 분류: 설명을 기반으로 자동 분류, 수동 선택: 모든 코드에 동일한 카테고리 적용"
        )
        
        manual_category = None
        if category_option == "수동 선택":
            manual_category = st.selectbox("카테고리 선택", ["알림톡", "RCS", "일반", "기타"])
        
        submitted = st.form_submit_button("➕ 코드 추가", type="primary")
        
        if submitted:
            if new_code and new_description:
                # 카테고리 결정
                final_category = new_category
                if category_option == "수동 선택" and manual_category:
                    final_category = manual_category
                
                success = st.session_state.rag_system.add_code(new_code, new_description, final_category, allow_duplicate)
                if success:
                    if allow_duplicate:
                        st.success(f"결과코드 {new_code}이(가) 성공적으로 추가되었습니다! (중복 허용)")
                    else:
                        st.success(f"결과코드 {new_code}이(가) 성공적으로 추가되었습니다!")
                    # 데이터 저장
                    if st.session_state.rag_system.save_data():
                        st.info("데이터가 저장되었습니다.")
                    st.rerun()
                else:
                    if allow_duplicate:
                        st.error("코드 추가에 실패했습니다.")
                    else:
                        st.error("코드 추가에 실패했습니다. (중복 코드일 수 있습니다)")
            else:
                st.error("코드와 설명을 모두 입력해주세요.")

with tab4:
    st.header("PDF 업로드")
    st.markdown("PDF 파일에서 결과코드를 자동으로 추출하여 데이터베이스에 추가합니다.")
    
    # PDF 업로드
    uploaded_file = st.file_uploader(
        "PDF 파일을 선택하세요",
        type=['pdf'],
        help="결과코드가 포함된 PDF 파일을 업로드하세요."
    )
    
    if uploaded_file is not None:
        # 파일 정보 표시
        st.info(f"📄 업로드된 파일: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
        
        # 중복 허용 옵션
        allow_duplicate = st.checkbox(
            "중복 허용", 
            help="같은 코드에 대해 다른 설명(유형)을 허용합니다. 체크하면 기존 코드와 중복되어도 추가됩니다.",
            key="duplicate_pdf"
        )
        
        # 카테고리 선택
        st.write("**카테고리 선택:**")
        pdf_manual_category = st.selectbox("카테고리 선택", ["알림톡", "RCS", "일반", "기타"], key="pdf_manual_category")
        
        # 미리보기 버튼
        col1, col2 = st.columns([1, 1])
        
        with col1:
            preview_button = st.button("👁️ 미리보기", help="PDF에서 추출될 결과코드를 미리 확인합니다.")
        
        with col2:
            upload_button = st.button("📤 업로드", type="primary", help="PDF를 분석하여 결과코드를 데이터베이스에 추가합니다.")
        
        # 미리보기
        if preview_button:
            with st.spinner("PDF 분석 중..."):
                # 디버깅 정보를 위한 임시 출력 캡처
                import sys
                from io import StringIO
                
                # stdout 캡처
                old_stdout = sys.stdout
                sys.stdout = captured_output = StringIO()
                
                try:
                    preview_data = st.session_state.rag_system.get_pdf_preview(uploaded_file, allow_duplicate, pdf_manual_category)
                finally:
                    # stdout 복원
                    sys.stdout = old_stdout
                    debug_output = captured_output.getvalue()
                
                if preview_data:
                    st.subheader("📋 추출될 결과코드 미리보기")
                    
                    # 통계 정보
                    total_count = len(preview_data)
                    duplicate_count = sum(1 for item in preview_data if item['is_duplicate'])
                    new_count = total_count - duplicate_count
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("총 추출", total_count)
                    with col2:
                        st.metric("신규 추가", new_count)
                    with col3:
                        st.metric("중복 제외", duplicate_count)
                    
                    # 결과 테이블
                    df_data = []
                    for item in preview_data:
                        df_data.append({
                            "코드": item['code'],
                            "설명": item['description'][:50] + "..." if len(item['description']) > 50 else item['description'],
                            "카테고리": item['category'],
                            "페이지": item['page'],
                            "신뢰도": f"{item['confidence']:.2f}",
                            "상태": "🔄 중복" if item['is_duplicate'] else "✅ 신규"
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # 상세 정보 (확장 가능)
                    with st.expander("🔍 상세 정보"):
                        for i, item in enumerate(preview_data, 1):
                            st.write(f"**{i}. 결과코드 {item['code']}**")
                            st.write(f"- 설명: {item['description']}")
                            st.write(f"- 카테고리: {item['category']}")
                            st.write(f"- 페이지: {item['page']}")
                            st.write(f"- 신뢰도: {item['confidence']:.3f}")
                            st.write(f"- 상태: {'중복 (추가되지 않음)' if item['is_duplicate'] else '신규 (추가됨)'}")
                            st.divider()
                else:
                    st.warning("PDF에서 결과코드를 찾을 수 없습니다.")
                    
                    # 디버깅 정보 표시
                    if debug_output:
                        with st.expander("🔧 디버깅 정보"):
                            st.code(debug_output, language="text")
        
        # 업로드
        if upload_button:
            with st.spinner("PDF 업로드 및 분석 중..."):
                result = st.session_state.rag_system.upload_pdf(uploaded_file, allow_duplicate, pdf_manual_category)
                
                if result['success']:
                    st.success(f"✅ {result['message']}")
                    
                    # 결과 통계
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("추출된 코드", result['extracted_count'])
                    with col2:
                        st.metric("신규 추가", result['added_count'])
                    with col3:
                        st.metric("중복 제외", result['duplicate_count'])
                    
                    # 추가된 코드 목록
                    if result['added_count'] > 0:
                        st.subheader("📋 추가된 결과코드")
                        for code in result['extracted_codes']:
                            if not any(item['code'] == code['code'] for item in st.session_state.rag_system.hybrid_search.data[:-result['added_count']]):
                                with st.expander(f"결과코드 {code['code']} (페이지 {code['page']})"):
                                    st.write(f"**설명:** {code['description']}")
                                    st.write(f"**신뢰도:** {code['confidence']:.3f}")
                    
                    # 페이지 새로고침
                    st.rerun()
                else:
                    st.error(f"❌ {result['message']}")
    
    # 사용법 안내
    with st.expander("📖 PDF 업로드 사용법"):
        st.markdown("""
        ### PDF 업로드 사용법
        
        1. **PDF 파일 준비**
           - 결과코드가 포함된 PDF 파일을 준비합니다
           - 텍스트가 선택 가능한 PDF를 권장합니다 (이미지 스캔 PDF는 정확도가 낮을 수 있음)
        
        2. **지원되는 형식**
           - `결과코드 4007: 설명`
           - `코드 4007: 설명`
           - `에러코드 4007: 설명`
           - `4007: 설명`
        
        3. **미리보기 기능**
           - 업로드 전에 추출될 결과코드를 미리 확인할 수 있습니다
           - 중복 여부와 신뢰도를 확인할 수 있습니다
        
        4. **중복 처리**
           - 기본적으로 이미 존재하는 코드는 자동으로 제외됩니다
           - "중복 허용" 옵션을 체크하면 같은 코드에 다른 설명이 있어도 추가 가능합니다
           - 신규 코드는 항상 데이터베이스에 추가됩니다
        """)
    
    # 현재 데이터베이스 상태
    st.subheader("📊 현재 데이터베이스 상태")
    all_codes = st.session_state.rag_system.get_all_codes()
    
    if all_codes:
        # 카테고리별 통계
        categories = {}
        for code in all_codes:
            cat = code.get('category', '기타')
            categories[cat] = categories.get(cat, 0) + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("총 결과코드 수", len(all_codes))
        
        with col2:
            st.write("**카테고리별 분포:**")
            for cat, count in sorted(categories.items()):
                st.write(f"- {cat}: {count}개")
    else:
        st.info("데이터베이스가 비어있습니다. PDF를 업로드하거나 수동으로 코드를 추가해주세요.")

with tab5:
    st.header("📊 엑셀 붙여넣기")
    st.markdown("엑셀에서 복사한 데이터를 붙여넣어 결과코드를 일괄 추가합니다.")
    
    # 샘플 형식 표시
    with st.expander("📋 엑셀 형식 가이드"):
        st.markdown("""
        ### 지원되는 엑셀 형식
        
        **방법 1: 표준 형식 (권장)**
        ```
        코드    설명                                    카테고리
        4007    서비스 요청한 클라이언트가 permission이 없는 경우    인증
        5000    내부 서버 오류                            서버
        6000    요청 데이터 형식 오류                       데이터
        ```
        
        **방법 2: 간단한 형식**
        ```
        코드    설명
        4007    서비스 요청한 클라이언트가 permission이 없는 경우
        5000    내부 서버 오류
        6000    요청 데이터 형식 오류
        ```
        
        **방법 3: 다른 컬럼명**
        ```
        번호    내용        분류
        4007    서비스 요청한 클라이언트가 permission이 없는 경우    인증
        5000    내부 서버 오류                            서버
        ```
        
        ### 사용 방법
        1. 엑셀에서 데이터를 선택하여 복사 (Ctrl+C)
        2. 아래 텍스트 영역에 붙여넣기 (Ctrl+V)
        3. "미리보기" 버튼으로 데이터 확인
        4. "업로드" 버튼으로 데이터베이스에 추가
        """)
    
    # 엑셀 데이터 입력
    excel_text = st.text_area(
        "엑셀 데이터를 붙여넣으세요:",
        height=200,
        placeholder="엑셀에서 복사한 데이터를 여기에 붙여넣으세요...",
        help="엑셀에서 데이터를 선택하여 복사(Ctrl+C)한 후 여기에 붙여넣기(Ctrl+V)하세요."
    )
    
    if excel_text:
        # 데이터 검증
        validation_result = st.session_state.rag_system.validate_excel_data(excel_text)
        
        if validation_result['is_valid']:
            st.success(f"✅ {validation_result['message']}")
            
            # 중복 허용 옵션
            allow_duplicate = st.checkbox(
                "중복 허용", 
                help="같은 코드에 대해 다른 설명(유형)을 허용합니다. 체크하면 기존 코드와 중복되어도 추가됩니다.",
                key="duplicate_excel"
            )
            
            # 카테고리 선택 옵션
            st.write("**카테고리 설정:**")
            excel_category_option = st.radio(
                "카테고리 설정 방법",
                ["자동 분류", "수동 선택"],
                help="자동 분류: 설명을 기반으로 자동 분류, 수동 선택: 모든 코드에 동일한 카테고리 적용",
                key="excel_category_option"
            )
            
            excel_manual_category = None
            if excel_category_option == "수동 선택":
                excel_manual_category = st.selectbox("카테고리 선택", ["알림톡", "RCS", "일반", "기타"], key="excel_manual_category")
            
            # 미리보기 및 업로드 버튼
            col1, col2 = st.columns([1, 1])
            
            with col1:
                preview_button = st.button("👁️ 미리보기", help="엑셀 데이터에서 추출될 결과코드를 미리 확인합니다.")
            
            with col2:
                upload_button = st.button("📤 업로드", type="primary", help="엑셀 데이터를 분석하여 결과코드를 데이터베이스에 추가합니다.")
            
            # 미리보기
            if preview_button:
                with st.spinner("엑셀 데이터 분석 중..."):
                    preview_data = st.session_state.rag_system.get_excel_preview(excel_text, allow_duplicate, excel_manual_category)
                    
                    if preview_data:
                        st.subheader("📋 추출될 결과코드 미리보기")
                        
                        # 통계 정보
                        total_count = len(preview_data)
                        duplicate_count = sum(1 for item in preview_data if item['is_duplicate'])
                        new_count = total_count - duplicate_count
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("총 추출", total_count)
                        with col2:
                            st.metric("신규 추가", new_count)
                        with col3:
                            st.metric("중복 제외", duplicate_count)
                        
                        # 결과 테이블
                        df_data = []
                        for item in preview_data:
                            df_data.append({
                                "코드": item['code'],
                                "설명": item['description'][:50] + "..." if len(item['description']) > 50 else item['description'],
                                "카테고리": item['category'],
                                "신뢰도": f"{item['confidence']:.2f}",
                                "상태": "🔄 중복" if item['is_duplicate'] else "✅ 신규"
                            })
                        
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # 상세 정보 (확장 가능)
                        with st.expander("🔍 상세 정보"):
                            for i, item in enumerate(preview_data, 1):
                                st.write(f"**{i}. 결과코드 {item['code']}**")
                                st.write(f"- 설명: {item['description']}")
                                st.write(f"- 카테고리: {item['category']}")
                                st.write(f"- 신뢰도: {item['confidence']:.3f}")
                                st.write(f"- 상태: {'중복 (추가되지 않음)' if item['is_duplicate'] else '신규 (추가됨)'}")
                                st.divider()
                    else:
                        st.warning("엑셀 데이터에서 결과코드를 찾을 수 없습니다.")
            
            # 업로드
            if upload_button:
                with st.spinner("엑셀 데이터 업로드 및 분석 중..."):
                    result = st.session_state.rag_system.upload_excel_data(excel_text, allow_duplicate, excel_manual_category)
                    
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        
                        # 결과 통계
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("추출된 코드", result['extracted_count'])
                        with col2:
                            st.metric("신규 추가", result['added_count'])
                        with col3:
                            st.metric("중복 제외", result['duplicate_count'])
                        
                        # 추가된 코드 목록
                        if result['added_count'] > 0:
                            st.subheader("📋 추가된 결과코드")
                            for code in result['extracted_codes']:
                                if not any(item['code'] == code['code'] for item in st.session_state.rag_system.hybrid_search.data[:-result['added_count']]):
                                    with st.expander(f"결과코드 {code['code']}"):
                                        st.write(f"**설명:** {code['description']}")
                                        st.write(f"**카테고리:** {code['category']}")
                                        st.write(f"**신뢰도:** {code['confidence']:.3f}")
                        
                        # 페이지 새로고침
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
        
        else:
            st.error(f"❌ {validation_result['message']}")
    
    # 현재 데이터베이스 상태
    st.subheader("📊 현재 데이터베이스 상태")
    all_codes = st.session_state.rag_system.get_all_codes()
    
    if all_codes:
        # 카테고리별 통계
        categories = {}
        for code in all_codes:
            cat = code.get('category', '기타')
            categories[cat] = categories.get(cat, 0) + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("총 결과코드 수", len(all_codes))
        
        with col2:
            st.write("**카테고리별 분포:**")
            for cat, count in sorted(categories.items()):
                st.write(f"- {cat}: {count}개")
    else:
        st.info("데이터베이스가 비어있습니다. 엑셀 데이터를 붙여넣거나 수동으로 코드를 추가해주세요.")

with tab6:
    st.header("🗑️ 데이터 관리")
    st.markdown("데이터베이스의 결과코드를 관리합니다.")
    
    # 현재 데이터 상태
    all_codes = st.session_state.rag_system.get_all_codes()
    
    if all_codes:
        st.subheader("📊 현재 데이터 상태")
        
        # 통계 정보
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 결과코드 수", len(all_codes))
        
        with col2:
            categories = {}
            for code in all_codes:
                cat = code.get('category', '기타')
                categories[cat] = categories.get(cat, 0) + 1
            st.metric("카테고리 수", len(categories))
        
        with col3:
            # 최근 추가된 코드 (마지막 5개)
            recent_codes = all_codes[-5:] if len(all_codes) >= 5 else all_codes
            st.metric("최근 추가", f"{len(recent_codes)}개")
        
        st.divider()
        
        # 개별 코드 삭제
        st.subheader("🔍 개별 코드 삭제")
        
        # 코드 선택
        code_options = {f"{code['code']} - {code['description'][:30]}...": code['code'] 
                       for code in all_codes}
        
        if code_options:
            selected_code_display = st.selectbox(
                "삭제할 결과코드를 선택하세요:",
                options=list(code_options.keys()),
                help="삭제할 결과코드를 선택하세요."
            )
            
            if selected_code_display:
                selected_code = code_options[selected_code_display]
                
                # 선택된 코드 정보 표시
                selected_code_info = next(code for code in all_codes if code['code'] == selected_code)
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**선택된 코드:** {selected_code_info['code']}")
                    st.write(f"**설명:** {selected_code_info['description']}")
                    st.write(f"**카테고리:** {selected_code_info.get('category', '기타')}")
                
                with col2:
                    if st.button("🗑️ 삭제", type="secondary", help="선택된 코드를 삭제합니다."):
                        if st.session_state.rag_system.delete_code(selected_code):
                            st.success(f"✅ 결과코드 {selected_code}이(가) 삭제되었습니다!")
                            st.rerun()
                        else:
                            st.error("❌ 코드 삭제에 실패했습니다.")
        
        st.divider()
        
        # 카테고리별 삭제
        st.subheader("📂 카테고리별 삭제")
        
        # 카테고리별 통계
        category_stats = {}
        for code in all_codes:
            cat = code.get('category', '기타')
            category_stats[cat] = category_stats.get(cat, 0) + 1
        
        if category_stats:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**카테고리별 코드 수:**")
                for cat, count in sorted(category_stats.items()):
                    st.write(f"- {cat}: {count}개")
            
            with col2:
                selected_category = st.selectbox(
                    "삭제할 카테고리를 선택하세요:",
                    options=list(category_stats.keys()),
                    help="선택한 카테고리의 모든 코드가 삭제됩니다."
                )
                
                if selected_category:
                    category_count = category_stats[selected_category]
                    st.warning(f"⚠️ {selected_category} 카테고리의 {category_count}개 코드가 삭제됩니다.")
                    
                    if st.button(f"🗑️ {selected_category} 카테고리 삭제", type="secondary"):
                        deleted_count = st.session_state.rag_system.delete_codes_by_category(selected_category)
                        if deleted_count > 0:
                            st.success(f"✅ {selected_category} 카테고리의 {deleted_count}개 코드가 삭제되었습니다!")
                            st.rerun()
                        else:
                            st.error("❌ 카테고리 삭제에 실패했습니다.")
        
        st.divider()
        
        # 전체 데이터 삭제
        st.subheader("⚠️ 전체 데이터 삭제")
        
        st.error("⚠️ **주의:** 이 작업은 모든 결과코드를 영구적으로 삭제합니다!")
        
        # 확인 체크박스
        confirm_delete = st.checkbox("전체 데이터 삭제를 확인합니다", help="체크해야 삭제 버튼이 활성화됩니다.")
        
        if confirm_delete:
            if st.button("🗑️ 전체 데이터 삭제", type="primary"):
                if st.session_state.rag_system.delete_all_codes():
                    st.success("✅ 모든 데이터가 삭제되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 전체 데이터 삭제에 실패했습니다.")
        else:
            st.button("🗑️ 전체 데이터 삭제", type="primary", disabled=True)
    
    else:
        st.info("📭 데이터베이스가 비어있습니다.")
        st.markdown("""
        데이터를 추가하려면:
        - **➕ 코드 추가** 탭에서 수동으로 추가
        - **📄 PDF 업로드** 탭에서 PDF 파일 업로드
        - **📊 엑셀 붙여넣기** 탭에서 PDF 파일 업로드
        """)
    
    # 데이터 백업/복원 안내
    with st.expander("💾 데이터 백업 및 복원"):
        st.markdown("""
        ### 데이터 백업
        - 데이터는 `data/result_codes.json` 파일에 저장됩니다
        - 이 파일을 복사하여 백업할 수 있습니다
        
        ### 데이터 복원
        - 백업된 `result_codes.json` 파일을 `data/` 폴더에 복사
        - 애플리케이션을 재시작하면 복원된 데이터가 로드됩니다
        
        ### 데이터 형식
        ```json
        [
          {
            "code": "4007",
            "description": "설명",
            "category": "카테고리"
          }
        ]
        ```
        """)

# 푸터
st.divider()

