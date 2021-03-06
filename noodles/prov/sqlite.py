import sqlite3
from threading import Lock
from collections import (namedtuple, defaultdict)
# from ..utility import on
import time
import sys

try:
    import ujson as json
except ImportError:
    import json


schema = '''
    create table if not exists "jobs" (
        "id"        integer unique primary key,
        "prov"      text unique not null,
        "link"      integer,
        "version"   text,
        "function"  text,
        "arguments" text,
        "result"    text );

    create table if not exists "timestamps" (
        "job"       integer not null references "jobs"("id")
                    on delete cascade,
        "time"      datetime default current_timestamp,
        "what"      text );
'''

JobEntry = namedtuple(
        'JobEntry',
        ['id', 'prov', 'link', 'version', 'function', 'arguments', 'result'])

TimestampEntry = namedtuple(
        'TimestampEntry',
        ['job', 'time', 'what'])


def time_stamp():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time()))


class JobDB:
    """Keeps a database of jobs, with a MD5 hash that encodes the function
    name, version, and all arguments to the function.
    """
    def __init__(self, path):
        self.duplicates = defaultdict(list)
        self.connection = sqlite3.connect(path, check_same_thread=False)

        self.cur = self.connection.cursor()
        self.cur.executescript(schema)
        self.lock = Lock()

    def add_job(self, prov, job_msg, running):
        with self.lock:
            self.cur.execute('select * from "jobs" where "prov" = ?;', (prov,))
            row = self.cur.fetchone()

            # if no record is found, register the job and return the db id
            if row is None:
                self.cur.execute(
                    'insert into "jobs" ("prov", "version", "function", '
                    '"arguments") values (?, ?, ?, ?)',
                    (prov, job_msg['data']['hints'].get('version'),
                     json.dumps(job_msg['data']['function']),
                     json.dumps(job_msg['data']['arguments'])))

                return 'registered', self.cur.lastrowid, None

            rec = JobEntry(row)

            if rec.result is not None:
                return 'retrieved', rec.id, rec.result

            job_running = rec.key in running
            wf_running = rec.link in running.workflows

            if job_running or wf_running:
                self.duplicates[rec.id].append(rec.key)
                return 'attached', rec.id, None

            print("WARNING: unfinished job in database. Removing it and "
                  " rerunning.", file=sys.stderr)
            self.cur.execute(
                'delete from "jobs" where "id" = ?;', rec.id)
            return 'broken', None, None

    def job_exists(self, prov):
        with self.lock:
            self.cur.execute('select * from "jobs" where "prov" = ?;', (prov,))
            rec = self.cur.fetchone()
            return rec is not None

    def store_result(self, db_id, result):
        with self.lock:
            self.add_time_stamp(db_id, 'done')
            self.cur.execute(
                'update "jobs" set "result" = ? where "id" = ?;',
                (result, db_id))
            # self.cur.execute('select "duplicate" from "duplicates" where
            # "primary" = ?;', db_id)
            # duplicates = self.cur.fetchall()
            return self.duplicates[db_id]

    def add_link(self, db_id, ppn):
        with self.lock:
            self.cur.execute(
                'update "jobs" set "link" = ? where "id" = ?', (ppn, db_id))

    def get_linked_jobs(self, ppn):
        with self.lock:
            self.cur.execute(
                'select "id" from "jobs" where "link" = ?', (ppn,))
            return self.cur.fetchall()

    def add_time_stamp(self, db_id, name):
        with self.lock:
            self.cur.execute(
                'insert into "timestamps" ("job", "what")'
                'values (?, ?)',
                (db_id, name))
