"""
Keyword Extraction skill for SEO optimization.
"""

from __future__ import annotations

import re
from collections import Counter

from src.core.registry import skill_registry
from src.interfaces.skill_interface import SkillContext, SkillParameter, SkillResult, SkillStatus
from src.skills.base import BaseSkill


@skill_registry.register(name="keyword_extraction", category="seo")
class KeywordExtractionSkill(BaseSkill):
    """Skill for extracting keywords from text."""

    name = "keyword_extraction"
    description = "Extract relevant keywords from text for SEO"
    category = "seo"
    parameters = [
        SkillParameter(
            name="text",
            param_type=str,
            description="The text to extract keywords from",
            required=True,
        ),
        SkillParameter(
            name="max_keywords",
            param_type=int,
            description="Maximum number of keywords to extract",
            required=False,
            default=10,
        ),
        SkillParameter(
            name="min_word_length",
            param_type=int,
            description="Minimum word length for keywords",
            required=False,
            default=4,
        ),
    ]

    # Common stop words in Portuguese and English
    STOP_WORDS = {
        # Portuguese
        "para", "como", "mais", "sobre", "isso", "esse", "essa", "este", "esta",
        "pelo", "pela", "pelos", "pelas", "outro", "outra", "outros", "outras",
        "todo", "toda", "todos", "todas", "muito", "muita", "muitos", "muitas",
        "pode", "podem", "fazer", "sendo", "sido", "seria", "mesmo", "mesma",
        "entre", "ainda", "depois", "antes", "quando", "onde", "qual", "quais",
        "cada", "deve", "apenas", "assim", "forma", "tipo", "tambem", "aqui",
        # English
        "that", "this", "with", "from", "have", "been", "were", "will", "would",
        "could", "should", "about", "which", "there", "their", "they", "what",
        "when", "where", "some", "many", "more", "most", "other", "than", "then",
        "also", "just", "only", "very", "such", "into", "over", "after", "before",
    }

    async def _execute(self, context: SkillContext) -> SkillResult:
        """Execute keyword extraction."""
        text = context.get("text")
        max_keywords = context.get("max_keywords", 10)
        min_word_length = context.get("min_word_length", 4)

        try:
            # Clean and tokenize text
            text_lower = text.lower()
            words = re.findall(r"\b[a-záàâãéèêíïóôõöúçñ]+\b", text_lower)

            # Filter words
            filtered_words = [
                word for word in words
                if len(word) >= min_word_length
                and word not in self.STOP_WORDS
            ]

            # Count frequency
            word_counts = Counter(filtered_words)

            # Get top keywords
            top_keywords = word_counts.most_common(max_keywords)

            # Extract bigrams
            bigrams = []
            for i in range(len(filtered_words) - 1):
                bigram = f"{filtered_words[i]} {filtered_words[i + 1]}"
                bigrams.append(bigram)

            bigram_counts = Counter(bigrams)
            top_bigrams = bigram_counts.most_common(max_keywords // 2)

            keywords = [
                {"keyword": word, "frequency": count, "type": "unigram"}
                for word, count in top_keywords
            ]

            keywords.extend([
                {"keyword": bigram, "frequency": count, "type": "bigram"}
                for bigram, count in top_bigrams
            ])

            # Sort by frequency
            keywords.sort(key=lambda x: x["frequency"], reverse=True)

            return SkillResult(
                skill_name=self.name,
                success=True,
                status=SkillStatus.COMPLETED,
                output={
                    "keywords": keywords[:max_keywords],
                    "total_words": len(words),
                    "unique_words": len(set(filtered_words)),
                },
                metadata={"extracted_count": len(keywords[:max_keywords])},
            )

        except Exception as e:
            self.logger.error("Keyword extraction failed", error=str(e))
            return SkillResult(
                skill_name=self.name,
                success=False,
                status=SkillStatus.FAILED,
                error=str(e),
            )
