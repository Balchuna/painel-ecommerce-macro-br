"""Cálculo do deflator acumulado pelo IPCA (BCB SGS 433) e agregação macro mensal.

Metodologia:
  - Cada mês t possui variação percentual mensal r_t (série 433 do BCB SGS).
  - O índice acumulado encadeado cresce por I_t = I_{t-1} * (1 + r_t / 100).
  - Escolhido um mês-base B (por padrão '2018-10', fim do período Olist):
        fator_deflator_t = I_B / I_t
        valor_real_t     = valor_nominal_t * fator_deflator_t
        indice_base100_t = 100.0 * (I_t / I_B)
  - No mês-base B, fator_deflator == 1.0 e indice_base100 == 100.0.
  - Em meses anteriores com inflação positiva até B, fator_deflator > 1.0,
    trazendo valores nominais antigos para poder de compra constante do mês-base.
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from typing import Iterable


def parse_data_bcb(texto: str) -> tuple[str, str]:
    """Converte 'dd/mm/aaaa' do BCB SGS em ('aaaa-mm-dd', 'aaaa-mm')."""
    dt = datetime.strptime(texto.strip(), "%d/%m/%Y")
    return dt.strftime("%Y-%m-%d"), dt.strftime("%Y-%m")


def parse_valor_bcb(valor: str | float | int | None) -> float | None:
    if valor is None:
        return None
    texto = str(valor).strip().replace(",", ".")
    if not texto:
        return None
    num = float(texto)
    if math.isnan(num) or math.isinf(num):
        return None
    return num


def agregar_serie_diaria_por_mes(registros: Iterable[dict]) -> dict[str, float]:
    """Agrega uma série diária BCB SGS (Selic 432 ou PTAX 1) por média simples mensal."""
    grupos: dict[str, list[float]] = defaultdict(list)
    for item in registros:
        _, ano_mes = parse_data_bcb(item["data"])
        v = parse_valor_bcb(item.get("valor"))
        if v is not None:
            grupos[ano_mes].append(v)
    return {
        ano_mes: round(sum(vals) / len(vals), 4)
        for ano_mes, vals in sorted(grupos.items())
        if vals
    }


def calcular_deflator_ipca(
    registros_ipca: Iterable[dict],
    mes_base: str,
    ano_mes_inicio: str | None = None,
    ano_mes_fim: str | None = None,
) -> list[dict]:
    """Calcula índice acumulado, IPCA 12 meses e fator deflator constante no mês-base.

    Retorna uma lista ordenada por ano_mes com:
      - ano_mes
      - ipca_mensal_pct
      - ipca_acum_12m_pct (None se houver menos de 12 meses acumulados)
      - indice_ipca_base100 (mes_base == 100.0000)
      - fator_deflator (mes_base == 1.000000)
    """
    por_mes: dict[str, float] = {}
    for item in registros_ipca:
        _, ano_mes = parse_data_bcb(item["data"])
        v = parse_valor_bcb(item.get("valor"))
        if v is None:
            raise ValueError(f"IPCA ausente ou inválido em {item}")
        por_mes[ano_mes] = v

    if mes_base not in por_mes:
        raise ValueError(f"Mês-base {mes_base!r} não encontrado na série IPCA")

    meses_ordenados = sorted(por_mes.keys())
    indice_bruto: dict[str, float] = {}
    acum = 1.0
    for m in meses_ordenados:
        acum *= 1.0 + (por_mes[m] / 100.0)
        indice_bruto[m] = acum

    indice_base = indice_bruto[mes_base]

    # IPCA acumulado em 12 meses (janelas móveis exatas de 12 meses consecutivos)
    acum_12m: dict[str, float | None] = {}
    for idx, m in enumerate(meses_ordenados):
        if idx < 11:
            acum_12m[m] = None
        else:
            prod = 1.0
            for j in range(idx - 11, idx + 1):
                prod *= 1.0 + (por_mes[meses_ordenados[j]] / 100.0)
            acum_12m[m] = round((prod - 1.0) * 100.0, 2)

    saida: list[dict] = []
    for m in meses_ordenados:
        if ano_mes_inicio and m < ano_mes_inicio:
            continue
        if ano_mes_fim and m > ano_mes_fim:
            continue
        fator = indice_base / indice_bruto[m]
        idx100 = 100.0 * (indice_bruto[m] / indice_base)
        saida.append({
            "ano_mes": m,
            "ipca_mensal_pct": round(por_mes[m], 2),
            "ipca_acum_12m_pct": acum_12m[m],
            "indice_ipca_base100": round(idx100, 4),
            "fator_deflator": round(fator, 6),
        })
    return saida


def calcular_ipca_acumulado(registros_ipca: Iterable[dict]) -> float:
    """Calcula a variação acumulada composta (%) sobre uma sequência de registros IPCA."""
    prod = 1.0
    count = 0
    for item in registros_ipca:
        v = parse_valor_bcb(item.get("valor"))
        if v is not None:
            prod *= 1.0 + (v / 100.0)
            count += 1
    if count == 0:
        raise ValueError("Nenhum valor válido de IPCA fornecido")
    return round((prod - 1.0) * 100.0, 2)
