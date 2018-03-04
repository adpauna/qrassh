# Copyright (c) 2009 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

# Commands mapped to common malware

import os
from irassh.shell.honeypot import HoneyPotCommand
from irassh.actions import dao

commands = {}


class ProxyCommand(HoneyPotCommand):
    def call(self):
        cmd = " ".join([self.protocol.cwd] + list(self.args))
        path = "/tmp/root/" + self.protocol.cwd
        output = os.popen("cd %s; %s" % (path, cmd)).read()
        if output and output[-1] != "\n":
            output = output + "\n"
        self.write(output)


class FakeCommand(HoneyPotCommand):
    def call(self):
        fakeOuput = dao.getIRasshDao().getFakeOutput(self.protocol.cwd)
        if fakeOuput is not None:
            self.write(fakeOuput + "\n")


commands['lsp'] = ProxyCommand
commands["cpp"] = ProxyCommand
commands["catp"] = ProxyCommand

supportedCommands = dao.getIRasshDao().getCommands()
for command in supportedCommands:
    if command["impl_type"] == 1:
        commands[command["command"]] = ProxyCommand
    elif command["impl_type"] == 2:
        commands[command["command"]] = FakeCommand
