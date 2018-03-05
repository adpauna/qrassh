# Copyright (c) 2015 Michel Oosterhof <michel@oosterhof.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The names of the author(s) may not be used to endorse or promote
#    products derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHORS ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

"""
FIXME: This module contains ...
"""

from __future__ import print_function, division, absolute_import

from zope.interface import implementer, provider

import os
import sys

from twisted._version import __version__
if __version__.major < 17:
    raise ImportError( "Your version of Twisted is too old. Please ensure your virtual environment is set up correctly.")

from twisted.python import log, usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet, service
from twisted.cred import portal
from twisted.internet import reactor
from twisted.logger import ILogObserver, globalLogPublisher

from qrassh.core.config import readConfigFile
from qrassh.core.utils import get_endpoints_from_section, create_endpoint_services
from qrassh import core
import qrassh.core.realm
import qrassh.core.checkers

import qrassh.telnet.transport
import qrassh.ssh.factory

class Options(usage.Options):
    """
    This defines commandline options and flags
    """
    # The '-c' parameters is currently ignored
    optParameters = [
        ["config", "c", 'qrassh.cfg', "The configuration file to use."]
        ]

    optFlags = [
        ['help', 'h', 'Display this help and exit.']
        ]



@provider(ILogObserver)
def importFailureObserver(event):
    if 'failure' in event and event['failure'].type is ImportError:
        log.err("ERROR: %s. Please run `pip install -U -r requirements.txt` "
                "from Cowrie's install directory and virtualenv to install "
                "the new dependency" % event['failure'].value.message)


globalLogPublisher.addObserver(importFailureObserver)


@implementer(IServiceMaker, IPlugin)
class CowrieServiceMaker(object):
    """
    FIXME: Docstring
    """
    tapname = "qrassh"
    description = "She sells sea shells by the sea shore."
    options = Options
    dbloggers = None
    output_plugins = None
    cfg = None

    def printHelp(self):
        """
        Print qrassh help
        """

        print( """Usage: twistd [options] qrassh [-h]
Options:
  -h, --help             print this help message.

Makes a Cowrie SSH/Telnet honeypot.
""")


    def makeService(self, options):
        """
        Construct a TCPServer from a factory defined in Cowrie.
        """

        if options["help"] == True:
            self.printHelp()
            sys.exit(1)

        if os.name == 'posix' and os.getuid() == 0:
            print('ERROR: You must not run qrassh as root!')
            sys.exit(1)

        log.msg("Python Version {}".format(str(sys.version).replace('\n','')))
        log.msg("Twisted Version {}.{}.{}".format(__version__.major, __version__.minor, __version__.micro))

        cfg = readConfigFile(("qrassh.cfg.dist", "etc/qrassh.cfg", "qrassh.cfg"))

        # ssh is enabled by default
        if cfg.has_option('ssh', 'enabled') == False or \
           (cfg.has_option('ssh', 'enabled') and \
               cfg.getboolean('ssh', 'enabled') == True):
            enableSSH = True
        else:
            enableSSH = False

        # telnet is disabled by default
        if cfg.has_option('telnet', 'enabled') and \
                 cfg.getboolean('telnet', 'enabled') == True:
            enableTelnet = True
        else:
            enableTelnet = False

        if enableTelnet == False and enableSSH == False:
            print('ERROR: You must at least enable SSH or Telnet')
            sys.exit(1)

        # Load db loggers
        self.dbloggers = []
        for x in cfg.sections():
            if not x.startswith('database_'):
                continue
            engine = x.split('_')[1]
            try:
                dblogger = __import__( 'qrassh.dblog.{}'.format(engine),
                    globals(), locals(), ['dblog']).DBLogger(cfg)
                log.addObserver(dblogger.emit)
                self.dbloggers.append(dblogger)
                log.msg("Loaded dblog engine: {}".format(engine))
            except:
                log.err()
                log.msg("Failed to load dblog engine: {}".format(engine))

        # Load output modules
        self.output_plugins = []
        for x in cfg.sections():
            if not x.startswith('output_'):
                continue
            engine = x.split('_')[1]
            try:
                output = __import__( 'qrassh.output.{}'.format(engine),
                    globals(), locals(), ['output']).Output(cfg)
                log.addObserver(output.emit)
                self.output_plugins.append(output)
                log.msg("Loaded output engine: {}".format(engine))
            except ImportError as e:
                log.err("Failed to load output engine: {} due to ImportError: {}".format(engine, e))
                log.msg("Please install the dependencies for {} listed in requirements-output.txt".format(engine))
            except Exception:
                log.err()
                log.msg("Failed to load output engine: {}".format(engine))

        topService = service.MultiService()
        application = service.Application('qrassh')
        topService.setServiceParent(application)

        if enableSSH:
            factory = qrassh.ssh.factory.CowrieSSHFactory(cfg)
            factory.tac = self
            factory.portal = portal.Portal(core.realm.HoneyPotRealm(cfg))
            factory.portal.registerChecker(
                core.checkers.HoneypotPublicKeyChecker())
            factory.portal.registerChecker(
                core.checkers.HoneypotPasswordChecker(cfg))

            if cfg.has_option('honeypot', 'auth_none_enabled') and \
                     cfg.getboolean('honeypot', 'auth_none_enabled') == True:
                factory.portal.registerChecker(
                    core.checkers.HoneypotNoneChecker())

            if cfg.has_section('ssh'):
                listen_endpoints = get_endpoints_from_section(cfg, 'ssh', 2222)
            else:
                listen_endpoints = get_endpoints_from_section(cfg, 'honeypot', 2222)

            create_endpoint_services(reactor, topService, listen_endpoints, factory)

        if enableTelnet:
            f = qrassh.telnet.transport.HoneyPotTelnetFactory(cfg)
            f.tac = self
            f.portal = portal.Portal(core.realm.HoneyPotRealm(cfg))
            f.portal.registerChecker(core.checkers.HoneypotPasswordChecker(cfg))

            listen_endpoints = get_endpoints_from_section(cfg, 'telnet', 2223)
            create_endpoint_services(reactor, topService, listen_endpoints, f)

        return topService

# Now construct an object which *provides* the relevant interfaces
# The name of this variable is irrelevant, as long as there is *some*
# name bound to a provider of IPlugin and IServiceMaker.

serviceMaker = CowrieServiceMaker()
