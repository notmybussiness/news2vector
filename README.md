# News2Vector

> 한국 경제 뉴스 기반 주식 추천 RAG 시스템

## 🎯 Overview

Naver 뉴스 API로 경제 뉴스를 수집하고, Milvus Vector DB에 저장하여  
**Ticker 이름 기반 유사 종목 추천** 및 **관련 뉴스 Top-K** 를 제공합니다.

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────────────────┐     ┌─────────────────────┐
│   Client    │ ──▶ │   Spring Boot Backend   │ ──▶ │   Python RAG API    │
│  (Frontend) │     │       (Consumer)        │     │     (Producer)      │
└─────────────┘     └─────────────────────────┘     └──────────┬──────────┘
                                                               │
                    ┌──────────────────────────────────────────┘
                    ▼
              ┌───────────┐     ┌───────────┐     ┌───────────┐
              │  Naver    │     │  Milvus   │     │  Gemini   │
              │  News API │     │ Vector DB │     │    LLM    │
              └───────────┘     └───────────┘     └───────────┘
```

## 📁 Project Structure

```
news2vector/
├── docs/                    # API 명세서
│   ├── API_NEWS_RAG.md      # Python RAG API 스펙
│   └── python_pipeline_interface_spec.md
├── infrastructure/          # Docker 설정 (Milvus)
├── data-pipeline/           # Python 뉴스 수집 & RAG API
│   └── src/
│       ├── api/             # FastAPI 서버 ✨ NEW
│       ├── rag/             # RAG 파이프라인 ✨ NEW
│       ├── collectors/      # Naver 뉴스 수집
│       ├── embeddings/      # KoSRoBERTa 임베딩
│       ├── processors/      # 텍스트 처리
│       └── storage/         # Milvus 클라이언트
├── embedding-service/       # Python 임베딩 API (독립)
└── scripts/                 # 유틸리티 스크립트
```

## 🚀 Quick Start

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일에 API 키 입력 (NAVER_CLIENT_ID, GEMINI_API_KEY 등)
```

### 2. Milvus 실행

```bash
cd infrastructure/docker
docker compose up -d
```

### 3. 뉴스 데이터 수집 (ETL)

```bash
cd data-pipeline
pip install -r requirements.txt
source venv/bin/activate
python -m src.main
```

### 4. RAG API 서버 실행 ✨ NEW

```bash
cd data-pipeline
source venv/bin/activate
python -m src.api.server
# 서버 시작: http://localhost:8000
```

### 5. API 테스트

```bash
# Health Check
curl http://localhost:8000/health

# 뉴스 검색
curl -X POST http://localhost:8000/api/news/search \
  -H "Content-Type: application/json" \
  -d '{"query": "삼성전자 반도체", "topK": 5}'
```

## 📡 API Endpoints

### POST /api/news/search

포트폴리오 기반 뉴스 검색 및 분석

**Request:**

```json
{
  "query": "삼성전자 반도체",
  "topK": 5,
  "filters": { "minRelevance": 0.3 }
}
```

**Response:**

```json
{
  "newsArticles": [...],
  "analysis": {
    "overallSentiment": "POSITIVE",
    "keyTopics": ["3nm 공정", "AI 칩"],
    "riskFactors": ["미중 갈등"],
    "opportunities": ["AI 반도체 수요 증가"],
    "recommendedStocks": [...]
  }
}
```

자세한 API 스펙은 [docs/API_NEWS_RAG.md](docs/API_NEWS_RAG.md) 참고

## ⏰ 자동 스케줄링

뉴스 수집 파이프라인이 **매일 오전 8시**에 자동 실행됩니다.

```bash
# crontab 확인
crontab -l
# 0 8 * * * /Users/gyu/Desktop/프로젝트/news2vector/scripts/run_pipeline.sh
```

## 📄 License

MIT
