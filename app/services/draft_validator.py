from app.schemas.llm_draft import LLMCardDraft
from app.services.fact_checker import FactChecker

TITLE_MAX = 70
DESCRIPTION_MIN = 800
DESCRIPTION_MAX = 1200
QUERIES_MIN = 3
QUERIES_MAX = 5


class DraftValidator:
    def review(self, draft: LLMCardDraft, fact_checker: FactChecker) -> list[str]:
        issues: list[str] = []

        title_len = len(draft.seo_title)
        if title_len > TITLE_MAX:
            issues.append(f"seo_title длиной {title_len} символов, нужно не более {TITLE_MAX}")

        desc_len = len(draft.seo_description)
        if not DESCRIPTION_MIN <= desc_len <= DESCRIPTION_MAX:
            issues.append(f"seo_description длиной {desc_len} символов, нужно {DESCRIPTION_MIN}–{DESCRIPTION_MAX}")

        queries = {q.strip().lower() for q in draft.search_queries if q.strip()}
        if not QUERIES_MIN <= len(queries) <= QUERIES_MAX:
            issues.append(f"search_queries содержит {len(queries)} уникальных запросов, нужно {QUERIES_MIN}–{QUERIES_MAX}")

        if not draft.commercial.target_audience or not draft.commercial.tasks:
            issues.append("commercial.target_audience и commercial.tasks не должны быть пустыми")

        for field, text in self._texts(draft):
            unknown = fact_checker.unknown_numbers(text)
            if unknown:
                issues.append(f"{field} содержит числа, которых нет во входных данных: {', '.join(unknown)} — удали их")
        return issues

    @staticmethod
    def _texts(draft: LLMCardDraft) -> list[tuple[str, str]]:
        return [
            ("seo_title", draft.seo_title),
            ("seo_description", draft.seo_description),
            ("search_queries", " ".join(draft.search_queries)),
            ("commercial", " ".join(draft.commercial.target_audience + draft.commercial.tasks)),
        ]
