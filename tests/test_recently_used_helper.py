"""Tests for _get_recent_models helper and sectioned model selector."""

from unittest.mock import patch, MagicMock
import pytest


class TestGetRecentModels:
    """Tests for _get_recent_models()."""

    def test_global_mode_passes_limit_to_db(self):
        from hermes_cli.auth import _get_recent_models

        mock_db = MagicMock()
        mock_db.recently_used_models.return_value = ["m-a", "m-b", "m-c"]

        with patch("hermes_state.SessionDB", return_value=mock_db):
            result = _get_recent_models(limit=3)

        mock_db.recently_used_models.assert_called_once_with(limit=3, provider=None)
        assert result == ["m-a", "m-b", "m-c"]

    def test_provider_filtered(self):
        from hermes_cli.auth import _get_recent_models

        mock_db = MagicMock()
        mock_db.recently_used_models.return_value = ["m-a", "m-c"]

        with patch("hermes_state.SessionDB", return_value=mock_db):
            result = _get_recent_models(provider="openrouter", limit=5)

        mock_db.recently_used_models.assert_called_once_with(limit=5, provider="openrouter")
        assert result == ["m-a", "m-c"]

    def test_returns_empty_on_db_error(self):
        from hermes_cli.auth import _get_recent_models

        with patch("hermes_state.SessionDB", side_effect=Exception("DB error")):
            result = _get_recent_models(limit=3)

        assert result == []


class TestPromptModelSelectionSections:
    """Tests for _prompt_model_selection() with provider_recent sections."""

    def test_no_duplicates_between_sections(self, capsys):
        """Models in recent section should not appear in all models section."""
        from hermes_cli.auth import _prompt_model_selection

        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    ["m-a", "m-b", "m-c", "m-d"],
                    current_model="m-a",
                    provider_recent=["m-a", "m-b"],
                    provider_label="Test",
                )

        output = capsys.readouterr().out
        lines = output.strip().split("\n")
        model_lines = [l.strip() for l in lines if l.strip() and l.strip()[0].isdigit()]
        model_names = [l.split(". ", 1)[1].split("  ←")[0].strip() for l in model_lines if ". " in l]
        # No duplicates
        assert len(model_names) == len(set(model_names))

    def test_cap_15_models(self, capsys):
        """Total model entries should never exceed 15."""
        from hermes_cli.auth import _prompt_model_selection

        models = [f"model-{i}" for i in range(25)]
        recent = [f"model-{i}" for i in range(8)]

        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    models,
                    provider_recent=recent,
                    provider_label="Test",
                )

        output = capsys.readouterr().out
        lines = output.strip().split("\n")
        numbered = [l for l in lines if l.strip() and l.strip()[0].isdigit()]
        # Subtract 2 for "Enter custom model name" and "Skip"
        model_count = len(numbered) - 2
        assert model_count <= 15

    def test_ratio_recent_le_5(self, capsys):
        """Recent section should have at most 5 models (15 // 3 = 5)."""
        from hermes_cli.auth import _prompt_model_selection

        models = [f"model-{i}" for i in range(20)]
        recent = [f"model-{i}" for i in range(10)]

        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    models,
                    provider_recent=recent,
                    provider_label="Test",
                )

        output = capsys.readouterr().out
        lines = output.strip().split("\n")
        in_recent = False
        recent_count = 0
        for line in lines:
            if "Recent" in line and "──" in line:
                in_recent = True
                continue
            if "All Models" in line and "──" in line:
                break
            if in_recent and line.strip() and line.strip()[0].isdigit():
                recent_count += 1
        assert recent_count <= 5

    def test_no_sections_when_empty(self, capsys):
        """When provider_recent is None, no section headers should appear."""
        from hermes_cli.auth import _prompt_model_selection

        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    ["model-a", "model-b"],
                    current_model="model-a",
                )

        output = capsys.readouterr().out
        assert "──" not in output

    def test_fallback_shows_section_headers(self, capsys):
        """Numbered list fallback should show Recent and All Models headers."""
        from hermes_cli.auth import _prompt_model_selection

        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    ["model-a", "model-b"],
                    current_model="model-a",
                    provider_recent=["model-a"],
                    provider_label="TestProvider",
                )

        output = capsys.readouterr().out
        assert "Recent (TestProvider)" in output
        assert "All Models" in output


class TestModelSelectionsDB:
    """Tests for record_model_selection and recently_used_models with model_selections table."""

    def test_record_and_retrieve(self, tmp_path):
        from hermes_state import SessionDB
        db = SessionDB(db_path=tmp_path / "test.db")

        db.record_model_selection("model-a", provider="openrouter")
        db.record_model_selection("model-b", provider="openrouter")
        db.record_model_selection("model-c", provider="anthropic")

        # Global query
        result = db.recently_used_models(limit=10)
        assert result == ["model-c", "model-b", "model-a"]

        # Provider-filtered query
        result = db.recently_used_models(limit=10, provider="openrouter")
        assert result == ["model-b", "model-a"]

        result = db.recently_used_models(limit=10, provider="anthropic")
        assert result == ["model-c"]

        db.close()

    def test_deduplication_in_selections(self, tmp_path):
        from hermes_state import SessionDB
        import time
        db = SessionDB(db_path=tmp_path / "test.db")

        db.record_model_selection("model-a", provider="openrouter")
        time.sleep(0.01)
        db.record_model_selection("model-b", provider="openrouter")
        time.sleep(0.01)
        db.record_model_selection("model-a", provider="openrouter")

        result = db.recently_used_models(limit=10, provider="openrouter")
        # model-a should be first (most recent), model-b second
        assert result == ["model-a", "model-b"]
        db.close()

    def test_fallback_to_sessions(self, tmp_path):
        """When no model_selections exist, falls back to sessions table."""
        from hermes_state import SessionDB
        db = SessionDB(db_path=tmp_path / "test.db")

        # No model_selections, but sessions have models
        db._conn.execute(
            "INSERT INTO sessions (id, source, model, started_at) VALUES (?, ?, ?, ?)",
            ("s1", "cli", "legacy-model", 1000.0),
        )
        db._conn.commit()

        result = db.recently_used_models(limit=10)
        assert result == ["legacy-model"]
        db.close()

    def test_empty_model_ignored(self, tmp_path):
        from hermes_state import SessionDB
        db = SessionDB(db_path=tmp_path / "test.db")

        db.record_model_selection("", provider="openrouter")
        db.record_model_selection("model-a", provider="openrouter")

        result = db.recently_used_models(limit=10)
        assert result == ["model-a"]
        db.close()
