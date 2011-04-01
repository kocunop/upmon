import os, sys
import sqlite3
import ping_delay
from platform import node


def hlp():
    print('''Usage: [function] [parameters] \n
      [function] \n
        add hostname [time(default 5000)]  - to add host in DB\n
        del hostname - to delete host from DB\n
          example:\n
           upmon.py add 192.168.1.1 5000\n
           upmon.py del dev.z-gu.ru
                        ''')


#def read_arg():
#    args = []
#    for arg in sys.argv[2:4]:
#      args.append(arg)
#    if len(args) ==1 :
#        return args[0]
#    else:
#        print(args[0],args[1])
#        return args[0] #, args[1]  #TODO: убрать костыль

def ins_db(hostname = [],repit_t = 5000,ch = True):
    try:
        c.execute('create table hosts_for_ping(h,t,p)')
    except sqlite3.OperationalError:
        try:
            c.execute('select * from hosts_for_ping where h=?',(hostname))
        except sqlite3.OperationalError:
            c.execute("insert into hosts_for_ping values(?,?,?)", (hostname,repit_t,ch))
            connection.commit()

def del_db(hostmane):
    try:
        c.execute('delete from hosts_for_ping where h=?',(hostmane,))
        connection.commit()
    except sqlite3.OperationalError:
        return 


def fetch_hosts(primary = True):
    hostnames = []
    times = []
    try:
        for hostname, time in c.execute('select h,t  from hosts_for_ping where p=?',(primary,)):
            hostnames.append(hostname)
            times.append(time)
    except sqlite3.OperationalError:
        print('DB is empty, add host first \n')
        hlp()
    return hostnames, times

connection =  sqlite3.connect("upmondb")
c = connection.cursor()

if len(sys.argv) > 1:
    if sys.argv[1] in ('-h','-help','--help'):
        hlp()
    elif sys.argv[1] == 'add':             #если добавляем
        if len(sys.argv) == 3:
            ins_db(sys.argv[2])
        else:
            ins_db(sys.argv[2],sys.argv[3])
    elif sys.argv[1] == 'del':
        del_db(sys.argv[2])

host_primary = []
hosts_primary = fetch_hosts()

for hostname in hosts_primary[0]:
    servname = node()
    ho = ping_delay.delay * 1000
    try:
        c.execute('create table ping_stat(h,s,t)')
    except sqlite3.OperationalError:
        c.execute("insert into ping_stat values(?,?,?)", (hostname,servname,ho))
        connection.commit()

print('Первая табл\n')
for i in c.execute('select * from hosts_for_ping'):
    print(i)
print('\n2 табл\n')
for i in c.execute('select * from ping_stat'):
    print(i)
c.close()