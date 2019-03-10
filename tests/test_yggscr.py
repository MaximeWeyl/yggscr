#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Ygg Scraper test suite
# Copyright © 2018-2019, Laurent Kislaire.
# See /LICENSE for licensing information.


import logging
import time
import sys
import robobrowser
import requests
import pytest
from mock import patch, Mock
from transmissionrpc.error import TransmissionError
from src.yggscr.exceptions import YggException
import src.yggscr.ygg
from src.yggscr.stats import Stats
from src.yggscr.sbrowser import SBrowser
from src.yggscr.torrents import htn, Torrent
from src.yggscr.client import rtorrent_add_torrent, transmission_add_torrent, deluge_add_torrent, exec_cmd
from src.yggscr.link import list_cats, list_subcats, get_link, get_cat_id, list_cat_subcat, cat_subcat_from_href
from src.yggscr.const import get_dl_link, detect_redir


def test_link():
    with pytest.raises(YggException):
        get_link('filmvidéo', 'emission_tv')
    get_link('filmvidéo', 'emission-tv')
    get_cat_id('jeu-vidéo', 'tablette')
    get_cat_id('jeu-vidéo', 'tablette')
    get_cat_id('film-vidéo', 'série-tv')
    log = logging.getLogger()
    get_cat_id('jeu-vidéo', 'tablette', log)
    get_cat_id('jeu-vidéo', 'tablette', log)
    get_cat_id('film-vidéo', 'série-tv', log)
    list_cat_subcat()
    with pytest.raises(YggException):
        get_cat_id('jeu_vidéo', 'foo')
    cat_subcat_from_href('')
    for c in list_cats():
        a = ','.join('"' + e + '"' for e in list_subcats(c))
        print('cat["'+c+'"]=['+a+'];')


def test_core():
    """Test search."""
    s = Stats()
    s.add([('10.5', 'T'), ('8.2', 'G')])
    s.add([('1', 'G'), ('8.2', 'T')])
    s = SBrowser(parser='html.parser')
    print("{}".format(s))
    s.proxify("socks5h://user:pass@127.0.0.1:port")
    print(s.parsed())
    y = src.yggscr.ygg.YggBrowser()
    y.download_torrent(id=41909)
    y.next_torrents()
    y.cat_subcat()
    with pytest.raises(Exception):
        y.get_stats()
    y.login()
    ts = y.search_torrents(q={'name': 'cyber'})
    for t in ts:
        print(t)
    y.logout()
    for _ in range(1, 4):
        with pytest.raises(src.yggscr.ygg.LoginFailed):
            y.login("a b")
        time.sleep(1)
    with pytest.raises(src.yggscr.ygg.TooManyFailedLogins):
        y.login("a b")


def test_client1():
    """Test bt client"""
    try:
        rtorrent_add_torrent("http://127.0.0.1/RPC2", b'0')
    except ConnectionRefusedError:
        pass

    with pytest.raises(ValueError):
        rtorrent_add_torrent("http://127.0.0.1/RPC2")

    try:
        transmission_add_torrent("127.0.0.1", 65432, "user", "pass", b'0')
    except TransmissionError:
        pass

    with patch("src.yggscr.client.tclient"):
        transmission_add_torrent("127.0.0.1", 65432, "user", "pass", b'0')

    try:
        deluge_add_torrent("127.0.0.1", 65432, "user", "pass", b'0')
    except ConnectionRefusedError:
        pass

    with patch("src.yggscr.client.DelugeRPCClient"):
        deluge_add_torrent("127.0.0.1", 65432, "user", "pass", b'0')

    exec_cmd("ls .")


@pytest.mark.skipif(sys.version_info[:2] == (3, 5), reason="python3.5 doesn't have tmp_path")
def test_client2(tmp_path):
    try:
        f = tmp_path / "foo.torrent"
        f.write_bytes(b'00')
        rtorrent_add_torrent("http://127.0.0.1/RPC2", None, str(f))
    except ConnectionRefusedError:
        pass

def test_torrents():
    htn("12")
    t = Torrent("title", "12", "1970", "12GO", "12", "12", "12", "http://test/foo/bar/baz")
    t = Torrent("title", "12", "1970", "12GO", "12", "12", "12", href=None, tid="12", cat="12")
    t.get_dl_link()
    t.set_tref('plop')
    t.set_id('12')


def _mock_response(status=200, headers=None):
    mock_resp = Mock()
    mock_resp.status_code = status
    mock_resp.headers = headers
    return mock_resp


@patch('requests.get')
def test_more(mock_get):
    get_dl_link(42)
    detect_redir()
    mock_resp = _mock_response(status=301, headers={'Location': 'https://wtf.yggtorrent.gg'})
    mock_get.return_value = mock_resp
    detect_redir()


def test_sbrowser_failures():
    # Initialise
    s = SBrowser()
    s.open("http://example.com")

    # Verify example doesn't use CF
    assert s.is_cloudflare() is False
    print(s.is_cloudflare())

    # Generate exception on cfscrape, verify internal handling of RoboError
    with patch("cfscrape.CloudflareScraper.is_cloudflare_challenge",
               side_effect=robobrowser.exceptions.RoboError()):
        print(s.is_cloudflare())
    # Generate unhandled exception on cfscrape, verify exception raised
    with patch("cfscrape.CloudflareScraper.is_cloudflare_challenge",
               side_effect=Exception("!")):
        with pytest.raises(Exception):
            print(s.is_cloudflare())

    s = SBrowser()
    s.connection_details()
    with patch("robobrowser.RoboBrowser.open", side_effect=requests.exceptions.ProxyError()):
        assert s.connection_details() == {'ip': 'Unknown'}
    with patch("robobrowser.RoboBrowser.open", side_effect=requests.exceptions.ConnectionError):
        assert s.connection_details() == {'ip': 'Unknown'}
    with patch("robobrowser.RoboBrowser.open", side_effect=ValueError()):
        assert s.connection_details() == {'ip': 'Unknown'}
    with patch("robobrowser.RoboBrowser.open", side_effect=Exception()):
        assert s.connection_details() == {'ip': 'Unknown'}
