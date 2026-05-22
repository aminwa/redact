import io, json, subprocess, time, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from redact.core.entities import Entity, EntityType
from redact.core.pipeline import redact, compare

WIDTH  = 75
HEIGHT = 36

E = "\x1b"
PROMPT = f"\r\n{E}[1;32muser@demo{E}[0m:{E}[1;34m~/redact{E}[0m$ "

RAW_TEXT = (
    "Hi, I'm Alice Martin — reach me at alice@company.com\n"
    "or call 415-555-0192. My SSN is 123-45-6789."
)

NER_ENTS = [
    Entity(EntityType.PERSON,   "Alice Martin",   8,  20, "ner"),
    Entity(EntityType.EMAIL,    "alice@company.com", 34, 52, "regex"),
    Entity(EntityType.PHONE,    "415-555-0192",   61, 73, "regex"),
    Entity(EntityType.SSN,      "123-45-6789",    84, 95, "regex"),
]

LLM_ENTS = [
    Entity(EntityType.PERSON,   "Alice Martin",   8,  20, "llm"),
    Entity(EntityType.EMAIL,    "alice@company.com", 34, 52, "llm"),
    Entity(EntityType.PHONE,    "415-555-0192",   61, 73, "llm"),
]


def render_scan() -> str:
    buf = io.StringIO()
    c = Console(file=buf, width=WIDTH, force_terminal=True, color_system="truecolor")
    t = Table(box=box.SIMPLE, show_header=True, header_style="bold white", expand=True)
    t.add_column("TYPE",   style="bold", no_wrap=True)
    t.add_column("TEXT",   style="dim")
    t.add_column("SOURCE", style="dim", no_wrap=True)
    for ent in sorted(NER_ENTS, key=lambda e: e.start):
        t.add_row(ent.type.value, ent.text, ent.source)
    c.print(Panel(t, title="[bold red]PII detected[/bold red]", border_style="red", box=box.ROUNDED))
    return buf.getvalue().replace("\n", "\r\n")


def render_compare() -> str:
    buf = io.StringIO()
    c = Console(file=buf, width=WIDTH, force_terminal=True, color_system="truecolor")
    result = compare(NER_ENTS, LLM_ENTS)
    for label, ents in [("both caught", result["both"]), ("NER only", result["ner_only"]), ("LLM only", result["llm_only"])]:
        if not ents:
            continue
        t = Table(box=box.SIMPLE, show_header=False, expand=True)
        t.add_column("TYPE", style="bold", no_wrap=True)
        t.add_column("TEXT", style="dim")
        for ent in ents:
            t.add_row(ent.type.value, ent.text)
        c.print(Panel(t, title=f"[bold]{label}[/bold]", box=box.ROUNDED))
    return buf.getvalue().replace("\n", "\r\n")


def render_redacted() -> str:
    return redact(RAW_TEXT, NER_ENTS + LLM_ENTS).replace("\n", "\r\n")


def build_cast(cast_path, gif_path):
    scan_out    = render_scan()
    compare_out = render_compare()
    redacted    = render_redacted()

    def t(s, text):
        return [round(s, 3), "o", text]

    events = [
        t(0.1,  PROMPT),
        t(0.8,  "cat report.txt"),
        t(1.1,  "\r\n"),
        t(1.3,  RAW_TEXT.replace("\n", "\r\n") + "\r\n"),
        t(1.8,  PROMPT),
        t(2.6,  "redact scan report.txt"),
        t(3.0,  "\r\n"),
        t(3.6,  scan_out),
        t(4.0,  PROMPT),
        t(4.8,  "redact compare report.txt"),
        t(5.2,  "\r\n"),
        t(5.8,  compare_out),
        t(6.2,  PROMPT),
        t(7.0,  "redact report.txt"),
        t(7.4,  "\r\n"),
        t(8.0,  redacted + "\r\n"),
        t(8.4,  PROMPT),
        t(10.5, ""),
    ]

    header = {
        "version": 2, "width": WIDTH, "height": HEIGHT,
        "timestamp": int(time.time()), "title": "redact demo",
        "env": {"SHELL": "/bin/zsh", "TERM": "xterm-256color"},
    }

    with open(cast_path, "w") as f:
        f.write(json.dumps(header) + "\n")
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    print(f"cast written: {cast_path}")
    r = subprocess.run(
        ["agg", "--theme", "monokai", "--font-size", "14", cast_path, gif_path],
        capture_output=True, text=True,
    )
    print("gif done" if r.returncode == 0 else f"error: {r.stderr}")


if __name__ == "__main__":
    build_cast(
        "/Users/aminwafi/redact_demo.cast",
        "/Users/aminwafi/redact/demo.gif",
    )
