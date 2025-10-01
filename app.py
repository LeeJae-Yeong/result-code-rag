"""
Streamlit RAG 시스템 UI
"""
import streamlit as st
import pandas as pd
from rag_system import RAGSystem
from faq_system import FAQSystem
from integrated_search import IntegratedSearch
from search_history import search_history_manager
import config

def generate_ai_response(query, faq_result, rag_results):
    """AI 어시스턴트 응답 생성"""
    response_parts = []
    
    # 인사말이나 의미없는 검색어 처리
    greeting_words = ["안녕", "안녕하세요", "hi", "hello", "헬로", "헬로우", "하이"]
    meaningless_words = ["ㅋㅋ", "ㅎㅎ", "ㅠㅠ", "ㅜㅜ", "?", "!", "...", "음", "어", "아"]
    
    query_lower = query.lower().strip()
    
    if query_lower in greeting_words:
        response_parts.append("👋 **안녕하세요!** 무엇을 도와드릴까요?")
        response_parts.append("\n**다음과 같은 질문을 해보세요:**")
        response_parts.append("- 결과코드 검색: \"4202\", \"트래픽 초과\", \"인증 실패\"")
        response_parts.append("- FAQ 검색: \"스팸 차단\", \"DB 오류\", \"전송 실패\"")
        response_parts.append("- 일반 질문: \"메시지가 안 가요\", \"오류가 나와요\"")
        response_parts.append("\n💡 자연스럽게 질문해주시면 정확한 답변을 찾아드립니다!")
        return '\n'.join(response_parts)
    
    # 의미없는 단어나 너무 짧은 검색어 처리
    if query_lower in meaningless_words or len(query.strip()) < 2:
        response_parts.append("🤔 **더 구체적으로 질문해주세요!**")
        response_parts.append("\n**예시:**")
        response_parts.append("- 결과코드 검색: \"4202\", \"트래픽 초과\", \"인증 실패\"")
        response_parts.append("- FAQ 검색: \"스팸 차단\", \"DB 오류\", \"전송 실패\"")
        response_parts.append("- 일반 질문: \"메시지가 안 가요\", \"오류가 나와요\"")
        response_parts.append("\n💡 결과코드 번호나 구체적인 문제를 말씀해주시면 도움을 드릴 수 있습니다!")
        return '\n'.join(response_parts)
    
    # 검색 결과 요약
    faq_count = len(faq_result.get('results', [])) if faq_result.get('success') else 0
    rag_count = len(rag_results)
    total_results = faq_count + rag_count
    
    if total_results == 0:
        response_parts.append("🤔 **죄송합니다.** '" + query + "'에 대한 관련 정보를 찾을 수 없습니다.")
        response_parts.append("\n💡 **다른 방법을 시도해보세요:**")
        response_parts.append("- 다른 키워드로 검색해보세요")
        response_parts.append("- 더 간단한 단어로 검색해보세요")
        response_parts.append("- 결과코드 번호를 직접 입력해보세요")
        response_parts.append("\n🆘 **도움이 필요하시면** 기술지원센터로 문의해주세요.")
    else:
        response_parts.append(f"✅ **{query}**에 대한 검색 결과를 {total_results}개 찾았습니다!")
        
        # 결과코드 검색 결과
        if rag_results:
            response_parts.append("\n🔢 **결과코드 정보:**")
            for i, result in enumerate(rag_results[:3], 1):
                response_parts.append(f"\n**{i}. 결과코드 {result['code']}**")
                response_parts.append(f"📋 {result['description']}")
                response_parts.append(f"🏷️ 카테고리: {result['category']}")
        
        # FAQ 검색 결과
        if faq_result.get('success') and faq_result.get('results'):
            response_parts.append("\n❓ **FAQ 답변:**")
            for i, faq in enumerate(faq_result['results'][:2], 1):
                response_parts.append(f"\n**{i}. {faq['question']}**")
                
                # FAQ 답변을 간단하게 요약
                answer_lines = faq['answer'].split('\n')
                summary_lines = []
                for line in answer_lines:
                    if line.startswith('**🔍 결과코드:'):
                        summary_lines.append(line)
                    elif line.startswith('**📝 설명:'):
                        summary_lines.append(line)
                    elif line.startswith('**💡 이 오류는 무엇인가요?**'):
                        summary_lines.append(line)
                        # 다음 줄도 포함
                        if len(answer_lines) > answer_lines.index(line) + 1:
                            next_line = answer_lines[answer_lines.index(line) + 1]
                            if next_line.strip():
                                summary_lines.append(next_line)
                
                if summary_lines:
                    response_parts.append('\n'.join(summary_lines[:4]))  # 최대 4줄만
                else:
                    response_parts.append(faq['answer'][:200] + "..." if len(faq['answer']) > 200 else faq['answer'])
        
        # 추가 도움말
        response_parts.append("\n🔍 **더 자세한 정보가 필요하시면:**")
        response_parts.append("- 위의 결과코드나 FAQ를 클릭해서 자세히 확인해보세요")
        response_parts.append("- 다른 키워드로 추가 검색해보세요")
        response_parts.append("- 📚 검색 내역 탭에서 이전 검색을 다시 확인할 수 있습니다")
    
    return '\n'.join(response_parts)

# 페이지 설정
st.set_page_config(
    page_title="결과코드 RAG 시스템",
    page_icon="🔍",
    layout="wide"
)

# 커스텀 CSS로 챗봇 아이콘 변경
st.markdown("""
<style>
/* Assistant 메시지 아이콘 변경 */
div[data-testid="stChatMessage"] > div:first-child > div:first-child {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Assistant 아이콘을 🤖로 변경 */
div[data-testid="stChatMessage"] > div:first-child > div:first-child > svg {
    display: none !important;
}

div[data-testid="stChatMessage"] > div:first-child > div:first-child::after {
    content: "🎯" !important;
    font-size: 20px !important;
    color: white !important;
}

/* User 메시지 아이콘 변경 */
div[data-testid="stChatMessage"] > div:first-child > div:last-child {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%) !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* User 아이콘을 👤로 변경 */
div[data-testid="stChatMessage"] > div:first-child > div:last-child > svg {
    display: none !important;
}

div[data-testid="stChatMessage"] > div:first-child > div:last-child::after {
    content: "👤" !important;
    font-size: 20px !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = RAGSystem()

if 'faq_system' not in st.session_state:
    st.session_state.faq_system = FAQSystem()

if 'integrated_search' not in st.session_state:
    st.session_state.integrated_search = IntegratedSearch(
        st.session_state.rag_system, 
        st.session_state.faq_system
    )

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
    all_faqs = st.session_state.faq_system.get_all_faqs()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("총 결과코드 수", len(all_codes))
    with col2:
        st.metric("총 FAQ 수", len(all_faqs))
    
    # 카테고리별 통계
    if all_codes:
        categories = {}
        for code in all_codes:
            cat = code.get('category', '기타')
            categories[cat] = categories.get(cat, 0) + 1
        
        st.write("**결과코드 카테고리별 분포:**")
        for cat, count in categories.items():
            st.write(f"- {cat}: {count}개")
    
    # FAQ 카테고리별 통계
    if all_faqs:
        faq_categories = {}
        for faq in all_faqs:
            cat = faq.get('category', '기타')
            faq_categories[cat] = faq_categories.get(cat, 0) + 1
        
        st.write("**FAQ 카테고리별 분포:**")
        for cat, count in faq_categories.items():
            st.write(f"- {cat}: {count}개")

# 탭 전환 처리
if hasattr(st.session_state, 'switch_to_tab'):
    if st.session_state.switch_to_tab == "integrated":
        st.info("🔄 통합 검색 탭으로 이동했습니다. 위의 검색창에서 검색어가 자동으로 입력되었습니다.")
        del st.session_state.switch_to_tab
    elif st.session_state.switch_to_tab == "faq":
        st.info("🔄 FAQ 검색 탭으로 이동했습니다. 위의 검색창에서 검색어가 자동으로 입력되었습니다.")
        del st.session_state.switch_to_tab

# 메인 컨텐츠
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["🤖 AI 어시스턴트", "❓ FAQ 검색", "📋 전체 목록", "➕ 코드 추가", "📄 PDF 업로드", "📊 엑셀 붙여넣기", "🗑️ 데이터 관리", "📚 FAQ 관리", "📝 검색 내역"])

with tab1:
    st.header("🤖 AI 어시스턴트")
    st.markdown("**안녕하세요! 결과코드와 FAQ 검색을 도와드리는 AI 어시스턴트입니다.**")
    
    # 채팅 히스토리 초기화
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # 채팅 히스토리 표시
    chat_container = st.container()
    
    with chat_container:
        # 환영 메시지
        if not st.session_state.chat_history:
            with st.chat_message("assistant"):
                st.markdown("""
                🎯 **안녕하세요!** 결과코드와 FAQ 검색을 도와드립니다.
                
                **어떤 것을 도와드릴까요?**
                - 결과코드 검색 (예: "4202", "트래픽 초과")
                - FAQ 검색 (예: "스팸 차단", "DB 오류")
                - 일반적인 질문 (예: "전송 실패", "인증 오류")
                
                🔍 **팁**: 자연스럽게 질문해주시면 가장 관련성 높은 답변을 찾아드립니다!
                """)
        
        # 채팅 히스토리 표시
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    st.markdown(message["content"])
    
    # 채팅 입력
    if prompt := st.chat_input("💬 질문을 입력하세요...", key="chat_input"):
        # 사용자 메시지 추가
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # AI 응답 생성
        with st.spinner("검색 중..."):
            # FAQ 검색
            faq_result = st.session_state.faq_system.search_faq(prompt, 5)
            
            # 결과코드 검색
            detailed_results = st.session_state.rag_system.get_detailed_results(prompt, 5)
            
            # 검색 내역 저장
            integrated_results = {
                'faq_results': faq_result.get('results', []) if faq_result.get('success') else [],
                'rag_results': detailed_results
            }
            search_history_manager.add_search(
                query=prompt,
                search_type='integrated',
                results=[integrated_results],
                result_count=len(faq_result.get('results', [])) + len(detailed_results)
            )
            
            # AI 응답 생성
            ai_response = generate_ai_response(prompt, faq_result, detailed_results)
            
            # AI 응답을 채팅 히스토리에 추가
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            
            # 채팅 화면 새로고침
            st.rerun()
    
    # 하단 버튼들
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🗑️ 대화 내역 지우기", help="채팅 히스토리를 모두 삭제합니다", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    with col2:
        st.markdown(
            '<a href="http://cms.mono.co.kr" target="_blank">'
            '<button style="background-color: #ff4b4b; color: white; padding: 0.5rem 1rem; border: none; border-radius: 0.5rem; cursor: pointer; font-size: 1rem; width: 100%;">'
            '👨‍💻 기술지원센터 문의'
            '</button></a>',
            unsafe_allow_html=True
        )
    
    with col3:
        if st.button("📋 FAQ 목록 보기", help="전체 FAQ 목록을 확인합니다", use_container_width=True):
            st.session_state.show_faq_list = True
            st.rerun()
    
    # FAQ 목록 표시 (버튼 클릭 시)
    if hasattr(st.session_state, 'show_faq_list') and st.session_state.show_faq_list:
        st.markdown("---")
        st.subheader("📋 전체 FAQ 목록")
        
        # FAQ 목록 가져오기
        all_faqs = st.session_state.faq_system.get_all_faqs()
        
        if all_faqs:
            # 우선순위별로 정렬 (높은 우선순위부터)
            sorted_faqs = sorted(all_faqs, key=lambda x: x.get('priority', 0), reverse=True)
            
            # FAQ 리스트를 확장 가능한 형태로 표시
            for i, faq in enumerate(sorted_faqs, 1):
                with st.expander(f"{i}. {faq['question']}", expanded=False):
                    st.markdown(faq['answer'])
                    
                    # 태그와 관련 코드 표시
                    col1, col2 = st.columns(2)
                    with col1:
                        if faq.get('tags'):
                            st.write("**태그:**")
                            for tag in faq['tags']:
                                st.markdown(f"`{tag}`")
                    
                    with col2:
                        if faq.get('related_codes'):
                            st.write("**관련 결과코드:**")
                            for code in faq['related_codes']:
                                st.markdown(f"- {code}")
                    
                    st.caption(f"카테고리: {faq.get('category', 'N/A')}")
        else:
            st.info("등록된 FAQ가 없습니다.")
        
        # 닫기 버튼
        if st.button("❌ FAQ 목록 닫기"):
            st.session_state.show_faq_list = False
            st.rerun()

with tab2:
    st.header("FAQ 검색")
    st.markdown("자주 묻는 질문을 검색하여 답변을 찾아보세요.")
    
    # FAQ 검색 폼
    with st.form("faq_search_form"):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            faq_query = st.text_input(
                "FAQ 검색어를 입력하세요:",
                placeholder="예: SMS 전송 실패, 인증 오류, 스팸 차단 등",
                help="질문이나 키워드를 입력하면 관련 FAQ를 찾아드립니다.",
                key="faq_search_input"
            )
        
        with col2:
            st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
            faq_search_submitted = st.form_submit_button("🔍 FAQ 검색", type="primary", use_container_width=True)
    
    # FAQ 검색 결과 (폼 제출 시)
    if faq_search_submitted and faq_query:
        with st.spinner("FAQ 검색 중..."):
            faq_result = st.session_state.faq_system.search_faq(faq_query, top_k)
            
            # 검색 내역 저장
            search_history_manager.add_search(
                query=faq_query,
                search_type='faq',
                results=faq_result.get('results', []),
                result_count=len(faq_result.get('results', []))
            )
            
            # 검색 결과 요약 (예시 이미지 스타일) - 성공/실패 관계없이 항상 표시
            st.markdown(f"**{faq_query}**에 대한 검색 결과가 **{len(faq_result['results'])}건**이 검색되었습니다.")
            
            if faq_result['success'] and faq_result['results']:
                # 검색 결과를 확장 가능한 형태로 표시
                for i, faq in enumerate(faq_result['results'], 1):
                    with st.expander(f"{i}. {faq['question']}", expanded=False):
                        st.write(faq['answer'])
                        
                        # 태그와 관련 코드 표시
                        col1, col2 = st.columns(2)
                        with col1:
                            if faq.get('tags'):
                                st.write("**태그:**")
                                for tag in faq['tags']:
                                    st.markdown(f"`{tag}`")
                        
                        with col2:
                            if faq.get('related_codes'):
                                st.write("**관련 결과코드:**")
                                for code in faq['related_codes']:
                                    st.markdown(f"- {code}")
                        
                        st.caption(f"카테고리: {faq.get('category', 'N/A')}")
            else:
                # 검색 결과가 없을 때
                st.info("검색 결과가 없습니다. 다른 검색어를 시도해보세요.")
    else:
        # 검색하지 않았을 때 자주 묻는 질문 리스트 표시
        st.subheader("📋 자주 묻는 질문")
        
        # FAQ 목록 가져오기
        all_faqs = st.session_state.faq_system.get_all_faqs()
        
        if all_faqs:
            # 우선순위별로 정렬 (높은 우선순위부터)
            sorted_faqs = sorted(all_faqs, key=lambda x: x.get('priority', 0), reverse=True)
            
            # FAQ 리스트를 확장 가능한 형태로 표시
            for i, faq in enumerate(sorted_faqs, 1):
                with st.expander(f"{i}. {faq['question']}", expanded=False):
                    st.write(faq['answer'])
                    
                    # 태그와 관련 코드 표시
                    col1, col2 = st.columns(2)
                    with col1:
                        if faq.get('tags'):
                            st.write("**태그:**")
                            for tag in faq['tags']:
                                st.markdown(f"`{tag}`")
                    
                    with col2:
                        if faq.get('related_codes'):
                            st.write("**관련 결과코드:**")
                            for code in faq['related_codes']:
                                st.markdown(f"- {code}")
                    
                    st.caption(f"카테고리: {faq.get('category', 'N/A')}")
        else:
            st.info("등록된 FAQ가 없습니다.")

with tab3:
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
                        if st.button("수정", key=f"update_{code['code']}_{i}"):
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

with tab4:
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

with tab5:
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

with tab6:
    st.header("📊 엑셀 붙여넣기")
    st.markdown("엑셀에서 복사한 데이터를 붙여넣어 결과코드를 일괄 추가합니다.")
    
    # 샘플 형식 표시
    with st.expander("📋 엑셀 형식 가이드"):
        st.markdown("""
        ### 지원되는 엑셀 형식
        
        ```
        코드    설명
        4007    서비스 요청한 클라이언트가 permission이 없는 경우
        5000    내부 서버 오류
        6000    요청 데이터 형식 오류
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

with tab7:
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

with tab8:
    st.header("📚 FAQ 관리")
    st.markdown("FAQ 항목을 추가, 수정, 삭제할 수 있습니다.")
    
    # FAQ 통계 정보
    faq_stats = st.session_state.faq_system.get_faq_statistics()
    
    if 'error' not in faq_stats:
        st.subheader("📊 FAQ 통계")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 FAQ 수", faq_stats['total_faqs'])
        
        with col2:
            st.metric("카테고리 수", len(faq_stats['categories']))
        
        with col3:
            popular_tags_count = len(faq_stats['popular_tags'])
            st.metric("인기 태그 수", popular_tags_count)
        
        # 카테고리별 분포
        if faq_stats['categories']:
            st.write("**카테고리별 분포:**")
            for category, count in faq_stats['categories'].items():
                st.write(f"- {category}: {count}개")
        
        # 인기 태그
        if faq_stats['popular_tags']:
            st.write("**인기 태그 (상위 5개):**")
            for tag, count in list(faq_stats['popular_tags'].items())[:5]:
                st.write(f"- {tag}: {count}회")
    
    st.divider()
    
    # FAQ 관리 기능
    management_tab1, management_tab2, management_tab3 = st.tabs(["➕ FAQ 추가", "✏️ FAQ 수정", "🗑️ FAQ 삭제"])
    
    with management_tab1:
        st.subheader("새 FAQ 추가")
        
        with st.form("add_faq_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_faq_question = st.text_area("질문", placeholder="FAQ 질문을 입력하세요.", height=100)
                new_faq_category = st.selectbox("카테고리", ["일반", "RCS", "알림톡"])
            
            with col2:
                new_faq_answer = st.text_area("답변", placeholder="FAQ 답변을 입력하세요.", height=200)
                new_faq_tags = st.text_input("태그 (쉼표로 구분)", placeholder="예: 전송실패, SMS, 오류", help="쉼표로 구분하여 여러 태그를 입력하세요.")
                new_faq_related_codes = st.text_input("관련 결과코드 (쉼표로 구분)", placeholder="예: 2, 7, 17", help="관련된 결과코드를 쉼표로 구분하여 입력하세요.")
                new_faq_priority = st.slider("우선순위", 1, 3, 2, help="1: 높음, 2: 보통, 3: 낮음")
            
            add_faq_submitted = st.form_submit_button("➕ FAQ 추가", type="primary")
            
            if add_faq_submitted:
                if new_faq_question and new_faq_answer:
                    # 태그 처리
                    tags = [tag.strip() for tag in new_faq_tags.split(',') if tag.strip()] if new_faq_tags else []
                    
                    # 관련 코드 처리
                    related_codes = [code.strip() for code in new_faq_related_codes.split(',') if code.strip()] if new_faq_related_codes else []
                    
                    # FAQ 데이터 구성 (ID는 자동 생성)
                    faq_data = {
                        'question': new_faq_question,
                        'answer': new_faq_answer,
                        'category': new_faq_category,
                        'tags': tags,
                        'related_codes': related_codes,
                        'priority': new_faq_priority
                    }
                    
                    # FAQ 추가
                    result = st.session_state.faq_system.add_faq(faq_data)
                    
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                        st.rerun()
                    else:
                        st.error(f"❌ {result['message']}")
                else:
                    st.error("질문과 답변은 필수 입력 항목입니다.")
    
    with management_tab2:
        st.subheader("FAQ 수정")
        
        # 수정할 FAQ 선택
        all_faqs = st.session_state.faq_system.get_all_faqs()
        
        if all_faqs:
            faq_options = {f"{faq['id']} - {faq['question'][:50]}...": faq['id'] for faq in all_faqs}
            
            selected_faq_display = st.selectbox(
                "수정할 FAQ를 선택하세요:",
                options=list(faq_options.keys()),
                help="수정할 FAQ를 선택하세요."
            )
            
            if selected_faq_display:
                selected_faq_id = faq_options[selected_faq_display]
                selected_faq = st.session_state.faq_system.get_faq_by_id(selected_faq_id)
                
                if selected_faq['success']:
                    faq_data = selected_faq['faq']
                    
                    with st.form("update_faq_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            update_question = st.text_area("질문", value=faq_data['question'], height=100)
                            update_category = st.selectbox("카테고리", ["일반", "RCS", "알림톡"], 
                                                         index=["일반", "RCS", "알림톡"].index(faq_data['category']) 
                                                         if faq_data['category'] in ["일반", "RCS", "알림톡"] else 0)
                        
                        with col2:
                            update_answer = st.text_area("답변", value=faq_data['answer'], height=200)
                            update_tags = st.text_input("태그 (쉼표로 구분)", value=', '.join(faq_data.get('tags', [])))
                            update_related_codes = st.text_input("관련 결과코드 (쉼표로 구분)", value=', '.join(faq_data.get('related_codes', [])))
                            update_priority = st.slider("우선순위", 1, 3, faq_data.get('priority', 2))
                        
                        update_faq_submitted = st.form_submit_button("✏️ FAQ 수정", type="primary")
                        
                        if update_faq_submitted:
                            # 태그 처리
                            tags = [tag.strip() for tag in update_tags.split(',') if tag.strip()] if update_tags else []
                            
                            # 관련 코드 처리
                            related_codes = [code.strip() for code in update_related_codes.split(',') if code.strip()] if update_related_codes else []
                            
                            # 업데이트 데이터 구성
                            update_data = {
                                'question': update_question,
                                'answer': update_answer,
                                'category': update_category,
                                'tags': tags,
                                'related_codes': related_codes,
                                'priority': update_priority
                            }
                            
                            # FAQ 수정
                            result = st.session_state.faq_system.update_faq(selected_faq_id, update_data)
                            
                            if result['success']:
                                st.success(f"✅ {result['message']}")
                                st.rerun()
                            else:
                                st.error(f"❌ {result['message']}")
                else:
                    st.error(f"❌ {selected_faq['message']}")
        else:
            st.info("수정할 FAQ가 없습니다.")
    
    with management_tab3:
        st.subheader("FAQ 삭제")
        
        # 삭제할 FAQ 선택
        if all_faqs:
            delete_faq_options = {f"{faq['id']} - {faq['question'][:50]}...": faq['id'] for faq in all_faqs}
            
            selected_delete_faq_display = st.selectbox(
                "삭제할 FAQ를 선택하세요:",
                options=list(delete_faq_options.keys()),
                help="삭제할 FAQ를 선택하세요.",
                key="delete_faq_select"
            )
            
            if selected_delete_faq_display:
                selected_delete_faq_id = delete_faq_options[selected_delete_faq_display]
                
                # 선택된 FAQ 정보 표시
                faq_info = st.session_state.faq_system.get_faq_by_id(selected_delete_faq_id)
                
                if faq_info['success']:
                    faq_data = faq_info['faq']
                    
                    st.warning("⚠️ **삭제할 FAQ 정보:**")
                    st.write(f"**ID:** {faq_data['id']}")
                    st.write(f"**질문:** {faq_data['question']}")
                    st.write(f"**카테고리:** {faq_data['category']}")
                    st.write(f"**우선순위:** {faq_data.get('priority', 0)}")
                    
                    # 확인 체크박스
                    confirm_delete = st.checkbox("위 FAQ를 삭제하는 것을 확인합니다", help="체크해야 삭제 버튼이 활성화됩니다.")
                    
                    if confirm_delete:
                        if st.button("🗑️ FAQ 삭제", type="primary"):
                            result = st.session_state.faq_system.delete_faq(selected_delete_faq_id)
                            
                            if result['success']:
                                st.success(f"✅ {result['message']}")
                                st.rerun()
                            else:
                                st.error(f"❌ {result['message']}")
                    else:
                        st.button("🗑️ FAQ 삭제", type="primary", disabled=True)
                else:
                    st.error(f"❌ {faq_info['message']}")
        else:
            st.info("삭제할 FAQ가 없습니다.")

with tab9:
    st.header("📝 검색 내역")
    st.markdown("이전에 검색한 내용들을 확인하고 관리할 수 있습니다.")
    
    # 검색 통계
    stats = search_history_manager.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 검색 횟수", stats['total_searches'])
    with col2:
        st.metric("오늘 검색 횟수", stats['today_searches'])
    with col3:
        st.metric("통합 검색", stats['by_type'].get('integrated', 0))
    with col4:
        st.metric("FAQ 검색", stats['by_type'].get('faq', 0))
    
    st.divider()
    
    # 검색 내역 필터링 옵션
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        search_filter = st.selectbox(
            "검색 유형 필터",
            ["전체", "통합 검색", "FAQ 검색"],
            key="history_filter"
        )
    
    with col2:
        history_search = st.text_input(
            "검색어로 내역 찾기",
            placeholder="검색어를 입력하세요",
            key="history_search"
        )
    
    with col3:
        # 버튼을 상단에 정렬하기 위해 빈 공간 추가
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ 내역 삭제", help="전체 검색 내역을 삭제합니다", use_container_width=True):
            if st.session_state.get('confirm_clear', False):
                search_history_manager.clear_history()
                st.success("✅ 검색 내역이 모두 삭제되었습니다.")
                st.session_state.confirm_clear = False
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("⚠️ 다시 클릭하면 검색 내역이 삭제됩니다!")
    
    # 인기 검색어
    if not history_search:
        st.subheader("🔥 인기 검색어")
        popular_searches = search_history_manager.get_popular_searches(5)
        
        if popular_searches:
            cols = st.columns(len(popular_searches))
            for i, (col, popular) in enumerate(zip(cols, popular_searches)):
                with col:
                    st.metric(
                        f"{i+1}. {popular['query']}", 
                        f"{popular['count']}회",
                        help=f"'{popular['query']}' 검색 횟수"
                    )
        else:
            st.info("아직 인기 검색어가 없습니다.")
        
        st.divider()
    
    # 검색 내역 표시
    st.subheader("📋 최근 검색 내역")
    
    # 필터링된 검색 내역 가져오기
    if history_search:
        # 검색어로 필터링
        filtered_history = search_history_manager.search_history(history_search)
    elif search_filter == "통합 검색":
        filtered_history = search_history_manager.get_searches_by_type('integrated')
    elif search_filter == "FAQ 검색":
        filtered_history = search_history_manager.get_searches_by_type('faq')
    else:
        # 전체 내역
        filtered_history = search_history_manager.get_recent_searches(20)
    
    if filtered_history:
        for i, search in enumerate(filtered_history, 1):
            with st.expander(f"{i}. {search['query']} - {search['time']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**검색어:** {search['query']}")
                    st.write(f"**검색 유형:** {search['search_type']}")
                    st.write(f"**검색 시간:** {search['date']} {search['time']}")
                    st.write(f"**결과 개수:** {search['result_count']}개")
                    
                    # 결과 미리보기
                    if search['results_preview']:
                        st.write("**결과 미리보기:**")
                        for preview in search['results_preview']:
                            if search['search_type'] == 'result_code':
                                st.write(f"- {preview['code']}: {preview['description']}")
                            elif search['search_type'] == 'faq':
                                st.write(f"- {preview['question']} ({preview['category']})")
                            elif search['search_type'] == 'integrated':
                                if preview['faq_count'] > 0:
                                    st.write(f"- FAQ: {preview['faq_preview']}")
                                if preview['rag_count'] > 0:
                                    st.write(f"- 결과코드: {preview['rag_preview']}")
                
    else:
        if history_search:
            st.info(f"'{history_search}'에 대한 검색 내역이 없습니다.")
        elif search_filter != "전체":
            st.info(f"{search_filter} 내역이 없습니다.")
        else:
            st.info("아직 검색 내역이 없습니다. 검색을 시작해보세요!")

# 푸터
st.divider()


