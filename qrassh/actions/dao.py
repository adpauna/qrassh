import MySQLdb
import MySQLdb.cursors

from irassh.core.config import *


class IRasshDao:

    def __init__(self, cfg):
        if cfg.has_option('output_mysql', 'port'):
            port = int(cfg.get('output_mysql', 'port'))
        else:
            port = 3306
        host = cfg.get('output_mysql', 'host')
        db = cfg.get('output_mysql', 'database')
        user = cfg.get('output_mysql', 'username')
        pwd = cfg.get('output_mysql', 'password')
        self.connection = MySQLdb.connect(host=host, user=user, passwd=pwd, db=db, port=port,
                                          cursorclass=MySQLdb.cursors.DictCursor)

    def getCommands(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM commands")
        return cursor

    def getFakeOutput(self, cmd):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM fake_commands WHERE command = %s", (cmd,))
        for record in cursor:
            return record["fake_output"]

        return None

    def saveCase(self, case):
        cursor = self.connection.cursor()

        initial_cmd = case["initial_cmd"]
        next_cmd = case["next_cmd"]

        # cursor.execute(
        #     "INSERT INTO cases(initial_cmd, action, next_cmd, cmd_profile) VALUES (%s, %s, %s, %s, %s)",
        #     (
        #         initial_cmd,
        #         case["action"],
        #         next_cmd,
        #         self.getProfile(initial_cmd)
        #     )
        # )
        # self.connection.commit()

    def getProfile(self, cmd):
        cursor = self.connection.cursor()
        cursor.execute("SELECT prof_type FROM commands WHERE command = %s", (cmd,))
        for record in cursor:
            return record["prof_type"]
        return "no prof_type in commands for command: `" + cmd + "`"

    def getInsultMsg(self, loc):
        cursor = self.connection.cursor()
        print ("SELECT message FROM messages WHERE country = %s: " + loc)
        cursor.execute("SELECT message FROM messages WHERE country = %s", (loc,))
        for record in cursor:
            return record["message"].strip()

        cursor = self.connection.cursor()
        print ("SELECT message FROM messages WHERE country = %s: DEFAULT")
        cursor.execute("SELECT message FROM messages WHERE country = %s", ('DEFAULT',))
        for record in cursor:
            return record["message"].strip()


irasshDao = None


def getIRasshDao():
    global irasshDao
    if irasshDao is None:
        irasshDao = IRasshDao(CONFIG)
    return irasshDao
