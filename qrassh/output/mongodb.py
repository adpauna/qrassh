# -*- coding: utf-8 -*-

from __future__ import division, absolute_import

import pymongo

from twisted.python import log

import irassh.core.output


class Output(irassh.core.output.Output):
    """
    """

    def __init__(self, cfg):
        self.cfg = cfg
        irassh.core.output.Output.__init__(self, cfg)

    def insert_one(self, collection, event):
        try:
            object_id = collection.insert_one(event).inserted_id
            return object_id
        except Exception as e:
            log.msg('mongo error - {0}'.format(e))

    def update_one(self, collection, session, doc):
        try:
            object_id = collection.update({'session': session}, doc)
            return object_id
        except Exception as e:
            log.msg('mongo error - {0}'.format(e))

    def start(self):
        """
        """
        db_addr = self.cfg.get('output_mongodb', 'connection_string')
        db_name = self.cfg.get('output_mongodb', 'database')

        try:
            self.mongo_client = pymongo.MongoClient(db_addr)
            self.mongo_db = self.mongo_client[db_name]
            # Define Collections.
            self.col_sensors = self.mongo_db['sensors']
            self.col_sessions = self.mongo_db['sessions']
            self.col_auth = self.mongo_db['auth']
            self.col_input = self.mongo_db['input']
            self.col_downloads = self.mongo_db['downloads']
            self.col_input = self.mongo_db['input']
            self.col_clients = self.mongo_db['clients']
            self.col_ttylog = self.mongo_db['ttylog']
            self.col_keyfingerprints = self.mongo_db['keyfingerprints']
            self.col_event = self.mongo_db['event']
        except Exception, e:
            log.msg('output_mongodb: Error: %s' % str(e))


    def stop(self):
        """
        """
        self.mongo_client.close()


    def write(self, entry):
        """
        """
        for i in list(entry.keys()):
            # Remove twisted 15 legacy keys
            if i.startswith('log_'):
                del entry[i]

        eventid = entry["eventid"]

        if eventid == 'irassh.session.connect':
            # Check if sensor exists, else add it.
            doc = self.col_sensors.find_one({'sensor': self.sensor})
            if doc:
                sensorid = doc['sensor']
            else:
                sensorid = self.insert_one(self.col_sensors, entry)

            # Prep extra elements just to make django happy later on
            entry['starttime'] = entry['timestamp']
            entry['endtime'] = None
            entry['sshversion'] = None
            entry['termsize'] = None
            log.msg('Session Created')
            self.insert_one(self.col_sessions, entry)

        elif eventid in ['irassh.login.success', 'irassh.login.failed']:
            self.insert_one(self.col_auth, entry)

        elif eventid in ['irassh.command.success', 'irassh.command.failed']:
            self.insert_one(self.col_input, entry)

        elif eventid == 'irassh.session.file_download':
            # ToDo add a config section and offer to store the file in the db - useful for central logging
            # we will add an option to set max size, if its 16mb or less we can store as normal,
            # If over 16 either fail or we just use gridfs both are simple enough.
            self.insert_one(self.col_downloads, entry)

        elif eventid == 'irassh.client.version':
            doc = self.col_sessions.find_one({'session': entry['session']})
            if doc:
                doc['sshversion'] = entry['version']
                self.update_one(self.col_sessions, entry['session'], doc)
            else:
                pass

        elif eventid == 'irassh.client.size':
            doc = self.col_sessions.find_one({'session': entry['session']})
            if doc:
                doc['termsize'] = '{0}x{1}'.format(entry['width'], entry['height'])
                self.update_one(self.col_sessions, entry['session'], doc)
            else:
                pass

        elif eventid == 'irassh.session.closed':
            doc = self.col_sessions.find_one({'session': entry['session']})
            if doc:
                doc['endtime'] = entry['timestamp']
                self.update_one(self.col_sessions, entry['session'], doc)
            else:
                pass

        elif eventid == 'irassh.log.closed':
            # ToDo Compress to opimise the space and if your sending to remote db
            with open(entry["ttylog"]) as ttylog:
                entry['ttylogpath'] = entry['ttylog']
                entry['ttylog'] = ttylog.read().encode('hex')
            self.insert_one(self.col_ttylog, entry)

        elif eventid == 'irassh.client.fingerprint':
            self.insert_one(self.col_keyfingerprints, entry)

        # Catch any other event types
        else:
            self.insert_one(self.col_event, entry)
