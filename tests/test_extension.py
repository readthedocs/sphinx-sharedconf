from unittest import mock

import pytest
from sphinx.testing.path import path as Path

basedir = Path(__file__).parent / "examples"


class TestExtension:
    def _read_text(self, path):
        """Compatible read_text for Sphinx<3."""
        if hasattr(path, "read_text"):
            return path.read_text()
        return path.text()

    @pytest.mark.sphinx("html", srcdir=basedir / "basic")
    def test_build_default_docset(self, app):
        assert list(app.config.sharedconf_docsets.keys())[0] == "api"
        app.build()
        expected_srcdir = basedir / "basic/api"
        assert app.srcdir == str(expected_srcdir)
        out = self._read_text(Path(app.outdir) / "index.html")
        assert "API documentation" in out

    @pytest.mark.parametrize(
        "docset, expected_text",
        [
            ("api", "API documentation"),
            ("dev", "Dev documentation"),
            ("user", "User documentation"),
        ],
    )
    def test_build_docset(self, make_app, monkeypatch, docset, expected_text):
        monkeypatch.setenv("DOCSET", docset)
        app = make_app("html", srcdir=basedir / "basic")
        app.build()
        expected_srcdir = basedir / "basic" / docset
        assert app.srcdir == str(expected_srcdir)
        out = self._read_text(Path(app.outdir) / "index.html")
        assert expected_text in out

    def test_per_docset_settings(self, make_app):
        config = {
            "project": "A project",
            "sharedconf_docsets": {
                "dev": {
                    "config": {
                        "project": "Dev documentation",
                    },
                },
            },
        }
        app = make_app("html", srcdir=basedir / "basic", confoverrides=config)
        app.build()

        assert app.config.project == "Dev documentation"

        out = self._read_text(Path(app.outdir) / "index.html")
        assert "Dev documentation" in out

    def test_custom_docset_path(self, make_app):
        config = {
            "sharedconf_docsets": {
                "dev": {
                    "path": "user",
                },
            },
        }
        app = make_app("html", srcdir=basedir / "basic", confoverrides=config)
        app.build()

        out = self._read_text(Path(app.outdir) / "index.html")
        assert "User documentation" in out

    def test_custom_env_var(self, make_app, monkeypatch):
        monkeypatch.setenv("DOCSET", "dev")
        monkeypatch.setenv("MYDOCSET", "user")
        config = {"sharedconf_env_var": "MYDOCSET"}
        app = make_app("html", srcdir=basedir / "basic", confoverrides=config)
        app.build()

        expected_srcdir = basedir / "basic/user"
        assert app.srcdir == str(expected_srcdir)

        out = self._read_text(Path(app.outdir) / "index.html")
        assert "User documentation" in out

    @mock.patch("sharedconf.extension.log")
    def test_warn_special_settings(self, log, make_app):
        config = {
            "language": "en",
            "sharedconf_docsets": {
                "dev": {
                    "config": {
                        "language": "es",
                    },
                },
            },
        }
        app = make_app("html", srcdir=basedir / "basic", confoverrides=config)
        app.build()

        assert app.config.language == "es"

        log.warning.assert_called_once()
        args, _ = log.warning.call_args
        assert args[0].startswith("Setting the `%s` option inside")
        assert args[1] == "language"

    @pytest.mark.parametrize(
        "docset, expected_text, expected_config",
        [
            (
                "api",
                "API documentation",
                {
                    "language": "en",
                    "suppress_warnings": ["ref.doc"],
                    "locale_dirs": ["locale/api"],
                },
            ),
            (
                "dev",
                "Dev documentation",
                {
                    "language": "es",
                    "suppress_warnings": ["ref.python"],
                    "locale_dirs": ["locales"],
                },
            ),
            (
                "user",
                "User documentation",
                {
                    "language": "de",
                    "suppress_warnings": [],
                    "locale_dirs": ["locale/api"],
                },
            ),
        ],
    )
    def test_conditional_settings(
        self, make_app, monkeypatch, docset, expected_text, expected_config
    ):
        monkeypatch.setenv("DOCSET", docset)
        app = make_app("html", srcdir=basedir / "conditional")
        app.build()

        expected_srcdir = basedir / "conditional" / docset
        assert app.srcdir == str(expected_srcdir)

        out = self._read_text(Path(app.outdir) / "index.html")
        assert expected_text in out

        for k, v in expected_config.items():
            assert app.config[k] == v