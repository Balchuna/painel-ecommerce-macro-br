"""Cliente HTTP educado com controle de taxa, retries e hash SHA-256."""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import requests

from src.constantes import (
    ATRASO_PADRAO_S,
    TENTATIVAS_PADRAO,
    TIMEOUT_PADRAO_S,
    USER_AGENT,
)


class ErroDeColeta(Exception):
    """Falha controlada ao buscar dados de fonte pública."""


@dataclass(frozen=True)
class RegistroDownload:
    fonte: str
    arquivo: str
    url: str
    status_http: int
    bytes_total: int
    sha256: str
    coletado_em_utc: str
    cache_reutilizado: bool


def calcular_sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


class HttpCliente:
    """Wrapper sobre requests.Session com intervalo mínimo entre requisições e retry."""

    def __init__(
        self,
        atraso_s: float = ATRASO_PADRAO_S,
        timeout_s: float = TIMEOUT_PADRAO_S,
        tentativas: int = TENTATIVAS_PADRAO,
        sessao: requests.Session | None = None,
        relogio: Callable[[], float] = time.monotonic,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        if atraso_s < 0:
            raise ValueError("atraso_s deve ser >= 0")
        if tentativas < 1:
            raise ValueError("tentativas deve ser >= 1")
        self.atraso_s = atraso_s
        self.timeout_s = timeout_s
        self.tentativas = tentativas
        self._sessao = sessao or requests.Session()
        self._sessao.headers.setdefault("User-Agent", USER_AGENT)
        self._relogio = relogio
        self._dormir = dormir
        self._ultimo_pedido: float | None = None

    def _respeitar_limite(self) -> None:
        if self._ultimo_pedido is None or self.atraso_s == 0:
            return
        decorrido = self._relogio() - self._ultimo_pedido
        falta = self.atraso_s - decorrido
        if falta > 0:
            self._dormir(falta)

    def buscar_bytes(self, url: str) -> tuple[bytes, int]:
        ultimo_erro: Exception | None = None
        for tentativa in range(1, self.tentativas + 1):
            self._respeitar_limite()
            try:
                self._ultimo_pedido = self._relogio()
                resp = self._sessao.get(url, timeout=self.timeout_s)
                if resp.status_code == 200:
                    return resp.content, resp.status_code
                # Erros 4xx (exceto 429) não melhoram com retry
                if 400 <= resp.status_code < 500 and resp.status_code != 429:
                    raise ErroDeColeta(f"HTTP {resp.status_code} ao buscar {url}")
                ultimo_erro = ErroDeColeta(f"HTTP {resp.status_code} ao buscar {url}")
            except ErroDeColeta:
                raise
            except requests.RequestException as exc:
                ultimo_erro = exc

            if tentativa < self.tentativas:
                self._dormir(max(self.atraso_s, 0.5) * tentativa)

        raise ErroDeColeta(
            f"Falha após {self.tentativas} tentativas em {url}: {ultimo_erro}"
        )

    def baixar_arquivo(
        self,
        url: str,
        destino: Path,
        fonte: str,
        forcar: bool = False,
    ) -> RegistroDownload:
        destino.parent.mkdir(parents=True, exist_ok=True)
        agora_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if destino.is_file() and destino.stat().st_size > 0 and not forcar:
            return RegistroDownload(
                fonte=fonte,
                arquivo=destino.name,
                url=url,
                status_http=200,
                bytes_total=destino.stat().st_size,
                sha256=calcular_sha256(destino),
                coletado_em_utc=agora_utc,
                cache_reutilizado=True,
            )

        conteudo, status = self.buscar_bytes(url)
        tmp = destino.with_suffix(destino.suffix + ".tmp")
        tmp.write_bytes(conteudo)
        tmp.replace(destino)
        return RegistroDownload(
            fonte=fonte,
            arquivo=destino.name,
            url=url,
            status_http=status,
            bytes_total=len(conteudo),
            sha256=hashlib.sha256(conteudo).hexdigest(),
            coletado_em_utc=agora_utc,
            cache_reutilizado=False,
        )
