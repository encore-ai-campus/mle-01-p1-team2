import sys
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from pages import rag_copy


class FakeSessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class FakeStreamlit:
    def __init__(self, calls=None):
        self.session_state = FakeSessionState()
        self.calls = calls if calls is not None else []

    def title(self, _text):
        pass

    def caption(self, _text):
        pass

    def spinner(self, _text):
        return nullcontext()

    def error(self, _text):
        pass

    def columns(self, spec):
        return [nullcontext() for _ in spec]

    def selectbox(self, _label, options):
        self.calls.append(f"selectbox:{_label}")
        return options[0]

    def slider(self, _label, min_value, max_value, value):
        self.calls.append(f"slider:{_label}")
        return value

    def chat_message(self, _role):
        return nullcontext()

    def write(self, _content):
        pass

    def chat_input(self, _placeholder):
        return None


class RagCopyPageTest(unittest.TestCase):
    def test_initial_render_does_not_initialize_rag_before_question(self):
        fake_st = FakeStreamlit()

        with (
            patch.object(rag_copy, "st", fake_st),
            patch.object(rag_copy, "load_disease_options", return_value=["전체"]),
            patch.object(rag_copy, "initialize_rag") as initialize_rag,
        ):
            rag_copy.render_rag_page()

        initialize_rag.assert_not_called()

    def test_loads_disease_options_before_rendering_filter_controls(self):
        calls = []
        fake_st = FakeStreamlit(calls)

        def load_disease_options():
            calls.append("load_disease_options")
            return ["전체"]

        with (
            patch.object(rag_copy, "st", fake_st),
            patch.object(
                rag_copy,
                "load_disease_options",
                side_effect=load_disease_options,
            ),
            patch.object(rag_copy, "initialize_rag") as initialize_rag,
        ):
            rag_copy.render_rag_page()

        initialize_rag.assert_not_called()
        first_control_index = min(
            index
            for index, call in enumerate(calls)
            if call.startswith(("selectbox:", "slider:"))
        )
        disease_options_index = calls.index("load_disease_options")

        self.assertLess(disease_options_index, first_control_index)


if __name__ == "__main__":
    unittest.main()
