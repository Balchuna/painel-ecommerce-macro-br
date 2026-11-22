"""Monta o banco SQLite a partir de data/limpa/*.csv e gera o gabarito SQL em sql/gabarito/.

Passo a passo:
  1. recria o banco (--banco) aplicando sql/01_tabelas.sql com PRAGMA foreign_keys = ON;
  2. carrega os 11 CSVs do Star Schema na ordem de chaves estrangeiras;
  3. cria as views analíticas de sql/02_views.sql;
  4. executa cada consulta em sql/consultas/*.sql e grava o resultado CSV em --gabarito.

Uso:
  python scripts/gerar_gabarito.py
  python scripts/gerar_gabarito.py --limpa outra/limpa --gabarito outro/gabarito
"""
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SQL = RAIZ / "sql"
LIMPA_PADRAO = RAIZ / "data" / "limpa"
BANCO_PADRAO = RAIZ / "data" / "painel.sqlite"
GABARITO_PADRAO = SQL / "gabarito"

# Ordem das chaves estrangeiras: dimensões antes dos fatos.
ORDEM_DE_CARGA = [
    "dim_macro_mensal",
    "dim_calendario",
    "dim_geo_uf",
    "dim_categoria",
    "dim_faixa_atraso",
    "dim_vendedor",
    "fato_pedidos",
    "fato_itens_pedido",
    "qualidade_auditoria",
    "fontes_metadados",
    "macro_benchmark_atual",
]
NOME_DE_COLUNA = re.compile(r"[a-z_][a-z0-9_]*")
SQLITE_MINIMO = (3, 35)  # funções de janela + CTEs aninhadas


class ErroDeCarga(Exception):
    """CSV da camada limpa violou alguma regra de integridade das tabelas."""


def carregar_csv(banco: sqlite3.Connection, tabela: str, caminho: Path) -> int:
    if not caminho.is_file():
        raise ErroDeCarga(f"não achei {caminho}")
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        colunas = next(leitor)
        linhas = [[valor if valor != "" else None for valor in linha] for linha in leitor]
    invalidas = [c for c in colunas if not NOME_DE_COLUNA.fullmatch(c)]
    if invalidas:
        raise ErroDeCarga(f"{caminho.name}: cabeçalho inesperado {invalidas}")
    comando = (
        f"INSERT INTO {tabela} ({', '.join(colunas)}) "
        f"VALUES ({', '.join('?' * len(colunas))})"
    )
    try:
        banco.executemany(comando, linhas)
    except sqlite3.Error as erro:
        raise ErroDeCarga(f"{caminho.name} quebra uma regra das tabelas: {erro}") from None
    return len(linhas)


def montar_banco(caminho: Path, limpa: Path) -> sqlite3.Connection:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.unlink(missing_ok=True)
    banco = sqlite3.connect(caminho)
    banco.execute("PRAGMA foreign_keys = ON")
    try:
        banco.executescript((SQL / "01_tabelas.sql").read_text(encoding="utf-8"))
        with banco:
            for tabela in ORDEM_DE_CARGA:
                carregar_csv(banco, tabela, limpa / f"{tabela}.csv")
        banco.executescript((SQL / "02_views.sql").read_text(encoding="utf-8"))
    except (ErroDeCarga, sqlite3.Error) as erro:
        banco.close()
        caminho.unlink(missing_ok=True)
        if isinstance(erro, ErroDeCarga):
            raise
        raise ErroDeCarga(f"falha ao aplicar SQL no banco: {erro}") from None
    return banco


def gravar_resultado(cursor: sqlite3.Cursor, caminho: Path) -> int:
    colunas = [descricao[0] for descricao in cursor.description]
    linhas = cursor.fetchall()
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(colunas)
        escritor.writerows(["" if v is None else v for v in linha] for linha in linhas)
    return len(linhas)


def gerar_todos_gabaritos(limpa: Path, banco_path: Path, gabarito: Path) -> dict[str, int]:
    banco = montar_banco(banco_path, limpa)
    contagens: dict[str, int] = {}
    try:
        gabarito.mkdir(parents=True, exist_ok=True)
        for consulta in sorted((SQL / "consultas").glob("*.sql")):
            cursor = banco.execute(consulta.read_text(encoding="utf-8"))
            contagens[consulta.stem] = gravar_resultado(cursor, gabarito / f"{consulta.stem}.csv")
    finally:
        banco.close()
    return contagens


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Monta SQLite e gera o gabarito SQL.")
    parser.add_argument("--limpa", type=Path, default=LIMPA_PADRAO)
    parser.add_argument("--banco", type=Path, default=BANCO_PADRAO)
    parser.add_argument("--gabarito", type=Path, default=GABARITO_PADRAO)
    args = parser.parse_args()

    if sqlite3.sqlite_version_info < SQLITE_MINIMO:
        sys.exit(
            f"erro: as consultas pedem SQLite {'.'.join(map(str, SQLITE_MINIMO))}+; "
            f"este Python traz o {sqlite3.sqlite_version}"
        )

    try:
        contagens = gerar_todos_gabaritos(args.limpa, args.banco, args.gabarito)
    except ErroDeCarga as erro:
        sys.exit(f"erro: {erro}")

    print(f"Banco montado em {args.banco}. Gabarito gravado em {args.gabarito}:")
    for nome, qtd in contagens.items():
        print(f"  {nome}.csv: {qtd} linhas")

    # Resumo executivo direto do banco
    banco = sqlite3.connect(args.banco)
    banco.row_factory = sqlite3.Row
    try:
        visao = dict(banco.execute(
            (SQL / "consultas" / "01_visao_executiva.sql").read_text(encoding="utf-8")
        ).fetchone())
    finally:
        banco.close()

    print()
    print("Resumo executivo (pedidos entregues, R$ constantes de 2018-10):")
    print(f"  Pedidos brutos: {visao['pedidos_brutos']:,} | Entregues: {visao['pedidos_entregues']:,} ({100 - visao['pct_excluidos']:.2f}%)")
    print(f"  GMV Nominal: R$ {visao['gmv_nominal']:,.2f} | GMV Real (IPCA): R$ {visao['gmv_real_ipca']:,.2f}")
    print(f"  Ticket Médio Real: R$ {visao['ticket_medio_real']:,.2f} | Frete % GMV: {visao['pct_frete_gmv']:.2f}%")
    print(f"  No prazo: {visao['pct_no_prazo']:.2f}% | Prazo médio: {visao['prazo_medio_dias']:.2f}d | Nota média: {visao['nota_media']:.2f}★")
    print(f"  Nota no prazo: {visao['nota_media_no_prazo']:.2f}★ vs Atrasado: {visao['nota_media_atrasado']:.2f}★ (queda {visao['queda_nota_atraso']:.2f}★)")
    print(f"  Recompra clientes: {visao['pct_clientes_recompra']:.2f}% | Top 10% vendedores: {visao['pct_gmv_top10_vendedores']:.2f}% | Pareto 80%: {visao['categorias_80pct_gmv']} categorias")
    print(f"  YoY Jan–Ago 2018 vs 2017: Nominal +{visao['var_gmv_nominal_yoy_jan_ago_pct']:.2f}% | Real +{visao['var_gmv_real_yoy_jan_ago_pct']:.2f}% (inflação: {visao['efeito_inflacao_yoy_pp']:.2f} p.p.)")


if __name__ == "__main__":
    main()
