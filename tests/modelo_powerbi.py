"""Abre o projeto PBIP no Power BI Desktop, atualiza e executa consultas DAX via TOM/ADOMD.

Gera uma cópia temporária do projeto com scripts/montar_pbip.py apontando para data/limpa,
abre PainelEcommerceMacro.pbip no Power BI Desktop, dispara RefreshType.Full no motor
Analysis Services local (msmdsrv.exe) e consulta as medidas DAX diretamente via ADOMD.

Só roda com a opção --desktop do pytest; ao final, fecha a janela sem salvar.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GERADOR = RAIZ / "scripts" / "montar_pbip.py"
MOTOR = RAIZ / "tests" / "motor_powerbi.ps1"
POWERSHELL = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass"]
ESPERA = 300  # segundos para abrir o Power BI Desktop e subir o modelo


def executavel_do_desktop() -> Path | None:
    candidatos = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WindowsApps" / "PBIDesktopStore.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        / "Microsoft Power BI Desktop"
        / "bin"
        / "PBIDesktop.exe",
    ]
    return next((c for c in candidatos if c.exists()), None)


def desktop_instalado() -> bool:
    return sys.platform == "win32" and executavel_do_desktop() is not None


def nome_da_coluna(rotulo: str) -> str:
    """Extrai o nome limpo de uma coluna retornada pelo ADOMD ('Tabela[col]' ou '[col]')."""
    m = re.search(r"\[([^\]]+)\]$", rotulo)
    return m.group(1) if m else rotulo


def _powershell(*argumentos: str) -> str:
    return subprocess.run(
        [*POWERSHELL, *argumentos],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout


def _motores() -> dict[int, int]:
    saida = _powershell(
        "-Command",
        "Get-CimInstance Win32_Process | Where-Object Name -eq 'msmdsrv.exe'"
        " | ForEach-Object { '{0} {1}' -f $_.ProcessId, $_.ParentProcessId }",
    )
    return {
        int(m): int(p)
        for m, p in (linha.split() for linha in saida.splitlines() if linha.strip())
    }


def _porta(motor: int) -> int | None:
    saida = _powershell(
        "-Command",
        f"try {{ Get-NetTCPConnection -OwningProcess {motor} -State Listen -ErrorAction Stop"
        " | Select-Object -First 1 -ExpandProperty LocalPort } catch {}",
    ).strip()
    return int(saida) if saida else None


class ModeloPowerBI:
    def __init__(self, pasta_dados: Path, pasta_trabalho: Path):
        self.pasta = Path(pasta_trabalho)
        self.desktop: int | None = None
        self.motor: int | None = None
        self.porta: int | None = None
        try:
            self._abrir(Path(pasta_dados))
        except BaseException:
            self.fechar()
            raise

    def _abrir(self, pasta_dados: Path) -> None:
        projeto = self.pasta / "projeto"
        subprocess.run(
            [
                sys.executable,
                str(GERADOR),
                "--saida",
                str(projeto),
                "--pasta-dados",
                str(pasta_dados),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        antes = _motores()
        subprocess.Popen([str(executavel_do_desktop()), str(projeto / "PainelEcommerceMacro.pbip")])

        prazo = time.monotonic() + ESPERA
        while self.porta is None:
            if time.monotonic() > prazo:
                raise TimeoutError("o Power BI Desktop não abriu o motor msmdsrv a tempo")
            time.sleep(3)
            novos = {m: p for m, p in _motores().items() if m not in antes}
            if novos:
                self.motor, self.desktop = next(iter(novos.items()))
                self.porta = _porta(self.motor)

        while not self._modelo()["tabelas"]:
            if time.monotonic() > prazo:
                raise TimeoutError("o Power BI Desktop não carregou o modelo a tempo")
            time.sleep(3)
        self._chamar("atualizar")

    def _chamar(self, acao: str, *argumentos: str):
        saida = _powershell("-File", str(MOTOR), "-Porta", str(self.porta), "-Acao", acao, *argumentos)
        return json.loads(saida)

    def _modelo(self) -> dict:
        return self._chamar("modelo")

    def tabelas(self) -> list[str]:
        return self._modelo()["tabelas"]

    def ligacoes(self) -> list[tuple[tuple[str, str], tuple[str, str], bool]]:
        return [((a, b), (c, d), ativa) for a, b, c, d, ativa in self._modelo()["ligacoes"]]

    def consultar(self, dax: str) -> list[dict]:
        arquivo = self.pasta / "consulta.dax"
        arquivo.write_text(dax, encoding="utf-8")
        linhas = self._chamar("dax", "-Arquivo", str(arquivo))
        return [{nome_da_coluna(c): v for c, v in linha.items()} for linha in linhas]

    def fechar(self) -> None:
        processos = [p for p in (self.desktop, self.motor) if p]
        self.desktop = self.motor = None
        if processos:
            ids = ",".join(map(str, processos))
            _powershell(
                "-Command",
                f"foreach ($p in {ids}) {{ try {{ Stop-Process -Id $p -Force -ErrorAction Stop }} catch {{}} }}",
            )
