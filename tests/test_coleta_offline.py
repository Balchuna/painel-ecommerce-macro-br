"""Testes 100% offline da coleta (Olist, BCB SGS, IBGE), rate-limit e deflator IPCA.

Nenhuma chamada real de rede é feita: todas as respostas HTTP são simuladas
e o relógio/sleep do cliente HTTP são controlados para provar o respeito
ao intervalo mínimo entre requisições, retries e tratamento de erros.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from scripts.coletar_dados import (
    coletar_bcb,
    coletar_ibge,
    coletar_olist,
    coletar_tudo,
    validar_csv_baixado,
    validar_json_baixado,
)
from src.constantes import BCB_SERIES, IBGE_ENDPOINTS, OLIST_ARQUIVOS, USER_AGENT
from src.deflator import (
    agregar_serie_diaria_por_mes,
    calcular_deflator_ipca,
    calcular_ipca_acumulado,
    parse_data_bcb,
    parse_valor_bcb,
)
from src.http_cliente import ErroDeColeta, HttpCliente


class SessaoFalsa:
    """Stub determinístico de requests.Session para testes sem rede."""

    def __init__(self, handler):
        self.headers: dict[str, str] = {}
        self.chamadas: list[tuple[str, float]] = []
        self._handler = handler

    def get(self, url: str, timeout: float = 30.0):
        self.chamadas.append((url, timeout))
        return self._handler(url, len(self.chamadas))


def resposta(status: int, conteudo: bytes | str):
    corpo = conteudo.encode("utf-8") if isinstance(conteudo, str) else conteudo
    return SimpleNamespace(status_code=status, content=corpo)


# ---------------------------------------------------------------------------------------------
# Cliente HTTP: rate limit, retry, cache e tratamento de erro


def test_http_cliente_respeita_rate_limit_e_define_user_agent():
    tempo = [10.0]
    pausas: list[float] = []

    def relogio() -> float:
        return tempo[0]

    def dormir(seg: float) -> None:
        pausas.append(seg)
        tempo[0] += seg

    sessao = SessaoFalsa(lambda url, n: resposta(200, f"ok-{n}"))
    cliente = HttpCliente(
        atraso_s=0.4,
        sessao=sessao,
        relogio=relogio,
        dormir=dormir,
    )

    assert sessao.headers["User-Agent"] == USER_AGENT

    assert cliente.buscar_bytes("https://exemplo.test/1") == (b"ok-1", 200)
    # 0.1s depois da primeira requisição -> precisa dormir 0.3s para completar 0.4s
    tempo[0] += 0.1
    assert cliente.buscar_bytes("https://exemplo.test/2") == (b"ok-2", 200)
    # 1.0s depois -> já passou do atraso mínimo, não precisa dormir
    tempo[0] += 1.0
    assert cliente.buscar_bytes("https://exemplo.test/3") == (b"ok-3", 200)

    assert len(pausas) == 1
    assert pausas[0] == pytest.approx(0.3, abs=1e-6)


@pytest.mark.parametrize("status_transitorio", [429, 500, 503])
def test_http_cliente_faz_retry_em_erros_transitorios_e_recupera(status_transitorio):
    pausas: list[float] = []

    def handler(url, n):
        if n < 3:
            return resposta(status_transitorio, "temporariamente indisponivel")
        return resposta(200, "recuperado")

    sessao = SessaoFalsa(handler)
    cliente = HttpCliente(
        atraso_s=0.0,
        tentativas=3,
        sessao=sessao,
        relogio=lambda: 0.0,
        dormir=pausas.append,
    )
    conteudo, status = cliente.buscar_bytes("https://api.bcb.gov.br/teste")
    assert (conteudo, status) == (b"recuperado", 200)
    assert len(sessao.chamadas) == 3
    assert len(pausas) == 2
    assert pausas[1] > pausas[0]


@pytest.mark.parametrize("status_definitivo", [400, 403, 404])
def test_http_cliente_nao_repassa_erros_4xx_definitivos(status_definitivo):
    pausas: list[float] = []
    sessao = SessaoFalsa(lambda url, n: resposta(status_definitivo, "erro"))
    cliente = HttpCliente(
        atraso_s=0.0,
        tentativas=3,
        sessao=sessao,
        relogio=lambda: 0.0,
        dormir=pausas.append,
    )
    with pytest.raises(ErroDeColeta, match=f"HTTP {status_definitivo}"):
        cliente.buscar_bytes("https://api.bcb.gov.br/inexistente")
    assert len(sessao.chamadas) == 1
    assert pausas == []


def test_http_cliente_trata_timeout_e_esgota_tentativas():
    pausas: list[float] = []

    def handler(url, n):
        raise requests.Timeout("tempo esgotado")

    sessao = SessaoFalsa(handler)
    cliente = HttpCliente(
        atraso_s=0.0,
        tentativas=3,
        sessao=sessao,
        relogio=lambda: 0.0,
        dormir=pausas.append,
    )
    with pytest.raises(ErroDeColeta, match="3 tentativas"):
        cliente.buscar_bytes("https://servicodados.ibge.gov.br/lento")
    assert len(sessao.chamadas) == 3
    assert len(pausas) == 2


def test_http_cliente_valida_parametros_invalidos():
    with pytest.raises(ValueError):
        HttpCliente(atraso_s=-0.1)
    with pytest.raises(ValueError):
        HttpCliente(tentativas=0)


def test_baixar_arquivo_reutiliza_cache_e_forca_quando_pedido(tmp_path):
    sessao = SessaoFalsa(lambda url, n: resposta(200, f"versao-{n}"))
    cliente = HttpCliente(atraso_s=0.0, sessao=sessao, relogio=lambda: 0.0, dormir=lambda _: None)
    destino = tmp_path / "amostra.csv"

    r1 = cliente.baixar_arquivo("https://exemplo.test/a.csv", destino, fonte="olist")
    assert not r1.cache_reutilizado
    assert r1.sha256 == hashlib.sha256(b"versao-1").hexdigest()
    assert len(sessao.chamadas) == 1

    r2 = cliente.baixar_arquivo("https://exemplo.test/a.csv", destino, fonte="olist")
    assert r2.cache_reutilizado
    assert r2.sha256 == r1.sha256
    assert len(sessao.chamadas) == 1

    r3 = cliente.baixar_arquivo("https://exemplo.test/a.csv", destino, fonte="olist", forcar=True)
    assert not r3.cache_reutilizado
    assert r3.sha256 == hashlib.sha256(b"versao-2").hexdigest()
    assert len(sessao.chamadas) == 2


# ---------------------------------------------------------------------------------------------
# Coleta completa mockada (Olist + BCB SGS + IBGE) e validações de integridade


def test_coletar_tudo_mockado_grava_arquivos_e_manifesto(tmp_path):
    bcb_json = json.dumps([{"data": "01/10/2018", "valor": "0.45"}])
    ibge_estados = json.dumps([{"id": 35, "sigla": "SP", "nome": "São Paulo", "regiao": {"sigla": "SE", "nome": "Sudeste"}}])
    ibge_pop = json.dumps([{"id": "9324", "resultados": [{"series": [{"localidade": {"id": "35"}, "serie": {"2018": "45538936"}}]}]}])

    def handler(url, n):
        if "api.bcb.gov.br" in url:
            return resposta(200, bcb_json)
        if "localidades/estados" in url:
            return resposta(200, ibge_estados)
        if "agregados" in url:
            return resposta(200, ibge_pop)
        if url.endswith(".csv"):
            return resposta(200, "col_a,col_b\n1,2\n")
        return resposta(404, "nao mapeado")

    tempo = [0.0]
    pausas: list[float] = []

    def dormir(s: float) -> None:
        pausas.append(s)
        tempo[0] += s

    sessao = SessaoFalsa(handler)
    cliente = HttpCliente(atraso_s=0.25, sessao=sessao, relogio=lambda: tempo[0], dormir=dormir)

    manifesto = coletar_tudo(tmp_path, cliente, forcar=False, incluir_olist=True)

    total_esperado = len(OLIST_ARQUIVOS) + 2 * len(BCB_SERIES) + len(IBGE_ENDPOINTS)
    assert len(manifesto["arquivos"]) == total_esperado
    assert len(sessao.chamadas) == total_esperado
    # Entre N requisições sequenciais no mesmo instante virtual, há N-1 pausas de rate-limit
    assert len(pausas) == total_esperado - 1
    assert all(p == pytest.approx(0.25, abs=1e-6) for p in pausas)

    manifesto_disco = json.loads((tmp_path / "manifesto_coleta.json").read_text(encoding="utf-8"))
    assert set(manifesto_disco["licencas"]) == {"olist", "bcb", "ibge"}
    assert "CC BY-NC-SA 4.0" in manifesto_disco["licencas"]["olist"]
    for item in manifesto_disco["arquivos"]:
        caminho = tmp_path / item["arquivo"]
        assert caminho.is_file()
        assert hashlib.sha256(caminho.read_bytes()).hexdigest() == item["sha256"]


def test_coletar_sem_olist_baixa_apenas_bcb_e_ibge(tmp_path):
    sessao = SessaoFalsa(lambda url, n: resposta(200, json.dumps([{"data": "01/10/2018", "valor": "1.0"}])))
    cliente = HttpCliente(atraso_s=0.0, sessao=sessao, relogio=lambda: 0.0, dormir=lambda _: None)

    manifesto = coletar_tudo(tmp_path, cliente, incluir_olist=False)
    fontes = {item["fonte"] for item in manifesto["arquivos"]}
    assert fontes == {"bcb", "ibge"}
    assert len(manifesto["arquivos"]) == 2 * len(BCB_SERIES) + len(IBGE_ENDPOINTS)


@pytest.mark.parametrize(
    "conteudo",
    [
        "",
        "version https://git-lfs.github.com/spec/v1\noid sha256:abc\n",
        "<!DOCTYPE html><html><body>404</body></html>",
    ],
)
def test_validar_csv_baixado_rejeita_conteudo_invalido(tmp_path, conteudo):
    caminho = tmp_path / "quebrado.csv"
    caminho.write_text(conteudo, encoding="utf-8")
    with pytest.raises(ErroDeColeta):
        validar_csv_baixado(caminho)


@pytest.mark.parametrize("conteudo", ["not-json", "{}", "[]"])
def test_validar_json_baixado_rejeita_payload_invalido(tmp_path, conteudo):
    caminho = tmp_path / "quebrado.json"
    caminho.write_text(conteudo, encoding="utf-8")
    with pytest.raises(ErroDeColeta):
        validar_json_baixado(caminho)


# ---------------------------------------------------------------------------------------------
# Matemática do deflator IPCA e agregação diária -> mensal


def test_parse_data_e_valor_bcb():
    assert parse_data_bcb("01/10/2018") == ("2018-10-01", "2018-10")
    assert parse_valor_bcb("0,45") == pytest.approx(0.45)
    assert parse_valor_bcb("6.50") == pytest.approx(6.50)
    assert parse_valor_bcb("") is None
    assert parse_valor_bcb(None) is None
    assert parse_valor_bcb("nan") is None


def test_deflator_ipca_encadeado_com_inflacao_e_deflacao():
    # 13 meses consecutivos (2017-10 .. 2018-10), incluindo um mês de deflação (-0,20%)
    taxas = [
        ("01/10/2017", "0.42"),
        ("01/11/2017", "0.28"),
        ("01/12/2017", "0.44"),
        ("01/01/2018", "0.29"),
        ("01/02/2018", "0.32"),
        ("01/03/2018", "0.09"),
        ("01/04/2018", "0.22"),
        ("01/05/2018", "0.40"),
        ("01/06/2018", "1.26"),
        ("01/07/2018", "0.33"),
        ("01/08/2018", "-0.20"),
        ("01/09/2018", "0.48"),
        ("01/10/2018", "0.45"),
    ]
    registros = [{"data": d, "valor": v} for d, v in taxas]
    res = calcular_deflator_ipca(registros, mes_base="2018-10")
    por_mes = {r["ano_mes"]: r for r in res}

    # No mês-base, fator == 1.0 e índice == 100.0
    assert por_mes["2018-10"]["fator_deflator"] == pytest.approx(1.0, abs=1e-6)
    assert por_mes["2018-10"]["indice_ipca_base100"] == pytest.approx(100.0, abs=1e-4)

    # Fator de 2018-09 traz valores de set/18 para out/18 -> (1 + 0.45%)
    assert por_mes["2018-09"]["fator_deflator"] == pytest.approx(1.0045, abs=1e-6)
    # Fator de 2018-07 traz jul/18 para out/18 -> (1 - 0.0020) * (1 + 0.0048) * (1 + 0.0045)
    esperado_jul = 0.9980 * 1.0048 * 1.0045
    assert por_mes["2018-07"]["fator_deflator"] == pytest.approx(esperado_jul, abs=1e-6)
    assert por_mes["2018-07"]["indice_ipca_base100"] == pytest.approx(100.0 / esperado_jul, abs=1e-4)

    # Primeiros 11 meses não têm janela completa de 12 meses
    assert por_mes["2017-10"]["ipca_acum_12m_pct"] is None
    assert por_mes["2018-08"]["ipca_acum_12m_pct"] is None

    # 2018-10 tem janela exata de 2017-11 .. 2018-10 (últimos 12 meses)
    prod_12m = 1.0
    for _, v in taxas[1:]:
        prod_12m *= 1.0 + float(v) / 100.0
    assert por_mes["2018-10"]["ipca_acum_12m_pct"] == pytest.approx((prod_12m - 1.0) * 100.0, abs=0.01)


def test_deflator_recorta_janela_e_valida_mes_base():
    registros = [
        {"data": "01/08/2018", "valor": "0.10"},
        {"data": "01/09/2018", "valor": "0.50"},
        {"data": "01/10/2018", "valor": "1.00"},
    ]
    recorte = calcular_deflator_ipca(
        registros,
        mes_base="2018-10",
        ano_mes_inicio="2018-09",
        ano_mes_fim="2018-10",
    )
    assert [r["ano_mes"] for r in recorte] == ["2018-09", "2018-10"]
    assert recorte[0]["fator_deflator"] == pytest.approx(1.01, abs=1e-6)

    with pytest.raises(ValueError, match="Mês-base"):
        calcular_deflator_ipca(registros, mes_base="2019-01")

    with pytest.raises(ValueError, match="IPCA ausente"):
        calcular_deflator_ipca([{"data": "01/10/2018", "valor": ""}], mes_base="2018-10")


def test_calcular_ipca_acumulado_e_agregacao_diaria():
    assert calcular_ipca_acumulado([
        {"data": "01/01/2018", "valor": "1.00"},
        {"data": "01/02/2018", "valor": "2.00"},
    ]) == pytest.approx(3.02, abs=1e-4)

    with pytest.raises(ValueError):
        calcular_ipca_acumulado([])

    mensal = agregar_serie_diaria_por_mes([
        {"data": "01/09/2018", "valor": "6.50"},
        {"data": "15/09/2018", "valor": "6,50"},
        {"data": "01/10/2018", "valor": "6.00"},
        {"data": "02/10/2018", "valor": "7.00"},
        {"data": "03/10/2018", "valor": ""},
    ])
    assert mensal == {"2018-09": 6.5, "2018-10": 6.5}
