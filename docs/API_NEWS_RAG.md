# News RAG API Specification (Python ↔ Spring Integration)

> **작성일**: 2025-12-23
> **버전**: v1.0
> **담당**: Python RAG 파이프라인 팀 (Producer) ↔ Spring Boot 팀 (Consumer)

---

## 📋 개요

본 문서는 Python RAG 파이프라인과 Spring Boot 백엔드 간의 **뉴스 검색 및 분석 API** 연동 규격을 정의합니다.

### 목적
- **포트폴리오 기반 뉴스 검색**: 사용자 포트폴리오의 종목/섹터 관련 뉴스 검색
- **투자 인사이트 제공**: 뉴스 기반 리스크/기회 분석
- **추천 종목 제시**: 뉴스 분석 결과 기반 투자 추천

---

## 🔗 엔드포인트

### 1. 뉴스 검색 (News Search)

**URL**: `POST /api/news/search`

**용도**: 포트폴리오 관련 뉴스 검색 및 분석

---

## 📥 Request Specification

### Request Headers
```http
POST /api/news/search HTTP/1.1
Content-Type: application/json
Accept: application/json
```

### Request Body Schema

```json
{
  "query": "string (required)",
  "portfolioContext": {
    "holdings": [
      {
        "symbol": "string",
        "name": "string",
        "weight": "number (0-1)"
      }
    ],
    "sectors": ["string"],
    "totalValue": "number"
  },
  "filters": {
    "startDate": "string (YYYY-MM-DD)",
    "endDate": "string (YYYY-MM-DD)",
    "minRelevance": "number (0-1)"
  },
  "topK": "integer (default: 5, max: 20)"
}
```

### Field Descriptions

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `query` | String | ✅ | 검색 키워드 (예: "삼성전자 반도체 최신 동향") |
| `portfolioContext` | Object | ❌ | 포트폴리오 컨텍스트 (제공 시 더 정확한 검색) |
| `portfolioContext.holdings` | Array | ❌ | 보유 종목 목록 |
| `portfolioContext.holdings[].symbol` | String | ✅ | 종목 심볼 (예: "005930.KS", "BTC-KRW") |
| `portfolioContext.holdings[].name` | String | ✅ | 종목명 (예: "삼성전자", "비트코인") |
| `portfolioContext.holdings[].weight` | Number | ✅ | 포트폴리오 내 비중 (0~1) |
| `portfolioContext.sectors` | Array | ❌ | 관련 섹터 (예: ["반도체", "암호화폐"]) |
| `portfolioContext.totalValue` | Number | ❌ | 포트폴리오 총 가치 (원) |
| `filters` | Object | ❌ | 검색 필터 |
| `filters.startDate` | String | ❌ | 검색 시작일 (기본값: 7일 전) |
| `filters.endDate` | String | ❌ | 검색 종료일 (기본값: 오늘) |
| `filters.minRelevance` | Number | ❌ | 최소 유사도 임계값 (기본값: 0.7) |
| `topK` | Integer | ❌ | 반환할 뉴스 개수 (기본값: 5, 최대: 20) |

### Request Example

```json
{
  "query": "삼성전자 반도체 최신 동향",
  "portfolioContext": {
    "holdings": [
      {
        "symbol": "005930.KS",
        "name": "삼성전자",
        "weight": 0.3
      },
      {
        "symbol": "BTC-KRW",
        "name": "비트코인",
        "weight": 0.2
      }
    ],
    "sectors": ["반도체", "암호화폐"],
    "totalValue": 10000000
  },
  "filters": {
    "startDate": "2025-12-01",
    "endDate": "2025-12-22",
    "minRelevance": 0.7
  },
  "topK": 5
}
```

---

## 📤 Response Specification

### Response Headers
```http
HTTP/1.1 200 OK
Content-Type: application/json
```

### Response Body Schema

```json
{
  "query": "string",
  "newsArticles": [
    {
      "newsId": "integer",
      "title": "string",
      "summary": "string",
      "publishedAt": "string (YYYY-MM-DD HH:mm)",
      "url": "string",
      "relevanceScore": "number (0-1)",
      "sentiment": "string (POSITIVE|NEGATIVE|NEUTRAL)"
    }
  ],
  "analysis": {
    "overallSentiment": "string (POSITIVE|NEGATIVE|NEUTRAL)",
    "sentimentDistribution": {
      "positive": "number (0-1)",
      "negative": "number (0-1)",
      "neutral": "number (0-1)"
    },
    "keyTopics": ["string"],
    "riskFactors": ["string"],
    "opportunities": ["string"],
    "recommendedStocks": [
      {
        "symbol": "string",
        "name": "string",
        "reason": "string",
        "confidence": "number (0-1)"
      }
    ]
  },
  "metadata": {
    "totalMatches": "integer",
    "returnedCount": "integer",
    "searchTimeMs": "integer"
  }
}
```

### Field Descriptions

#### newsArticles[]
| 필드 | 타입 | 설명 |
|------|------|------|
| `newsId` | Integer | Milvus 뉴스 ID |
| `title` | String | 뉴스 제목 |
| `summary` | String | 뉴스 요약 (원문 청킹된 텍스트 or LLM 요약) |
| `publishedAt` | String | 기사 발행일시 (Format: `YYYY-MM-DD HH:mm`) |
| `url` | String | 기사 원문 링크 |
| `relevanceScore` | Number | 검색어와의 유사도 (0~1, 높을수록 관련성 높음) |
| `sentiment` | String | 뉴스 감성 분석 결과 (`POSITIVE`, `NEGATIVE`, `NEUTRAL`) |

#### analysis
| 필드 | 타입 | 설명 |
|------|------|------|
| `overallSentiment` | String | 전체 뉴스의 종합 감성 |
| `sentimentDistribution` | Object | 감성 비율 (합: 1.0) |
| `keyTopics` | Array | 핵심 키워드 (예: ["3nm 공정", "수출 증가", "AI 칩"]) |
| `riskFactors` | Array | 투자 리스크 요인 (예: ["중국 견제", "글로벌 경기 둔화"]) |
| `opportunities` | Array | 투자 기회 (예: ["AI 반도체 수요 급증", "정부 지원 확대"]) |
| `recommendedStocks` | Array | 추천 종목 (뉴스 기반) |
| `recommendedStocks[].symbol` | String | 종목 심볼 (예: "005930.KS") |
| `recommendedStocks[].name` | String | 종목명 (예: "삼성전자") |
| `recommendedStocks[].reason` | String | 추천 이유 (예: "3nm 양산 성공으로 수익성 개선 전망") |
| `recommendedStocks[].confidence` | Number | 추천 신뢰도 (0~1) |

#### metadata
| 필드 | 타입 | 설명 |
|------|------|------|
| `totalMatches` | Integer | Milvus 검색 결과 총 개수 |
| `returnedCount` | Integer | 실제 반환된 뉴스 개수 |
| `searchTimeMs` | Integer | 검색 소요 시간 (밀리초) |

### Response Example

```json
{
  "query": "삼성전자 반도체 최신 동향",
  "newsArticles": [
    {
      "newsId": 12345,
      "title": "삼성전자, 차세대 3nm 공정 양산 시작",
      "summary": "삼성전자가 3나노미터 공정을 활용한 차세대 반도체 양산을 시작했다. 업계 전문가들은 이번 3nm 공정이 기존 5nm 대비 성능은 23% 향상되고 전력 소비는 45% 감소할 것으로 전망하고 있다.",
      "publishedAt": "2025-12-20 10:30",
      "url": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=001&oid=001&aid=0014234567",
      "relevanceScore": 0.92,
      "sentiment": "POSITIVE"
    },
    {
      "newsId": 12346,
      "title": "반도체 수출 3개월 연속 증가, AI 칩 수요 급증",
      "summary": "한국 반도체 수출이 3개월 연속 증가하며 회복세를 보이고 있다. 특히 AI 서버용 고성능 칩 수요가 급증하면서 삼성전자와 SK하이닉스의 수주량이 전년 대비 40% 증가했다.",
      "publishedAt": "2025-12-19 14:20",
      "url": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=101&oid=009&aid=0005234567",
      "relevanceScore": 0.85,
      "sentiment": "POSITIVE"
    },
    {
      "newsId": 12347,
      "title": "미중 반도체 갈등 심화, 한국 기업 리스크 증가",
      "summary": "미국과 중국의 반도체 패권 경쟁이 격화되면서 한국 반도체 기업들이 양국 사이에서 선택의 기로에 놓였다. 전문가들은 지정학적 리스크가 단기 실적에 악영향을 미칠 수 있다고 경고했다.",
      "publishedAt": "2025-12-18 09:15",
      "url": "https://news.naver.com/main/read.nhn?mode=LSD&mid=sec&sid1=101&oid=011&aid=0004234567",
      "relevanceScore": 0.78,
      "sentiment": "NEGATIVE"
    }
  ],
  "analysis": {
    "overallSentiment": "POSITIVE",
    "sentimentDistribution": {
      "positive": 0.67,
      "negative": 0.20,
      "neutral": 0.13
    },
    "keyTopics": [
      "3nm 공정",
      "수출 증가",
      "AI 칩",
      "미중 갈등",
      "지정학적 리스크"
    ],
    "riskFactors": [
      "미중 반도체 패권 경쟁 심화",
      "중국 시장 의존도 높음",
      "글로벌 경기 둔화 우려",
      "환율 변동성 확대"
    ],
    "opportunities": [
      "AI 반도체 수요 급증 (40% 증가)",
      "3nm 공정 양산 성공으로 기술 우위 확보",
      "정부 반도체 지원 정책 확대",
      "차세대 HBM 메모리 독점적 지위"
    ],
    "recommendedStocks": [
      {
        "symbol": "005930.KS",
        "name": "삼성전자",
        "reason": "3nm 양산 성공 및 AI 칩 수요 증가로 수익성 개선 전망",
        "confidence": 0.88
      },
      {
        "symbol": "000660.KS",
        "name": "SK하이닉스",
        "reason": "HBM 메모리 시장 독점 및 AI 서버향 수주 급증",
        "confidence": 0.85
      }
    ]
  },
  "metadata": {
    "totalMatches": 15,
    "returnedCount": 3,
    "searchTimeMs": 120
  }
}
```

---

## 🚨 Error Responses

### 400 Bad Request
```json
{
  "error": "INVALID_REQUEST",
  "message": "query 필드는 필수입니다.",
  "timestamp": "2025-12-23T10:30:00Z"
}
```

### 500 Internal Server Error
```json
{
  "error": "MILVUS_CONNECTION_ERROR",
  "message": "벡터 DB 연결 실패",
  "timestamp": "2025-12-23T10:30:00Z"
}
```

---

## 📊 성능 요구사항

| 항목 | 요구사항 |
|------|----------|
| **응답 시간** | P95 < 3초 (벡터 검색 + LLM 분석 포함) |
| **Top-K** | 기본 5개, 최대 20개 |
| **동시 요청** | 10 req/s 이상 처리 가능 |
| **가용성** | 99% 이상 |

---

## 🔄 데이터 흐름

```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │ 1. POST /api/v1/ai/analyze-with-news
       ▼
┌─────────────────────────────────┐
│    Spring Boot Backend          │
│  - JWT 인증                     │
│  - 포트폴리오 조회               │
│  - Request DTO 생성             │
└──────┬──────────────────────────┘
       │ 2. POST /api/news/search
       ▼
┌─────────────────────────────────┐
│    Python RAG Module            │
│  - 질문 임베딩 (768 dim)        │
│  - Milvus 벡터 검색             │
│  - 뉴스 감성 분석 (LLM)         │
│  - 추천 종목 생성               │
└──────┬──────────────────────────┘
       │ 3. JSON Response
       ▼
┌─────────────────────────────────┐
│    Spring Boot Backend          │
│  - Gemini 분석과 통합           │
│  - Redis 캐싱 (1시간)           │
│  - Response DTO 반환            │
└──────┬──────────────────────────┘
       │ 4. Unified Response
       ▼
┌─────────────┐
│   Client    │
│  (Frontend) │
└─────────────┘
```

---

## 🧪 테스트 시나리오

### 1. 기본 검색
**Request**:
```json
{
  "query": "삼성전자",
  "topK": 3
}
```

**기대 결과**:
- 삼성전자 관련 최신 뉴스 3건 반환
- `relevanceScore` > 0.7
- `sentiment` 필드 존재

### 2. 포트폴리오 기반 검색
**Request**:
```json
{
  "query": "반도체 산업 동향",
  "portfolioContext": {
    "holdings": [
      {"symbol": "005930.KS", "name": "삼성전자", "weight": 0.5}
    ],
    "sectors": ["반도체"]
  }
}
```

**기대 결과**:
- 삼성전자 관련 뉴스 우선 반환
- `recommendedStocks`에 유사 종목 추천

### 3. 날짜 필터링
**Request**:
```json
{
  "query": "비트코인",
  "filters": {
    "startDate": "2025-12-22",
    "endDate": "2025-12-22"
  }
}
```

**기대 결과**:
- 2025-12-22 당일 뉴스만 반환

---

## 📝 구현 체크리스트 (Python 팀)

- [ ] Milvus 벡터 검색 구현
- [ ] 뉴스 감성 분석 (POSITIVE/NEGATIVE/NEUTRAL)
- [ ] 핵심 키워드 추출 (keyTopics)
- [ ] 투자 인사이트 생성 (riskFactors, opportunities)
- [ ] 추천 종목 생성 (recommendedStocks)
- [ ] 날짜 필터링 구현
- [ ] 응답 시간 < 3초 달성
- [ ] Error Handling (400, 500)
- [ ] API 문서화 (Swagger/OpenAPI)

---

## 🔗 관련 문서

- **Milvus Schema**: `.claude/python_pipeline_interface_spec.md`
- **Spring DTO 설계**: `.claude/roadmap/NEWS_RAG_INTEGRATION.md`
- **Frontend 연동**: `.claude/specs/API_AI.md` (업데이트 예정)

---

**Last Updated**: 2025-12-23
**Contact**: Spring Backend 팀 / Python RAG 팀
