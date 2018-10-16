#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Ygg Scraper test suite
# Copyright © 2018, Laurent Kislaire.
# See /LICENSE for licensing information.


import pytest
from src.yggscr.shell import YggShell
from src.yggscr.exceptions import LoginFailed

# FIXME use mock


def test_shell():
    """Test shell."""
    y = YggShell()
    y.do_open('http://www.example.org')
    y.do_print("")
    y.do_response("")
    y.do_ping("")
    y.do_proxify("")
    y.do_lscat("")
    y.do_login("")
#    with pytest.raises(LoginFailed):
#        y.do_login('test test')
    y.print_torrents([], n=1)
    y.do_search_torrents("q:cyber c:film n:2 d:True")
    y.do_next('')
    y.do_next('n:4')
    y.do_top_day("")
    y.do_top_week("")
    y.do_top_month("")
    y.do_exclus("")
