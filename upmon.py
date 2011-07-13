#!/usr/bin/env python
# coding=utf8
import os, sys
import sqlite3
import ping_delay
import threading
import collections
import time
import datetime
import queue
from platform import node
from optparse import OptionParser


if sys.platform == "win32":
    DEFAULT_TIMER = time.clock
else:
    DEFAULT_TIMER = time.time


SERVERNAME = node()
CONNECTION =  sqlite3.connect("upmondb")
C = CONNECTION.cursor()


class Hosts:
    def __init__(self, hostname, time_delay):
        self.hostname = hostname
        self.time_delay = int(time_delay)
    def name (self):
        return self.hostname
    def delay (self):
        return self.time_delay
    def __repr__(self):
        return repr((self.hostname, self.time_delay))

class Sheduler(threading.Thread):
    def __init__(self, sheduler_queue, hosts):
        self.hosts = hosts
        self.sheduler_queue = sheduler_queue
        threading.Thread.__init__(self)
    def run(self):
        print(self.hosts)
        while True:
            for tmp_host in self.hosts:
                print(round(time.clock()))
                if round(time.clock()) % tmp_host.delay()== 0:
                    print(round(time.clock()), 'hostname', tmp_host.name())
                    self.sheduler_queue.put(tmp_host.name())
            time.sleep(1)


class Ping_host(threading.Thread):
    def __init__(self, sheduler_queue):
        self.sheduler_queue = sheduler_queue
        threading.Thread.__init__(self)

    def run(self):
        while True:
            try:
                host = self.sheduler_queue.get()
                self.process(host)
                self.sheduler_queue.join()
            finally:
                self.sheduler_queue.task_done()



    def process(self, host):
        print( ping_delay.ping_result(host), 'result \n',
                host, '  date',time.strftime("%d %b %Y %H:%M:%S ", time.localtime()),'\n\n\n')
#        sqlite3.connect("upmondb").cursor().execute("insert into ping_stat values(?,?,?)",
#                 (host, SERVERNAME, ping_delay.ping_result(host)))
#        C().commit()
#        sqlite3.connect("upmondb").close()


def ins_db(hostname,repit_t = 5000,ch = True):
    try:
        CONNECTION.execute('create table hosts_for_ping(h,t,p)')
    except sqlite3.OperationalError: pass
    finally:
        C.execute("insert into hosts_for_ping values(?,?,?)", (hostname,repit_t,ch))
        CONNECTION.commit()

def del_db(hostmane):
    try:
        C.execute('delete from hosts_for_ping where h=?',(hostmane,))
    except sqlite3.OperationalError:
        print("""Host dont find \n
              enter correct hostname""")
    else:
        CONNECTION.commit()

def fetch_hosts(primary = True):
    hosts = []
    try:
        for hostname, time in C.execute('select h,t  from hosts_for_ping where p=?',(True,)):
            i = Hosts(hostname, time)
            hosts.append(i)
        return hosts

    except sqlite3.OperationalError:
        CONNECTION.commit()

def parse_options():
    parser = OptionParser(
            usage=("Usage: %prog [option [delay time]]\n"))
    parser.add_option("-a", "--add", dest="add_host",
            default=False,
            help="add host to ping into DB", metavar="HOSTNAME [TIME DELAY]")
    parser.add_option("-d", "--delete", dest="del_host", default=False,
                      help="delete host on DB", metavar="HOSTNAME")
    parser.add_option("-l", "--list", action='store_true', dest='list_hosts', default=False,
                        help="Print list of host")
    opts, args = parser.parse_args()
    if opts.add_host is not False:
        if len(args) != 1:
            parser.error('There should be one delay time for the host')
        try:
            args = int(args[0])
        except(ValueError):
            parser.error('Delay time must be integer')
        return opts, args
    else: return opts, False


def main():

    sheduler_queue = queue.Queue()
    Time_sleep = 15
    opts, args = parse_options()
    hosts_primary = fetch_hosts()

    if opts.add_host:
        ins_db(opts.add_host, args)
        sys.exit()
    if len(hosts_primary) == 0:
        print('DB is empty, add host first \n'
            'use -h or --help to print help message')
        sys.exit(1)
    if opts.del_host is not False:
        for tmp_host in hosts_primary:
            if opts.del_host == tmp_host:
                del_db(opts.del_host)
                print('{0} removed from DB'.format(opts.del_host))
                sys.exit()
            else:
                print('{0} not found in the database'.format(opts.del_host))
                sys.exit(1)
    if opts.list_hosts is True:
        for iter_tmp in fetch_hosts():
            print ('Host: {0} Delay time: {1}'.format(iter_tmp.name(), iter_tmp.delay()))
        sys.exit()


    sheduler = Sheduler(sheduler_queue, hosts_primary)
    sheduler.daemon = True
    sheduler.start()

    ph = Ping_host(sheduler_queue)
    ph.daemon = True
    ph.start()
    time.sleep(1)

    C.close()
if __name__ == '__main__':
    main()
