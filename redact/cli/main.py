import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

app = typer.Typer(add_completion=False, invoke_without_command=True)
console = Console()

_MODE_HELP = "detection engine: ner | llm | both"
_STYLE_HELP = "redaction style: label (e.g. [NAME]) | block (████)"


def _read(file: Optional[Path]) -> str:
    if file:
        return file.read_text()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    console.print("[red]provide a file or pipe text via stdin[/red]")
    raise typer.Exit(1)


def _engines(text: str, mode: str):
    from redact.core.ner import NEREngine
    ner_ents, llm_ents = [], []
    if mode in ("ner", "both"):
        ner_ents = NEREngine().extract(text)
    if mode in ("llm", "both"):
        from redact.core.llm import LLMEngine
        llm_ents = LLMEngine().extract(text)
    return ner_ents, llm_ents


@app.command()
def run(
    file:   Optional[Path] = typer.Argument(None),
    output: Optional[Path] = typer.Option(None,    "--output", "-o", help="write to file instead of stdout"),
    mode:   str            = typer.Option("both",  "--mode",   "-m", help=_MODE_HELP),
    style:  str            = typer.Option("label", "--style",  "-s", help=_STYLE_HELP),
):
    """redact PII from text — reads from file or stdin"""
    from redact.core.pipeline import redact
    text = _read(file)
    ner_ents, llm_ents = _engines(text, mode)
    result = redact(text, ner_ents + llm_ents, style=style)
    if output:
        output.write_text(result)
        console.print(f"[green]written → {output}[/green]")
    else:
        print(result, end="")


@app.command()
def scan(
    file: Optional[Path] = typer.Argument(None),
    mode: str            = typer.Option("both", "--mode", "-m", help=_MODE_HELP),
):
    """show what would be redacted without changing the text"""
    text = _read(file)
    ner_ents, llm_ents = _engines(text, mode)
    all_ents = sorted(ner_ents + llm_ents, key=lambda e: e.start)

    if not all_ents:
        console.print("[green]clean[/green] — no PII detected")
        return

    t = Table(box=box.SIMPLE, show_header=True, header_style="bold white", expand=True)
    t.add_column("TYPE",   style="bold", no_wrap=True)
    t.add_column("TEXT",   style="dim")
    t.add_column("SOURCE", style="dim", no_wrap=True)

    for e in all_ents:
        t.add_row(e.type.value, e.text[:80], e.source)

    console.print(Panel(
        t,
        title="[bold red]PII detected[/bold red]",
        border_style="red",
        box=box.ROUNDED,
    ))


@app.command()
def compare(
    file: Optional[Path] = typer.Argument(None),
):
    """compare what NER vs LLM each catch"""
    from redact.core.pipeline import compare as do_compare
    text = _read(file)
    ner_ents, llm_ents = _engines(text, "both")
    result = do_compare(ner_ents, llm_ents)

    labels = [("both caught", result["both"]), ("NER only", result["ner_only"]), ("LLM only", result["llm_only"])]
    any_found = False
    for label, ents in labels:
        if not ents:
            continue
        any_found = True
        t = Table(box=box.SIMPLE, show_header=False, expand=True)
        t.add_column("TYPE", style="bold", no_wrap=True)
        t.add_column("TEXT", style="dim")
        for e in ents:
            t.add_row(e.type.value, e.text[:80])
        console.print(Panel(t, title=f"[bold]{label}[/bold]", box=box.ROUNDED))

    if not any_found:
        console.print("[green]clean[/green] — no PII detected")
