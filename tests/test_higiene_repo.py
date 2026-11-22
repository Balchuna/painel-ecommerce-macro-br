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


def test_padrao_bi_estrutura_arquivos_e_sem_exemplos():
    obrigatorios = [
        "marca/tokens.json",
        "marca/gerar.py",
        "marca/REGRAS.md",
        "marca/tokens.css",
        "marca/powerbi/tema-azul-claro.json",
        "DESIGN.md",
        ".unslop-ui/taste.md",
        "AGENTS.md",
        "GEMINI.md",
        "docs/marca/tokens.css",
        "docs/dados/resumo.js",
    ]
    for rel in obrigatorios:
        assert (RAIZ / rel).is_file(), f"Arquivo obrigatório do Padrão BI ausente: {rel}"

    assert not (RAIZ / "exemplos").exists(), "A pasta exemplos/ do Padrão BI não deve ser copiada para o projeto"
    agents = (RAIZ / "AGENTS.md").read_text(encoding="utf-8")
    assert "--acento azul" in agents and "azul" in agents, "AGENTS.md deve declarar o acento azul"
    assert (RAIZ / "GEMINI.md").read_text(encoding="utf-8").strip() == "@./AGENTS.md"


def test_padrao_bi_zero_hex_fora_de_marca_e_conformidade_docs():
    hex6 = re.compile(r"#[0-9a-fA-F]{6}")
    # Regra estrita: zero hex escrito à mão em docs/*.html, docs/*.css, docs/*.js, docs/DESIGN_SPEC.md, scripts/montar_pbip.py
    alvos_zero_hex = [
        *sorted((RAIZ / "docs").glob("*.html")),
        *sorted((RAIZ / "docs").glob("*.css")),
        *sorted((RAIZ / "docs").glob("*.js")),
        RAIZ / "docs" / "DESIGN_SPEC.md",
        RAIZ / "scripts" / "montar_pbip.py",
    ]
    for caminho in alvos_zero_hex:
        achados = hex6.findall(caminho.read_text(encoding="utf-8"))
        assert not achados, f"Hex escrito à mão fora de marca/ em {caminho.relative_to(RAIZ)}: {achados}"

    # Verificação equivalente ao grep de marca/REGRAS.md em todo o repositório (*.html, *.css, *.qmd)
    permitidos_gerados = {"marca/tokens.css", "docs/marca/tokens.css"}
    for ext in ("*.html", "*.css", "*.qmd"):
        for caminho in sorted(RAIZ.rglob(ext)):
            rel = caminho.relative_to(RAIZ).as_posix()
            if "_files/" in rel or ".git/" in rel or rel in permitidos_gerados:
                continue
            achados = hex6.findall(caminho.read_text(encoding="utf-8", errors="replace"))
            assert not achados, f"Hex fora dos arquivos gerados em {rel}: {achados}"

    # Conformidade .unslop-ui/taste.md em DESIGN_SPEC.md, README.md e dax/medidas.dax
    palavras_proibidas = re.compile(r"\b(insights?|jornada|potencializar|alavancar|storytelling)\b", re.I)
    icones_unicode = re.compile(r"[▲▼→●✓★]")
    for rel in ("docs/DESIGN_SPEC.md", "README.md", "dax/medidas.dax"):
        texto = (RAIZ / rel).read_text(encoding="utf-8")
        sem_imgs = re.sub(r"!\[", "[", texto)
        assert not palavras_proibidas.search(texto), f"Palavra proibida em {rel}: {palavras_proibidas.findall(texto)}"
        assert not icones_unicode.search(texto), f"Ícone unicode proibido em {rel}"
        assert "—" not in texto, f"Travessão proibido em {rel}"
        assert "!" not in sem_imgs, f"Ponto de exclamação proibido em {rel}"
