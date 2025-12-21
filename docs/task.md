# Korean Stock News RAG System - Task Tracker

## Phase 1: 계획 수립 ✅

- [x] PRD.md 문서 작성
- [x] 프로젝트 폴더 구조 설계
- [x] 구현 계획 수립 (implementation_plan.md)
- [x] 사용자 리뷰 및 피드백 수집

## Phase 2: 환경 설정 ✅

- [x] Git 초기화 및 .gitignore 설정
- [x] Docker Compose 설정 (Milvus)
- [x] Python 환경 설정 (requirements.txt)
- [ ] Spring Boot 프로젝트 생성 (다음 단계)

## Phase 3: 데이터 수집 파이프라인 ✅

- [x] Naver API 연동 모듈 (`collectors/naver_news.py`)
- [x] 텍스트 전처리 모듈 (`processors/text_splitter.py`, `deduplicator.py`)
- [x] 임베딩 생성 모듈 (`embeddings/ko_sroberta.py`)
- [x] Milvus 저장 모듈 (`storage/milvus_client.py`)
- [x] 파이프라인 오케스트레이터 (`main.py`)

## Phase 4: 임베딩 서비스 ✅

- [x] FastAPI 서버 (`embedding-service/src/main.py`)
- [x] Dockerfile

## Phase 5: Spring Boot RAG 서비스 (예정)

- [ ] 프로젝트 생성
- [ ] Milvus 검색 API
- [ ] Gemini LLM 연동
- [ ] 추천 API 구현

## Phase 6: 테스트 및 배포 (예정)

- [ ] 통합 테스트
- [ ] 문서화
