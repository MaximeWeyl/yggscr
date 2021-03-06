# -*- encoding: utf-8 -*-
# Yggtorrent scraper library - Webserver - Rss - Shell
# Copyright © 2018-2019, Laurent Kislaire.
# See /LICENSE for licensing information.

"""
Main routine of Ygg Scraper shell.

:Copyright: © 2018-2019, Laurent Kislaire.
:License: ISC (see /LICENSE).
"""

__all__ = ('main',)
import yggscr.shell


def main():
    """Main routine of Ygg Scraper shell."""
    yggscr.shell.YggShell().cmdloop()
