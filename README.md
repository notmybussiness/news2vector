# News2Vector

> 한국 경제 뉴스 기반 주식 추천 RAG 시스템

## 🎯 Overview

Naver 뉴스 API로 경제 뉴스를 수집하고, Milvus Vector DB에 저장하여  
**Ticker 이름 기반 유사 종목 추천** 및 **관련 뉴스 Top-K** 를 제공합니다.

## 🏗️ Architecture

```
Naver API → Python Pipeline → Milvus → Spring Boot API → Gemini → Response
```

## 📁 Project Structure

```
news2vector/
├── docs/                    # 문서
├── infrastructure/          # Docker 설정
├── data-pipeline/           # Python 뉴스 수집
├── embedding-service/       # Python 임베딩 API
├── rag-service/             # Spring Boot RAG API
└── scripts/                 # 유틸리티
```

## 🚀 Quick Start

```bash
# 1. 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 입력

# 2. Milvus 실행
cd infrastructure/docker
docker compose up -d

# 3. 데이터 파이프라인 실행
cd data-pipeline
pip install -r requirements.txt
python -m src.main

# 4. RAG 서비스 실행
cd rag-service
./gradlew bootRun
```

## 📄 License

MIT
