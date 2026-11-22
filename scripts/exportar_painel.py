"""Gera as imagens PNG de cada página a partir do PDF exportado pelo Power BI Desktop.

Uso:
    python scripts/exportar_painel.py

Lê docs/painel/painel.pdf (exportado do Power BI Desktop em Arquivo > Exportar > Exportar em PDF)
e grava quatro PNGs em alta definição em docs/painel/:

    1-visao-executiva.png
    2-logistica-sla.png
    3-comercial-clientes.png
    4-qualidade-linhagem.png
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import pypdfium2

RAIZ = Path(__file__).resolve().parents[1]
PASTA_PADRAO = RAIZ / "docs" / "painel"
PAGINAS = [
    "Visão executiva",
    "Logística SLA",
    "Comercial clientes",
    "Qualidade linhagem",
]
ESCALA = 2


def nome_de_arquivo(posicao: int, titulo: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode()
    return f"{posicao}-{re.sub(r'[^a-z0-9]+', '-', sem_acento.lower()).strip('-')}.png"


def exportar(pdf: Path, pasta_saida: Path, escala: int = ESCALA) -> list[Path]:
    documento = pypdfium2.PdfDocument(pdf)
    if len(documento) != len(PAGINAS):
        raise ValueError(
            f"{pdf.name} tem {len(documento)} páginas; o painel tem {len(PAGINAS)}."
        )
    pasta_saida.mkdir(parents=True, exist_ok=True)
    gerados: list[Path] = []
    for posicao, (pagina, titulo) in enumerate(zip(documento, PAGINAS), start=1):
        destino = pasta_saida / nome_de_arquivo(posicao, titulo)
        pagina.render(scale=escala).to_pil().save(destino, optimize=True)
        gerados.append(destino)
    return gerados


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--pdf",
        type=Path,
        default=PASTA_PADRAO / "painel.pdf",
        help="caminho do PDF exportado pelo Power BI Desktop",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=PASTA_PADRAO,
        help="pasta de saída das imagens PNG (padrão: docs/painel)",
    )
    parser.add_argument("--escala", type=int, default=ESCALA, help="fator de escala (padrão: 2)")
    opcoes = parser.parse_args()
    try:
        gerados = exportar(opcoes.pdf, opcoes.saida, opcoes.escala)
    except Exception as exc:
        print(f"Erro ao exportar imagens: {exc}", file=sys.stderr)
        return 1
    for arq in gerados:
        try:
            print(arq.relative_to(RAIZ))
        except ValueError:
            print(arq)
    return 0


if __name__ == "__main__":
    sys.exit(main())
