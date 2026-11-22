#!/usr/bin/env python3
"""Scan context files for sensitive text. Usage: scan_secrets.py [ROOT]

Run me when: I changed an agent contract or a document under docs, memory, references or plans.
"""
from __future__ import annotations

import sys

from scan_context_secrets import main


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
