#!/usr/bin/env bash
set -e

command -v python3 >/dev/null || { echo "python3 required"; exit 1; }

PIP=$(command -v pip3 || command -v pip)
$PIP install -e .
python3 -m spacy download en_core_web_sm
echo "redact installed. run: redact --help"
