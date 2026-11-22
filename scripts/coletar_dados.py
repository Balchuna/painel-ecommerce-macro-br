"""Coleta dados públicos reais do painel: Olist, Banco Central (SGS) e IBGE.

Fontes consultadas (todas públicas e sem necessidade de chave de API):
  1. Olist Brazilian E-Commerce Public Dataset (8 CSVs oficiais em olist/work-at-olist-data, CC BY-NC-SA 4.0)
  2. Banco Central do Brasil — API SGS:
     - Série 433: IPCA variação mensal (%)
     - Série 432: Meta Selic definida pelo Copom (% a.a.)
     - Série 1:   Dólar comercial PTAX venda (R$/US$)
     Coleta a janela completa da Olist (2016-09 a 2018-10, com 12m prévios de IPCA)
     e um retrato recente de benchmark macroeconômico.
  3. IBGE — API de Localidades (estados e macrorregiões) e API SIDRA Agregados:
     - Agregado 6579 / var 9324: População residente estimada por UF (2018 — contemporânea à base Olist)
     - Agregado 4714 / var 93:   População residente Censo 2022 por UF (referência oficial mais recente)

Os arquivos ficam em data/raw/ (no .gitignore) com manifesto_coleta.json registrando
URLs exatas, timestamps UTC, hashes SHA-256, tamanhos e licenças.

Uso:
  python scripts/coletar_dados.py
  python scripts/coletar_dados.py --forcar --atraso 0.5
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.constantes import (
    ATRASO_PADRAO_S,
    BCB_SERIES,
    BCB_SGS_ULTIMOS_URL,
    BCB_SGS_URL,
    IBGE_ENDPOINTS,
    LICENCAS_FONTES,
    OLIST_ARQUIVOS,
    OLIST_BASE_URL,
)
from src.http_cliente import ErroDeColeta, HttpCliente, RegistroDownload

RAW_PADRAO = RAIZ / "data" / "raw"


def validar_json_baixado(caminho: Path) -> None:
    """Confirma que o arquivo baixado é JSON válido e não vazio."""
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ErroDeColeta(f"JSON inválido em {caminho.name}: {exc}") from exc
    if not isinstance(dados, list) or len(dados) == 0:
        raise ErroDeColeta(f"Resposta JSON vazia ou inesperada em {caminho.name}")


def validar_csv_baixado(caminho: Path) -> None:
    """Confirma que o CSV começa com cabeçalho válido e não é ponteiro LFS ou HTML."""
    with open(caminho, "r", encoding="utf-8-sig", errors="replace") as f:
        primeira_linha = f.readline().strip()
    if not primeira_linha or primeira_linha.startswith("version https://git-lfs"):
        raise ErroDeColeta(f"Arquivo {caminho.name} inválido ou ponteiro Git LFS")
    if primeira_linha.lstrip().startswith("<"):
        raise ErroDeColeta(f"Arquivo {caminho.name} retornou HTML em vez de CSV")


def coletar_bcb(
    saida: Path,
    cliente: HttpCliente,
    forcar: bool = False,
) -> list[RegistroDownload]:
    registros: list[RegistroDownload] = []
    for chave, spec in BCB_SERIES.items():
        url_hist = BCB_SGS_URL.format(
            codigo=spec["codigo"],
            inicio=spec["inicio"],
            fim=spec["fim"],
        )
        dest_hist = saida / f"bcb_{chave}_historico.json"
        reg = cliente.baixar_arquivo(url_hist, dest_hist, fonte="bcb", forcar=forcar)
        validar_json_baixado(dest_hist)
        registros.append(reg)

        url_rec = BCB_SGS_ULTIMOS_URL.format(
            codigo=spec["codigo"],
            n=spec["ultimos"],
        )
        dest_rec = saida / f"bcb_{chave}_recente.json"
        reg_rec = cliente.baixar_arquivo(url_rec, dest_rec, fonte="bcb", forcar=forcar)
        validar_json_baixado(dest_rec)
        registros.append(reg_rec)
    return registros


def coletar_ibge(
    saida: Path,
    cliente: HttpCliente,
    forcar: bool = False,
) -> list[RegistroDownload]:
    registros: list[RegistroDownload] = []
    for chave, url in IBGE_ENDPOINTS.items():
        destino = saida / f"ibge_{chave}.json"
        reg = cliente.baixar_arquivo(url, destino, fonte="ibge", forcar=forcar)
        validar_json_baixado(destino)
        registros.append(reg)
    return registros


def coletar_olist(
    saida: Path,
    cliente: HttpCliente,
    forcar: bool = False,
) -> list[RegistroDownload]:
    registros: list[RegistroDownload] = []
    for nome in OLIST_ARQUIVOS:
        url = f"{OLIST_BASE_URL}/{nome}"
        destino = saida / nome
        reg = cliente.baixar_arquivo(url, destino, fonte="olist", forcar=forcar)
        validar_csv_baixado(destino)
        registros.append(reg)
    return registros


def coletar_tudo(
    saida: Path,
    cliente: HttpCliente,
    forcar: bool = False,
    incluir_olist: bool = True,
) -> dict:
    saida.mkdir(parents=True, exist_ok=True)
    registros: list[RegistroDownload] = []
    if incluir_olist:
        registros.extend(coletar_olist(saida, cliente, forcar=forcar))
    registros.extend(coletar_bcb(saida, cliente, forcar=forcar))
    registros.extend(coletar_ibge(saida, cliente, forcar=forcar))

    manifesto = {
        "gerado_em_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "atraso_rate_limit_s": cliente.atraso_s,
        "licencas": LICENCAS_FONTES,
        "arquivos": [asdict(r) for r in registros],
    }
    manifesto_path = saida / "manifesto_coleta.json"
    manifesto_path.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifesto


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Coleta Olist, BCB SGS (IPCA/Selic/PTAX) e IBGE para data/raw/."
    )
    parser.add_argument("--saida", type=Path, default=RAW_PADRAO)
    parser.add_argument("--forcar", action="store_true", help="Rebaixa arquivos já em cache")
    parser.add_argument("--atraso", type=float, default=ATRASO_PADRAO_S, help="Intervalo mínimo entre requests (s)")
    parser.add_argument("--sem-olist", action="store_true", help="Coleta apenas BCB e IBGE")
    args = parser.parse_args()

    cliente = HttpCliente(atraso_s=args.atraso)
    try:
        manifesto = coletar_tudo(
            args.saida,
            cliente,
            forcar=args.forcar,
            incluir_olist=not args.sem_olist,
        )
    except ErroDeColeta as erro:
        sys.exit(f"erro de coleta: {erro}")

    total_mb = sum(a["bytes_total"] for a in manifesto["arquivos"]) / (1024 * 1024)
    print(f"Coleta concluída em {args.saida} ({len(manifesto['arquivos'])} arquivos, {total_mb:.2f} MB):")
    for item in manifesto["arquivos"]:
        modo = "cache" if item["cache_reutilizado"] else f"HTTP {item['status_http']}"
        kb = item["bytes_total"] / 1024
        print(f"  [{item['fonte']:5s}] {item['arquivo']:42s} {kb:8.1f} KB  ({modo})")


if __name__ == "__main__":
    main()
