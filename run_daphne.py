#!/usr/bin/env python
"""
Script do uruchamiania serwera Daphne z WebSocketami
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'record.settings')
django.setup()

from daphne.cli import CommandLineInterface

if __name__ == "__main__":
    sys.argv = [
        'daphne',
        '-b', '127.0.0.1',
        '-p', '8000',
        'record.asgi:application'
    ]
    CommandLineInterface().run()
