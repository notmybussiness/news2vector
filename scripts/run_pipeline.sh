#!/bin/bash
# News2Vector 파이프라인 실행 스크립트
# cron job에서 호출됨

set -e

# 경로 설정
PROJECT_DIR="/Users/gyu/Desktop/프로젝트/news2vector"
LOG_FILE="$PROJECT_DIR/logs/pipeline_$(date +%Y%m%d_%H%M%S).log"

# 로그 디렉토리 생성
mkdir -p "$PROJECT_DIR/logs"

echo "========================================" >> "$LOG_FILE"
echo "Pipeline started at $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 가상환경 활성화 및 실행
cd "$PROJECT_DIR/data-pipeline"
source venv/bin/activate

# 파이프라인 실행
python -m src.main >> "$LOG_FILE" 2>&1

echo "Pipeline completed at $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 7일 이상 된 로그 삭제
find "$PROJECT_DIR/logs" -name "pipeline_*.log" -mtime +7 -delete
