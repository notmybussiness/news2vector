# Python Pipeline & Spring Boot Integration Interface Specification

## 1. 개요 (Overview)

본 문서는 Python 데이터 파이프라인(Producer)과 Spring Boot 백엔드(Consumer) 간의 데이터 연동 규격을 정의합니다.
두 시스템은 **Milvus Vector DB**를 통해 데이터를 공유하며, 본 문서에 정의된 스키마(Schema)가 곧 연동 인터페이스(Interface)가 됩니다.

Spring 팀은 이 문서를 참고하여 `Entity` 및 `DTO`를 설계하면 됩니다.

---

## 2. Milvus Collection Schema (Shared Interface)

Python 파이프라인이 데이터를 적재하고, Spring이 조회하는 **Milvus 컬렉션의 구조**입니다.

- **Collection Name**: `news_articles` (기본값)
- **Embedding Model**: `jhgan/ko-sroberta-multitask` (768 dimensions)

### Field Definition

| 필드명 (Field Name) | 데이터 타입 (Milvus Type) | 설명 (Description)                       | Spring 대응 타입 (Java)       |
| :------------------ | :------------------------ | :--------------------------------------- | :---------------------------- |
| `news_id`           | **Int64** (Primary Key)   | 자동 생성되는 고유 ID                    | `Long`                        |
| `embedding`         | **FloatVector** (768)     | 뉴스 본문의 임베딩 벡터                  | `List<Float>`                 |
| `title`             | **VarChar** (512)         | 뉴스 제목                                | `String`                      |
| `original_text`     | **VarChar** (2000)        | 뉴스 본문 (청킹된 원문)                  | `String`                      |
| `published_at`      | **VarChar** (20)          | 기사 발행일 (Format: `YYYY-MM-DD HH:mm`) | `String` (or `LocalDateTime`) |
| `url`               | **VarChar** (1024)        | 기사 원문 링크                           | `String`                      |

> **Note**: `embedding` 필드는 Spring에서 검색 시에만 내부적으로 사용되며, RAG 응답 DTO에는 포함되지 않는 경우가 많습니다.

---

## 3. Data Transfer Object (DTO) Proposal for Spring

Spring Boot 프로젝트에서 사용할 것으로 예상되는 DTO 구조 제안입니다.

### 3.1. Search Request (Spring → Milvus)

유저의 질문을 벡터로 변환하여 검색할 때 필요한 파라미터입니다.

```java
public class NewsSearchRequest {
    private String query;       // 검색어 (자연어 질문)
    private Integer topK;       // 반환받을 개수 (Default: 5)
    private Float minScore;     // (Optional) 최소 유사도 임계값
}
```

### 3.2. Search Response / Entity (Milvus → Spring)

Milvus에서 검색된 결과를 Spring이 매핑할 객체입니다.

```java
// Entity (DB 매핑용)
public class NewsDocument {
    private Long newsId;
    private String title;
    private String originalText;
    private String publishedAt;
    private String url;
    private Double similarityScore; // 검색 결과 유사도 (Distance 기반 계산)
}

// DTO (클라이언트 응답용)
public class NewsResponseDto {
    private String title;
    private String summary; // originalText를 그대로 쓰거나 요약해서 사용
    private String date;
    private String link;
    private Double confidence; // 유사도 점수
}
```

---

## 4. 연동 프로세스 (Workflow)

1. **[Python] 데이터 적재 (Daily Batch)**

   - Naver 뉴스 수집 -> 텍스트 분할/청킹 -> 임베딩 생성 -> Milvus에 Insert
   - 스키마 준수 필수: `title`, `original_text`, `published_at` 등 필드명 일치 확인

2. **[Spring] 데이터 검색 (User Request)**
   - 사용자가 질문 입력 (예: "삼성전자 최신 반도체 동향 알려줘")
   - Spring 내부의 임베딩 모델(또는 별도 API)을 통해 질문을 벡터화 (768 dim)
   - Milvus에 벡터 검색 요청 (`ANN Search`)
   - 반환된 `news_id`, `original_text` 등을 활용하여 LLM(Gemini/GPT)에 프롬프트 구성

---

## 5. 변경 사항 관리 (Change Log)

규격 변경이 필요할 경우, Python(적재)과 Spring(조회) 양쪽 코드를 동시에 수정해야 합니다.

- **v1.0**: 초기 스키마 정의 (현재 상태)
