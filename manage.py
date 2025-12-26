#!/usr/bin/env python
"""
Command-line utility for administrative tasks.

# For more information about this file, visit
# https://docs.djangoproject.com/en/2.1/ref/django-admin/
"""

import os
import sys
from pathlib import Path

if __name__ == '__main__':
    # Try to auto-discover a local virtual environment (common names)
    project_root = Path(__file__).resolve().parent
    venv_names = ['.venv', 'venv', 'env']
    for name in venv_names:
        venv_path = project_root / name
        if venv_path.exists():
            # Windows venv layout: <venv>\Lib\site-packages
            site_packages_win = venv_path / 'Lib' / 'site-packages'
            # Unix layout: <venv>/lib/pythonX.Y/site-packages — add any matching dirs
            lib_dir = venv_path / 'lib'
            if site_packages_win.exists():
                sys.path.insert(0, str(site_packages_win))
                break
            elif lib_dir.exists():
                # try to find a site-packages under lib
                for sub in lib_dir.iterdir():
                    candidate = sub / 'site-packages'
                    if candidate.exists():
                        sys.path.insert(0, str(candidate))
                        break
                else:
                    continue
                break

    # Default settings module for local development (can be overridden by environment)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Palette.settings.development')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        hint_lines = [
            "Couldn't import Django.",
            "If you haven't installed dependencies, run:",
            "  python -m pip install -r requirements.txt",
            "If you use a virtual environment, activate it first:",
            "  Windows: .\\.venv\\Scripts\\activate",
            "  Unix: source .venv/bin/activate",
            "Or create one: python -m venv .venv && activate it.",
        ]
        raise ImportError("\n".join(hint_lines)) from exc
    execute_from_command_line(sys.argv)
