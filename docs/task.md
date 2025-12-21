# Korean Stock News RAG System - Task Tracker

## Phase 1: 계획 수립 ✅

- [x] PRD.md 문서 작성
- [x] 프로젝트 폴더 구조 설계
- [x] 구현 계획 수립

## Phase 2: 환경 설정 ✅

- [x] Git 초기화 및 .gitignore 설정
- [x] Docker Compose 설정 (Milvus)
- [x] Python 환경 설정 (venv + requirements.txt)

## Phase 3: 데이터 수집 파이프라인 ✅

- [x] Naver API 연동 모듈
- [x] 텍스트 전처리 모듈
- [x] 임베딩 생성 모듈 (ko-sroberta)
- [x] Milvus 저장 모듈
- [x] 파이프라인 오케스트레이터

## Phase 4: 테스트 및 검증 ✅

- [x] Naver API 테스트 통과
- [x] Milvus 컬렉션 생성
- [x] 전체 파이프라인 테스트 (378개 뉴스 저장)
- [x] 검색 테스트 통과

## 결과 요약

- **수집**: 378개 뉴스
- **임베딩**: MPS(Apple Silicon GPU) 사용
- **저장**: Milvus stock_news_v1 컬렉션
- **검색**: 벡터 유사도 기반 검색 동작 확인
