# Cron Job 설정 가이드

## 매일 오전 9시 자동 실행

### 1. crontab 편집

```bash
crontab -e
```

### 2. 아래 줄 추가

```bash
# News2Vector 파이프라인 - 매일 오전 9시 실행
0 9 * * * /Users/gyu/Desktop/프로젝트/news2vector/scripts/run_pipeline.sh
```

### 3. 저장 후 확인

```bash
crontab -l
```

## 로그 확인

```bash
# 최근 로그 확인
ls -la logs/
cat logs/pipeline_*.log | tail -50
```

## cron 문법

```
분 시 일 월 요일
0  9  *  *  *   = 매일 오전 9시
0  */6 * * *    = 6시간마다
0  9,18 * * *   = 오전 9시, 오후 6시
```

## 주의사항

- Mac이 꺼져 있으면 실행 안 됨
- Docker(Milvus)가 실행 중이어야 함
