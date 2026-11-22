"""Verificações de higiene do repositório, licenças, atribuições e privacidade (zero PII)."""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

LIMITE_ARQUIVO_BYTES = 25 * 1024 * 1024  # 25 MB (evita blobs gigantes no git)
PASTAS_IGNORADAS = {".git", ".pytest_cache", "__pycache__", ".venv", "venv", ".pbi"}
EXTENSOES_TEXTO = {
    ".py", ".sql", ".md", ".json", ".tmdl", ".dax", ".yml", ".yaml",
    ".html", ".css", ".js", ".ini", ".txt", ".ps1",
}


def arquivos_versionaveis():
    for caminho in sorted(RAIZ.rglob("*")):
        if not caminho.is_file():
            continue
        partes = set(caminho.relative_to(RAIZ).parts)
        if partes & PASTAS_IGNORADAS:
            continue
        rel = caminho.relative_to(RAIZ).as_posix()
        if rel.startswith("data/raw/") or rel.endswith((".sqlite", ".sqlite3")):
            continue
        yield rel, caminho


def test_nenhum_arquivo_versionavel_passa_de_25mb():
    grandes = [
        (rel, caminho.stat().st_size)
        for rel, caminho in arquivos_versionaveis()
        if caminho.stat().st_size > LIMITE_ARQUIVO_BYTES
    ]
    assert not grandes, f"Arquivos acima de 25 MB fora do .gitignore: {grandes}"


def test_gitignore_ignora_raw_sqlite_e_pbi():
    gi = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    assert "data/raw/" in gi
    assert "*.sqlite" in gi
    pbi_gi = (RAIZ / "powerbi" / ".gitignore").read_text(encoding="utf-8")
    assert ".pbi" in pbi_gi


def test_licenca_mit_valida():
    lic = (RAIZ / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in lic
    assert "Rafael Balchuna" in lic
    assert "Permission is hereby granted, free of charge" in lic


def test_zero_caminhos_pessoais_ou_segredos_em_arquivos_de_texto():
    padrao_usuario = re.compile(r"[A-Za-z]:\\Users\\[A-Za-z0-9_][A-Za-z0-9._-]*", re.IGNORECASE)
    padrao_chave = re.compile(r"(ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})")
    for rel, caminho in arquivos_versionaveis():
        if caminho.suffix.lower() not in EXTENSOES_TEXTO:
            continue
        if rel == "tests/test_higiene_repo.py":
            continue
        texto = caminho.read_text(encoding="utf-8", errors="replace")
        assert not padrao_usuario.search(texto), f"Caminho de usuário local vazou em {rel}"
        assert not padrao_chave.search(texto), f"Possível token/segredo encontrado em {rel}"


def test_readme_e_fontes_tem_atribuicoes_olist_bcb_ibge():
    readme = RAIZ / "README.md"
    assert readme.is_file(), "README.md ausente"
    texto = readme.read_text(encoding="utf-8")
    assert "## English summary" in texto or "English summary" in texto
    assert "Olist" in texto and "CC BY-NC-SA 4.0" in texto
    assert "Banco Central" in texto and "433" in texto and "432" in texto
    assert "IBGE" in texto
    assert "MIT" in texto
