"""News text preprocessor for RAG quality improvement."""

import re
import html
from typing import List
from dataclasses import dataclass
from loguru import logger


@dataclass
class PreprocessResult:
    """Result of text preprocessing."""

    original: str
    processed: str
    removed_patterns: List[str]


class NewsPreprocessor:
    """
    Preprocessor for Korean news articles.

    Removes boilerplate text, normalizes characters,
    and cleans noise to improve embedding quality.
    """

    # Patterns to remove (compiled for performance)
    NOISE_PATTERNS = [
        # 기자 정보
        (r"[가-힣]{2,4}\s*기자\s*[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "기자 이메일"),
        (r"[가-힣]{2,4}\s*기자\s*\([^)]+\)", "기자 정보"),
        (r"[가-힣]{2,4}\s*특파원", "특파원"),
        # 뉴스 태그
        (r"\[[가-힣A-Za-z0-9\s]+뉴스\]", "뉴스 태그"),
        (r"\[[가-힣]+\s*=\s*[가-힣]+\s*기자\]", "기자 태그"),
        (r"\(서울=[가-힣]+\)", "지역 태그"),
        (r"\(종합\d*\)", "종합 태그"),
        (r"\(상보\)", "상보 태그"),
        (r"\(속보\)", "속보 태그"),
        # 저작권 문구
        (r"무단\s*(전재|복제|배포).*?금지", "저작권 문구"),
        (r"저작권.*?[가-힣]+에\s*있습니다", "저작권 문구"),
        (r"ⓒ.*$", "저작권 기호"),
        (r"©.*$", "저작권 기호"),
        # 관련 기사 링크
        (r"[▶▷►→]\s*관련.*$", "관련기사"),
        (r"[▶▷►→]\s*[가-힣]+.*$", "관련링크"),
        (r"\[관련기사\].*$", "관련기사"),
        # 광고/홍보 문구
        (r"자세한\s*내용은.*?확인", "홍보 문구"),
        (r"문의\s*:?\s*\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4}", "연락처"),
        # SNS 공유
        (r"페이스북.*?공유", "SNS 공유"),
        (r"트위터.*?공유", "SNS 공유"),
        (r"카카오.*?공유", "SNS 공유"),
    ]

    def __init__(self):
        """Initialize the preprocessor with compiled patterns."""
        self._compiled_patterns = [
            (re.compile(pattern, re.MULTILINE | re.IGNORECASE), name)
            for pattern, name in self.NOISE_PATTERNS
        ]

    def preprocess(self, text: str) -> str:
        """
        Preprocess a single text.

        Args:
            text: Raw news text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        result = self._preprocess_with_details(text)
        return result.processed

    def preprocess_batch(self, texts: List[str]) -> List[str]:
        """
        Preprocess multiple texts.

        Args:
            texts: List of raw news texts

        Returns:
            List of cleaned texts
        """
        return [self.preprocess(text) for text in texts]

    def _preprocess_with_details(self, text: str) -> PreprocessResult:
        """
        Preprocess text and return details about what was removed.

        Args:
            text: Raw news text

        Returns:
            PreprocessResult with original, processed, and removed patterns
        """
        original = text
        removed = []

        # Step 1: HTML 엔티티 디코딩
        text = html.unescape(text)

        # Step 2: 노이즈 패턴 제거
        for pattern, name in self._compiled_patterns:
            if pattern.search(text):
                removed.append(name)
                text = pattern.sub("", text)

        # Step 3: 특수문자 정규화
        text = self._normalize_special_chars(text)

        # Step 4: 공백 정리
        text = self._normalize_whitespace(text)

        return PreprocessResult(
            original=original,
            processed=text.strip(),
            removed_patterns=removed,
        )

    def _normalize_special_chars(self, text: str) -> str:
        """Normalize special characters."""
        # 여러 종류의 따옴표 통일
        text = re.sub(r"[''`]", "'", text)
        text = re.sub(r'["""]', '"', text)

        # 여러 종류의 하이픈 통일
        text = re.sub(r"[‐‑‒–—―]", "-", text)

        # 여러 종류의 말줄임표 통일
        text = re.sub(r"[…⋯]", "...", text)
        text = re.sub(r"\.{4,}", "...", text)

        # 특수 공백 문자 통일
        text = re.sub(r"[\u00a0\u2000-\u200b\u3000]", " ", text)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace."""
        # 연속 공백을 하나로
        text = re.sub(r"[ \t]+", " ", text)

        # 연속 줄바꿈을 최대 2개로
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 줄 앞뒤 공백 제거
        text = "\n".join(line.strip() for line in text.split("\n"))

        return text

    def analyze(self, text: str) -> dict:
        """
        Analyze text and return preprocessing statistics.

        Useful for debugging and understanding what gets removed.

        Args:
            text: Raw news text

        Returns:
            dict with statistics
        """
        result = self._preprocess_with_details(text)

        return {
            "original_length": len(result.original),
            "processed_length": len(result.processed),
            "reduction_ratio": 1 - len(result.processed) / max(len(result.original), 1),
            "removed_patterns": result.removed_patterns,
            "sample_original": result.original[:200],
            "sample_processed": result.processed[:200],
        }
