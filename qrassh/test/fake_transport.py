# -*- test-case-name: Cowrie Test Cases -*-

# Copyright (c) 2016 Dave Germiquet
# See LICENSE for details.

from __future__ import division, absolute_import

from twisted.conch.insults import insults,helper
from twisted.test import proto_helpers


class Container(object):
    """
    This class is placeholder for creating a fake interface
    @var host Client fake infomration
    @var port Fake Port for connection
    @var otherVersionString version
    @var
    """
    otherVersionString = "1.0"

    """
    Fake function for mockup
    """
    def getPeer(self):
        self.host = "1.1.1.1"
        self.port = 2222
        return self

    """
    Fake function for mockup
    """
    def processEnded(self, reason):
        pass


class FakeTransport(proto_helpers.StringTransport):
    """
    Fake transport with abortConnection() method.
    """
    # Thanks to TerminalBuffer (some code was taken from twisted Terminal Buffer)

    width = 80
    height = 24
    void = object()
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, N_COLORS = list(range(9))

    for keyID in ('UP_ARROW', 'DOWN_ARROW', 'RIGHT_ARROW', 'LEFT_ARROW',
                  'HOME', 'INSERT', 'DELETE', 'END', 'PGUP', 'PGDN',
                  'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9',
                  'F10', 'F11', 'F12'):
        exec('%s = object()' % (keyID,))

    TAB = '\x09'
    BACKSPACE = '\x08'

    modes = {}
    # '\x01':     self.handle_HOME,	# CTRL-A
    # '\x02':     self.handle_LEFT,	# CTRL-B
    # '\x03':     self.handle_CTRL_C,	# CTRL-C
    # '\x04':     self.handle_CTRL_D,	# CTRL-D
    # '\x05':     self.handle_END,	# CTRL-E
    # '\x06':     self.handle_RIGHT,	# CTRL-F
    # '\x08':     self.handle_BACKSPACE,	# CTRL-H
    # '\x09':     self.handle_TAB,
    # '\x0B':     self.handle_CTRL_K,	# CTRL-K
    # '\x0C':     self.handle_CTRL_L,	# CTRL-L
    # '\x0E':     self.handle_DOWN,	# CTRL-N
    # '\x10':     self.handle_UP,		# CTRL-P
    # '\x15':     self.handle_CTRL_U,	# CTRL-U
    def setModes(self, modes):
        for m in modes:
            self.modes[m] = True


    aborting = False
    transport = Container()
    transport.session = Container()
    transport.session.conn = Container()
    transport.session.conn.transport = Container()
    transport.session.conn.transport.transport = Container()
    transport.session.conn.transport.transport.sessionno = 1
    transport.session.conn.transport.factory = Container()
    transport.session.conn.transport.factory.sessions = {}
    transport.session.conn.transport.factory.starttime = 0
    factory = Container()
    session = {}


    def abortConnection(self):
        self.aborting = True


    def resetModes(self, modes):
        for m in modes:
            try:
                del self.modes[m]
            except KeyError:
                pass


    def setPrivateModes(self, modes):
        """
        Enable the given modes.

        Track which modes have been enabled so that the implementations of
        other L{insults.ITerminalTransport} methods can be properly implemented
        to respect these settings.

        @see: L{resetPrivateModes}
        @see: L{insults.ITerminalTransport.setPrivateModes}
        """
        for m in modes:
            self.privateModes[m] = True

    def reset(self):
        self.home = insults.Vector(0, 0)
        self.x = self.y = 0
        self.modes = {}
        self.privateModes = {}
        self.setPrivateModes([insults.privateModes.AUTO_WRAP,
                              insults.privateModes.CURSOR_MODE])
        self.numericKeypad = 'app'
        self.activeCharset = insults.G0
        self.graphicRendition = {
            'bold': False,
            'underline': False,
            'blink': False,
            'reverseVideo': False,
            'foreground': self.WHITE,
            'background': self.BLACK}
        self.charsets = {
            insults.G0: insults.CS_US,
            insults.G1: insults.CS_US,
            insults.G2: insults.CS_ALTERNATE,
            insults.G3: insults.CS_ALTERNATE_SPECIAL}
        self.eraseDisplay()


    def eraseDisplay(self):
        self.lines = [self._emptyLine(self.width) for i in range(self.height)]


    def _currentFormattingState(self):
        return True

    def _FormattingState(self):
        return True

    def _emptyLine(self, width):
        return [(self.void, self._currentFormattingState())
                for i in range(width)]

