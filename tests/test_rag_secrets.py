import os
import sys
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from pages import rag


class RagSecretsTest(unittest.TestCase):
    def test_reads_openai_key_from_streamlit_secrets_when_env_is_missing(self):
        original = os.environ.pop("OPENAI_API_KEY", None)
        try:
            self.assertTrue(rag.get_openai_api_key())
        finally:
            if original is not None:
                os.environ["OPENAI_API_KEY"] = original

    def test_formats_evidence_row_for_streamlit_display(self):
        row = {
            "meta.lifeCycle": "성견",
            "meta.department": "내과",
            "meta.disease": "구토",
            "qa.input": "강아지가 계속 구토해요.",
            "qa.output": "반복 구토는 진료가 필요할 수 있습니다.",
        }

        item = rag.format_evidence_row(row, 0)

        self.assertEqual(item["title"], "1. 성견 / 내과 / 구토")
        self.assertNotIn("**질문**", item["body"])
        self.assertNotIn("강아지가 계속 구토해요.", item["body"])
        self.assertIn("반복 구토는 진료가 필요할 수 있습니다.", item["body"])

    def test_builds_filter_context_for_prompt(self):
        filters = {
            "life_cycle": "성견",
            "department": "내과",
            "disease": "기타",
        }

        context = rag.build_filter_context(filters)

        self.assertEqual(context, "나이 단계: 성견\n진료과: 내과\n질병 종류: 기타")

    def test_omits_all_filters_from_prompt_context(self):
        filters = {
            "life_cycle": "전체",
            "department": "전체",
            "disease": "전체",
        }

        context = rag.build_filter_context(filters)

        self.assertEqual(context, "선택 조건 없음")

    def test_adds_filters_to_search_query(self):
        filters = {
            "life_cycle": "자견",
            "department": "안과",
            "disease": "결막염",
        }

        query = rag.build_search_query("눈곱이 많이 껴요", filters)

        self.assertEqual(
            query,
            "눈곱이 많이 껴요\n나이 단계: 자견\n진료과: 안과\n질병 종류: 결막염",
        )

    def test_builds_metadata_filter_for_vector_search(self):
        filters = {
            "life_cycle": "노령견",
            "department": "외과",
            "disease": "골절",
        }

        metadata_filter = rag.build_metadata_filter(filters)

        self.assertEqual(
            metadata_filter,
            {
                "$and": [
                    {"meta.lifeCycle": "노령견"},
                    {"meta.department": "외과"},
                    {"meta.disease": "골절"},
                ]
            },
        )

    def test_normalizes_none_disease_option_to_etc_at_the_end(self):
        disease_options = rag.normalize_disease_options(["구토", "None", "기타", "피부염"])

        self.assertEqual(disease_options, ["전체", "구토", "피부염", "기타"])
        self.assertNotIn("None", disease_options)

    def test_etc_disease_filter_searches_etc_and_none_metadata(self):
        filters = {
            "life_cycle": "전체",
            "department": "전체",
            "disease": "기타",
        }

        metadata_filter = rag.build_metadata_filter(filters)

        self.assertEqual(
            metadata_filter,
            {
                "$or": [
                    {"meta.disease": "기타"},
                    {"meta.disease": "None"},
                ]
            },
        )


if __name__ == "__main__":
    unittest.main()
