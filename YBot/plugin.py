###
# Copyright (c) 2018, Laurent
# All rights reserved.
#
###

import yggscr
import requests
from time import sleep, time
from hashlib import sha256
import supybot.ircdb as ircdb
from supybot.commands import (wrap, optional)
import supybot.callbacks as callbacks
from .yggscr.ygg import YggBrowser
from .yggscr.shout import (YggShout, ShoutMessage)
from .yggscr.exceptions import YggException
# import supybot.utils as utils
# import supybot.plugins as plugins
import supybot.ircutils as ircutils
from bs4 import BeautifulSoup

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('YBot')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    def _(x):
        return x


class YBot(callbacks.Plugin):
    """sup ygg bot"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(YBot, self)
        self.__parent.__init__(irc)
        self.yggb = YggBrowser()
        self.yggb.proxify("socks5h://192.168.1.9:9100")
        self.shout = YggShout(self.yggb)
        self.col = dict()

    def yggv(self, irc, msg, args):
        """
        Prints the plugin version
        """
        irc.reply(yggscr.__version__)
    yggv = wrap(yggv)

    def yconn(self, irc, msg, args):
        """
        Print connection details
        """
        irc.reply("{}".format(self.yggb))
    yconn = wrap(yconn)

    def yprox(self, irc, msg, args, https_proxy):
        """[https proxy]
        Sets or removes proxy (http, socks, ..)
        """
        cuser = ircdb.users.getUser(msg.prefix)
        isOwner = cuser._checkCapability('owner')
        if not isOwner:
            irc.error("Not my owner")
            return
        if https_proxy:
            self.yggb.proxify(https_proxy)
        else:
            self.yggb.proxify(None)
        irc.replySuccess()
    yprox = wrap(yprox, [optional('anything')])

    def ysearch(self, irc, msg, args, q, n, detail):
        """q:pattern[,c:cat[,s:subcat]] [n:nmax] [detail True/False]
        Searches on ygg and return first page results -
        Will only return the first nmax results and waits 1s between each reply
        """
        try:
            p = dict((t.split(':')
                      for t in q.split(',')))
        except ValueError:
            irc.error("Wrong syntax")
            return
        try:
            torrents = self.yggb.search_torrents(
                p["q"], p.get("c"), p.get("s"), detail)
        except (requests.exceptions.ProxyError,
                requests.exceptions.ConnectionError) as e:
            irc.error("Network Error: %s" % e)
            return
        except YggException as e:
            irc.error("Ygg Exception raised: %s" % e)
            return
        if torrents is None:
            irc.reply("No results")
            return
        if n is None:
            n = 3
        for idx, torrent in enumerate(torrents[:n]):
            sleep(1)
            irc.reply("%2d - %s [%s Size:%s C:%s S:%s L:%s Comm:%s] : %s" %
                      (1+idx, torrent.title, torrent.age, torrent.size,
                       torrent.compl, torrent.seeders, torrent.leechers,
                       torrent.comm, torrent.href))
    ysearch = wrap(ysearch,
                   ['anything', optional('int'), optional('boolean')])

    def ycat(self, irc, msg, args):
        """Will list available cat/subcat combinaisons
        """
        irc.reply("Available (cat, subcat) combinaisons:{}".
                  format(self.yggb.cat_subcat()))
    ycat = wrap(ycat)

    def ylogin(self, irc, msg, args, yuser, ypass):
        """[user pass]
        Logins to ygg using given credentials or stored one
        """
        cuser = ircdb.users.getUser(msg.prefix)
        isOwner = cuser._checkCapability('owner')
        if not isOwner:
            irc.error("Not my owner")
            return
        if not yuser and not ypass:
            yuser = self.registryValue('cred.user')
            ypass = self.registryValue('cred.pass')
            if not yuser or not ypass:
                irc.error("You need to set cred.user and cred.pass")
                return
        elif not ypass:
            irc.error("Wrong syntax")
            return
        try:
            self.yggb.login(yuser, ypass)
        except (requests.exceptions.ProxyError,
                requests.exceptions.ConnectionError) as e:
            irc.error("Network Error: %s" % e)
            return
        except YggException as e:
            irc.error("Ygg Exception raised: %s" % e)
            return
        except Exception as e:
            irc.error("Could not login to Ygg with credentials: %s" % e)
            return
        irc.replySuccess()
        self.log.info("Connected as {}".format(yuser))
    ylogin = wrap(ylogin, [optional('anything'), optional('anything')])

    def ylogout(self, irc, msg, args):
        """
        Logout from ygg
        """
        cuser = ircdb.users.getUser(msg.prefix)
        isOwner = cuser._checkCapability('owner')
        if not isOwner:
            irc.error("Not my owner")
            return
        self.yggb.logout()
        irc.replySuccess()
    ylogout = wrap(ylogout)

    def ystats(self, irc, msg, args):
        """
        Return ratio stats
        """
        if self.yggb.idstate == "Anonymous":
            irc.error("You need to be authenticated at ygg")
        else:
            try:
                r = self.yggb.stats()
            except (requests.exceptions.ProxyError,
                    requests.exceptions.ConnectionError) as e:
                irc.error("Network Error: %s" % e)
                return
            except YggException as e:
                irc.error("Ygg Exception raised: %s" % e)
                return
            except Exception as e:
                irc.error("Could not get stats: %s" % e)
                return
            irc.reply('↑ {:7.2f}GB ↓ {:7.2f}GB % {:6.4f}'.
                      format(r['up'], r['down'], r['ratio']))
            irc.reply(
                '↑ Instant {}KBps Mean {}KBps ↓ Instant {}KBps Mean {}KBps'.
                format(r['i_up'], r['m_up'], r['i_down'], r['m_down']))
    ystats = wrap(ystats)

    def yresp(self, irc, msg, args):
        """
        Print http response on console
        """
        self.log.info("ygg request response:%s" % self.yggb.response())
        irc.replySuccess()
    yresp = wrap(yresp)

    def yping(self, irc, msg, args, n=1):
        """
        GET /
        """
        t = []
        mmin, mmax, mmean = float("inf"), float("-inf"), float("inf")
        for _ in range(n):
            try:
                t1 = time()
                self.yggb.ping()
                t2 = time()
                dt = t2-t1
                mmax = max(mmax, dt)
                mmin = min(mmin, dt)
                t.append(dt)
            except Exception as e:
                pass
                mmax = float("inf")
        if t:
            mmean = sum(t)/len(t)
        irc.reply("%d packets transmitted, %d received, %.2f:% packet loss".
                  format(n, len(t), 100*(1-len(t)/n)))
        irc.reply("rtt min/avg/max = %.2f/%.2f/%.2f ms".
                  format(mmin, mmean, mmax))

    yping = wrap(yping, [optional(int)])

    def colorize_user(self, user, group, w_colour):

        colours = ('blue',
                   'green',
                   'brown',
                   'purple',
                   'orange',
                   'yellow',
                   'light green',
                   'teal',
                   'light blue',
                   'pink',
                   'dark gray',
                   'light gray')

        # 1: unknown, 3: supermod, 4: mod, 5: tp
        gcolours = {1: 'blue', 3: 'orange', 4: 'green', 5: 'pink'}

        if group != 2:
            user = ircutils.bold(
                        ircutils.mircColor(user, gcolours[group]))
        elif w_colour:
            hash = sha256()
            hash.update(user.encode())
            hash = hash.digest()[0]
            hash = hash % len(colours)
            user = ircutils.mircColor(user, colours[hash])
        return user

    def shoutify(self, shout, w_colour):
        user = "{0: >12}".format(shout.user)
        user = self.colorize_user(user, shout.group, w_colour)
        fmt = self.registryValue('shout.fmt')
        return  fmt.format(time=shout.mtime, fuser=user, user=shout.user, group=shout.group, message=shout.message)

    def yshout(self, irc, msg, args, n, w_colour=False, hfile=None):
        """[int n] [boolean user_colorized] [injected html file]
        Print last shout messages and detects gap. Time is UTC.
        User will be colorized if boolean is True.
        """
        if hfile:
            try:
                with open(hfile,"r") as fn:
                    html = fn.read()
            except:
                irc.error("Can't read file %s" % hfile)
                return
            shout = ShoutMessage(shout=None, soup=BeautifulSoup(html))
            irc.reply(self.shoutify(shout, False), prefixNick=False)
            return
        try:
            diff = self.shout.do_diff()
        except Exception as e:
            self.log.info("Could not dump shout, aborting. Error %s" % e)
            #irc.error("Shout: Can't get shout (%s)" % e)
            return
        if n is None:
            n = len(diff)
        for removed, shout in diff[len(diff)-n:]:
            prefix = "REMOVED!!: " if removed else ""
            irc.reply(
                    prefix + self.shoutify(shout, w_colour), prefixNick=False)
            sleep(1)
    yshout = wrap(yshout, [optional('int'), optional('boolean'), optional('anything')])


Class = YBot


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
