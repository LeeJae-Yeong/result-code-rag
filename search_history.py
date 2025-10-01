#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class SearchHistoryManager:
    """검색 내역 관리 클래스"""
    
    def __init__(self, history_file: str = "data/search_history.json"):
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """검색 내역 파일 로드"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def _save_history(self):
        """검색 내역 파일 저장"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def add_search(self, query: str, search_type: str, results: List[Dict], result_count: int):
        """검색 내역 추가
        
        Args:
            query: 검색어
            search_type: 검색 유형 ('result_code', 'faq', 'integrated')
            results: 검색 결과
            result_count: 결과 개수
        """
        search_record = {
            "id": self._generate_id(),
            "query": query,
            "search_type": search_type,
            "result_count": result_count,
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "results_preview": self._get_results_preview(results, search_type)
        }
        
        # 최신 검색을 맨 앞에 추가
        self.history.insert(0, search_record)
        
        # 최대 100개까지만 저장 (메모리 절약)
        if len(self.history) > 100:
            self.history = self.history[:100]
        
        self._save_history()
    
    def _generate_id(self) -> str:
        """고유 ID 생성"""
        if not self.history:
            return "search_001"
        
        # 마지막 ID에서 번호 추출
        last_id = self.history[0].get('id', 'search_000')
        try:
            last_num = int(last_id.split('_')[1])
            return f"search_{last_num + 1:03d}"
        except:
            return "search_001"
    
    def _get_results_preview(self, results: List[Dict], search_type: str) -> List[Dict]:
        """검색 결과 미리보기 생성 (상위 3개만)"""
        preview = []
        for result in results[:3]:
            if search_type == 'result_code':
                preview.append({
                    "code": result.get('code', ''),
                    "description": result.get('description', '')[:50] + "..." if len(result.get('description', '')) > 50 else result.get('description', '')
                })
            elif search_type == 'faq':
                preview.append({
                    "question": result.get('question', '')[:50] + "..." if len(result.get('question', '')) > 50 else result.get('question', ''),
                    "category": result.get('category', '')
                })
            elif search_type == 'integrated':
                # 통합 검색의 경우 FAQ와 결과코드 결과 모두 포함
                faq_results = result.get('faq_results', [])
                rag_results = result.get('rag_results', [])
                preview.append({
                    "faq_count": len(faq_results),
                    "rag_count": len(rag_results),
                    "faq_preview": faq_results[0].get('question', '')[:30] + "..." if faq_results else "",
                    "rag_preview": rag_results[0].get('code', '') + ": " + rag_results[0].get('description', '')[:30] + "..." if rag_results else ""
                })
        return preview
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """최근 검색 내역 조회"""
        return self.history[:limit]
    
    def get_searches_by_date(self, date: str) -> List[Dict]:
        """특정 날짜의 검색 내역 조회"""
        return [search for search in self.history if search.get('date') == date]
    
    def get_searches_by_type(self, search_type: str) -> List[Dict]:
        """특정 검색 유형의 내역 조회"""
        return [search for search in self.history if search.get('search_type') == search_type]
    
    def search_history(self, query: str) -> List[Dict]:
        """검색 내역에서 검색어로 필터링"""
        query_lower = query.lower()
        return [
            search for search in self.history 
            if query_lower in search.get('query', '').lower()
        ]
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict]:
        """인기 검색어 조회 (빈도순)"""
        search_counts = {}
        for search in self.history:
            query = search.get('query', '')
            search_counts[query] = search_counts.get(query, 0) + 1
        
        # 빈도순으로 정렬
        popular = sorted(search_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"query": query, "count": count} for query, count in popular[:limit]]
    
    def clear_history(self):
        """검색 내역 전체 삭제"""
        self.history = []
        self._save_history()
    
    def get_statistics(self) -> Dict:
        """검색 통계 조회"""
        if not self.history:
            return {"total_searches": 0, "today_searches": 0, "by_type": {}, "by_date": {}}
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_searches = len([s for s in self.history if s.get('date') == today])
        
        # 검색 유형별 통계
        by_type = {}
        for search in self.history:
            search_type = search.get('search_type', 'unknown')
            by_type[search_type] = by_type.get(search_type, 0) + 1
        
        # 날짜별 통계 (최근 7일)
        by_date = {}
        for search in self.history[:50]:  # 최근 50개만 확인
            date = search.get('date', '')
            by_date[date] = by_date.get(date, 0) + 1
        
        return {
            "total_searches": len(self.history),
            "today_searches": today_searches,
            "by_type": by_type,
            "by_date": dict(sorted(by_date.items(), reverse=True)[:7])  # 최근 7일
        }

# 전역 인스턴스
search_history_manager = SearchHistoryManager()
