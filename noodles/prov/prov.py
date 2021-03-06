from tinydb import (TinyDB, Query)
from threading import Lock
# from ..utility import on
import time
import sys


def time_stamp():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time()))


def attach_job(key):
    def attach_to(rec):
        rec['attached'].append(key)
        return rec
    return attach_to


def append_link(preprov):
    def append_to(rec):
        rec['links'].append(preprov)
        return rec
    return append_to


class JobDB:
    """Keeps a database of jobs, with a MD5 hash that encodes the function
    name, version, and all arguments to the function.
    """
    def __init__(self, path):
        self.db = TinyDB(path)
        self.lock = Lock()

    def get_result_or_attach(self, key, prov, running):
        job = Query()
        with self.lock:
            rec = self.db.get(job.prov == prov)

            if 'result' in rec:
                return 'retrieved', rec['key'], rec['result']

            job_running = rec['key'] in running
            wf_running = rec['link'] in running.workflows

            if job_running or wf_running:
                self.db.update(attach_job(key), job.prov == prov)
                return 'attached', rec['key'], None

            print("WARNING: unfinished job in database. Removing it and "
                  " rerunning.", file=sys.stderr)
            self.db.remove(eids=[rec.eid])
            return 'broken', None, None

    def job_exists(self, prov):
        job = Query()
        with self.lock:
            return self.db.contains(job.prov == prov)

    def store_result(self, key, result):
        job = Query()
        with self.lock:
            if not self.db.contains(job.key == key):
                return

        self.add_time_stamp(key, 'done')
        with self.lock:
            self.db.update(
                    {'result': result, 'link': None},
                    job.key == key)
            rec = self.db.get(job.key == key)
            return rec['attached']

    def new_job(self, key, prov, job_msg):
        with self.lock:
            self.db.insert({
                'key': key,
                'attached': [],
                'prov': prov,
                'link': None,
                'time': {'schedule': time_stamp()},
                'version': job_msg['data']['hints'].get('version'),
                'function': job_msg['data']['function'],
                'arguments': job_msg['data']['arguments']
            })

        return key, prov

    def add_link(self, key, ppn):
        job = Query()
        with self.lock:
            self.db.update({'link': ppn}, job.key == key)

    def get_linked_jobs(self, ppn):
        job = Query()
        with self.lock:
            rec = self.db.search(job.link == ppn)
            return [r['key'] for r in rec]

    def add_time_stamp(self, key, name):
        def update(r):
            r['time'][name] = time_stamp()

        job = Query()
        with self.lock:
            self.db.update(
                update,
                job.key == key)
