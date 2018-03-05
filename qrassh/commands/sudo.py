

from __future__ import division, absolute_import

import getopt

from twisted.python import log

from qrassh.shell.honeypot import HoneyPotCommand,StdOutStdErrEmulationProtocol

commands = {}

sudo_shorthelp=('''
sudo: Only one of the -e, -h, -i, -K, -l, -s, -v or -V options may be specified
usage: sudo [-D level] -h | -K | -k | -V
usage: sudo -v [-AknS] [-D level] [-g groupname|#gid] [-p prompt] [-u user name|#uid]
usage: sudo -l[l] [-AknS] [-D level] [-g groupname|#gid] [-p prompt] [-U user name] [-u user name|#uid] [-g groupname|#gid] [command]
usage: sudo [-AbEHknPS] [-r role] [-t type] [-C fd] [-D level] [-g groupname|#gid] [-p prompt] [-u user name|#uid] [-g groupname|#gid] [VAR=value] [-i|-s] [<command>]
usage: sudo -e [-AknS] [-r role] [-t type] [-C fd] [-D level] [-g groupname|#gid] [-p prompt] [-u user name|#uid] file ...
''').strip().split('\n')

sudo_longhelp=('''
sudo - execute a command as another user

usage: sudo [-D level] -h | -K | -k | -V
usage: sudo -v [-AknS] [-D level] [-g groupname|#gid] [-p prompt] [-u user name|#uid]
usage: sudo -l[l] [-AknS] [-D level] [-g groupname|#gid] [-p prompt] [-U user name] [-u user name|#uid] [-g groupname|#gid] [command]
usage: sudo [-AbEHknPS] [-r role] [-t type] [-C fd] [-D level] [-g groupname|#gid] [-p prompt] [-u user name|#uid] [-g groupname|#gid] [VAR=value] [-i|-s] [<command>]
usage: sudo -e [-AknS] [-r role] [-t type] [-C fd] [-D level] [-g groupname|#gid] [-p prompt] [-u user name|#uid] file ...

Options:
  -a type       use specified BSD authentication type
  -b            run command in the background
  -C fd         close all file descriptors >= fd
  -E            preserve user environment when executing command
  -e            edit files instead of running a command
  -g group      execute command as the specified group
  -H            set HOME variable to target user's home dir.
  -h            display help message and exit
  -i [command]  run a login shell as target user
  -K            remove timestamp file completely
  -k            invalidate timestamp file
  -l[l] command list user's available commands
  -n            non-interactive mode, will not prompt user
  -P            preserve group vector instead of setting to target's
  -p prompt     use specified password prompt
  -r role       create SELinux security context with specified role
  -S            read password from standard input
  -s [command]  run a shell as target user
  -t type       create SELinux security context with specified role
  -U user       when listing, list specified user's privileges
  -u user       run command (or edit file) as specified user
  -V            display version information and exit
  -v            update user's timestamp without running a command
  --            stop processing command line arguments
''').strip().split('\n')

class command_sudo(HoneyPotCommand):
    """
    """

    def short_help(self):
        """
        """
        for ln in sudo_shorthelp:
            self.errorWrite(ln+'\n')
        self.exit()


    def long_help(self):
        """
        """
        for ln in sudo_longhelp:
            self.errorWrite(ln+'\n')
        self.exit()


    def version(self):
        """
        """
        self.errorWrite(
'''Sudo version 1.8.5p2
Sudoers policy plugin version 1.8.5p2
Sudoers file grammar version 41
Sudoers I/O plugin version 1.8.5p2\n''')
        self.exit()


    def start(self):
        """
        """
        start_value = None
        parsed_arguments = []
        for count in range(0,len(self.args)):
            class_found =  self.protocol.getCommand(self.args[count], self.environ['PATH'].split(':'))
            if class_found:
                start_value = count
                break
        if start_value is not None:
            for index_2 in range(start_value,len(self.args)):
                parsed_arguments.append(self.args[index_2])

        try:
            optlist, args = getopt.getopt(self.args[0:start_value], 'bEeHhKknPSVva:C:g:i:l:p:r:s:t:U:u:')
        except getopt.GetoptError as err:
            self.errorWrite('sudo: illegal option -- ' + err.opt + '\n')
            self.short_help()
            return

        for o, a in optlist:
            if o in ("-V"):
                self.version()
                return
            elif o in ("-h"):
                self.long_help()
                return

        if len(parsed_arguments) > 0:
            line = ' '.join(parsed_arguments)
            cmd = parsed_arguments[0]
            cmdclass = self.protocol.getCommand(cmd,
                self.environ['PATH'].split(':'))

            if cmdclass:
                log.msg(eventid='qrassh.command.success',
                        input=line,
                        format='Command found: %(input)s')
                command = StdOutStdErrEmulationProtocol(self.protocol,cmdclass,parsed_arguments[1:], None ,None)
                self.protocol.pp.insert_command(command)
                # this needs to go here so it doesn't write it out....
                if self.input_data:
                    self.write(self.input_data)
                self.exit()
            else:
                self.short_help()
        else:
            self.short_help()

commands['sudo'] = command_sudo
