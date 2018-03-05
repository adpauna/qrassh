from __future__ import division, absolute_import

import time
from datetime import datetime
import rethinkdb as r

import qrassh.core.output


def iso8601_to_timestamp(value):
    return time.mktime(datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").timetuple())


class Output(qrassh.core.output.Output):
    """
    """

    RETHINK_DB_SEGMENT = 'output_rethinkdblog'

    def __init__(self, cfg):
        """
        """
        self.host = cfg.get(self.RETHINK_DB_SEGMENT, 'host')
        self.port = cfg.get(self.RETHINK_DB_SEGMENT, 'port')
        self.db = cfg.get(self.RETHINK_DB_SEGMENT, 'db')
        self.table = cfg.get(self.RETHINK_DB_SEGMENT, 'table')
        self.password = cfg.get(self.RETHINK_DB_SEGMENT, 'password')
        qrassh.core.output.Output.__init__(self, cfg)

    # noinspection PyAttributeOutsideInit
    def start(self):
        """
        """
        self.connection = r.connect(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password
        )
        try:
            r.db_create(self.db).run(self.connection)
            r.db(self.db).table_create(self.table).run(self.connection)
        except r.RqlRuntimeError:
            pass

    def stop(self):
        """
        """
        self.connection.close()

    def write(self, logentry):
        """
        """
        for i in list(logentry.keys()):
            # remove twisted 15 legacy keys
            if i.startswith('log_'):
                del logentry[i]

        if 'timestamp' in logentry:
            logentry['timestamp'] = iso8601_to_timestamp(logentry['timestamp'])

        r.table(self.table).insert(logentry).run(self.connection)
