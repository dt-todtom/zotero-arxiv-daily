"""Tests for MedrxivRetriever."""

import json

from omegaconf import open_dict

from zotero_arxiv_daily.retriever.medrxiv_retriever import MedrxivRetriever


def test_medrxiv_server_attribute(config):
    with open_dict(config.source):
        config.source.medrxiv = {"category": ["neurology"]}
    retriever = MedrxivRetriever(config)
    assert retriever.server == "medrxiv"


def test_medrxiv_pdf_url(config):
    with open_dict(config.source):
        config.source.medrxiv = {"category": ["neurology"]}
    retriever = MedrxivRetriever(config)
    paper = retriever.convert_to_paper({
        "doi": "10.1101/2026.03.01.999",
        "title": "A medrxiv paper",
        "authors": "Smith, J.",
        "abstract": "Abstract.",
        "version": "1",
    })
    assert "medrxiv.org" in paper.pdf_url
    assert paper.source == "medrxiv"


def test_medrxiv_reuses_biorxiv_fallback_logic(config, monkeypatch):
    import requests
    from types import SimpleNamespace

    urls = []

    def _patched(url, **kw):
        urls.append(url)
        result = SimpleNamespace(status_code=200, raise_for_status=lambda: None)
        result.json = lambda: (_ for _ in ()).throw(json.JSONDecodeError("Expecting value", "", 0))
        return result

    monkeypatch.setattr(requests, "get", _patched)
    monkeypatch.setattr("zotero_arxiv_daily.retriever.biorxiv_retriever.sleep", lambda _: None)

    with open_dict(config.source):
        config.source.medrxiv = {"category": ["neurology"]}
    retriever = MedrxivRetriever(config)

    assert retriever._retrieve_raw_papers() == []
    assert urls
    assert all("/details/medrxiv/2d" in url for url in urls)
