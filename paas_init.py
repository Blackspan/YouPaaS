#!/usr/bin/python
# -*- coding: Utf-8 -*-
import logging
import time
import sys
import subprocess
import string
import os
import StringIO
import datetime
import novaclient
from novaclient.v1_1 import *
import base64
import sqlite3
import sqlite3 as lite
logging.basicConfig(
filename='/var/log/youpaas.log',
level=logging.INFO,
format='%(asctime)s %(levelname)s - %(message)s',
datefmt='%d/%m/%Y %H:%M:%S',
)

logging.info('youpaas start')
dicoval={}
path = open('conf.txt','rb')
lignes = path.readlines()
for lig in lignes:
        sp = lig.split('#')[0]
        sp = sp.split('=')
        if len(sp)==2: dicoval[sp[0].strip()]=sp[1].strip()
""" Creating database and tables for the program """
try:
        class database():
                conn = sqlite3.connect(dicoval['bdd'])
                c = conn.cursor()
                c.execute("CREATE TABLE mysql(id INTEGER PRIMARY KEY, date text, hostname text, hostip text, state real)")
                c.execute("CREATE TABLE apache(date text, hostname text, hostip text, state real)")
                c.execute("CREATE TABLE nginx(date text, hostname text, hostip text, state real)")
                c.execute("CREATE TABLE floatip(date text, hostip text, ip_public text)")
                c.execute("CREATE TABLE seconde_apache(date text, hostname text, hostip text, state real)")
                c.execute("CREATE TABLE seconde_nginx(date text, hostname text, hostip text, state real)")
                c.execute("CREATE TABLE request(hostname text, hostip text, nombre INTEGER)")
                conn.commit()
                print 'creating a database with the tables'
except:
        print 'database exists'
        pass

""" Parameter OpenStack """
yp = client.Client(dicoval['user_os'], dicoval['password_os'],  dicoval['tenant_os'], dicoval['authurl_os'], service_type="compute")
"""configuration access and security"""
try:
        conn = sqlite3.connect(dicoval['bdd'])
        c = conn.cursor()
        now = datetime.datetime.now()
        keypairs = yp.keypairs.create('youpaas_key')
        kprivate = keypairs.private_key
        file = open("youpaas_key.pem", "w")
        file.write(kprivate)
        file.close()
        yp.security_groups.create(dicoval['secgroup-sql'], 'Security group for Mysql')
        yp.security_groups.create(dicoval['secgroup-apa'], 'Security group for apache')
        yp.security_groups.create(dicoval['secgroup-ngx'], 'Security group for nginx')
        #""" Mysql """
        mysql = yp.security_groups.find(name='mysql_secure')
        mysql_id = mysql.id
        yp.security_group_rules.create( mysql_id, 'tcp', '22', '22', dicoval['cidr'] )
        yp.security_group_rules.create( mysql_id, 'tcp', '3306', '3306', dicoval['cidr'] )
        time.sleep(15)
        #""" Apache """
        apache = yp.security_groups.find(name='apache_secure')
        apache_id = apache.id
        yp.security_group_rules.create( apache_id, 'tcp', '22', '22', dicoval['cidr'] )
        yp.security_group_rules.create( apache_id, 'tcp', '8080', '8080', dicoval['cidr'] )
        yp.security_group_rules.create( apache_id, 'tcp', '3306', '3306', dicoval['cidr'] )
        time.sleep(15)
        #""" Nginx """
        nginx = yp.security_groups.find(name='nginx_secure')
        nginx_id = nginx.id
        yp.security_group_rules.create( nginx_id, 'tcp', '22', '22', dicoval['cidr'] )
        yp.security_group_rules.create( nginx_id, 'tcp', '80', '8080', '0.0.0.0/0' )
        time.sleep(15)
except:
        print 'access and security already congured'
else:
        print 'access and security configured'

""" Initialization """
def sqlinit(name):
        """ Launch SQL Server"""
        now = datetime.datetime.now()
        yp.servers.create(
        name, dicoval['default_image'],
        dicoval['default_flavor'],
        security_groups=['mysql_secure'],
        key_name='youpaas_key',
        userdata = open(dicoval['sql-init-file']))
        print 'mysql server'
        time.sleep(30)

try:
        a = yp.servers.find(name = dicoval['sql'])
        b = a.status
        if b == 'ACTIVE':
                print 'mysql server already start'
        else:
                time.sleep(2)
except:
        sqlinit(dicoval['sql'])
        time.sleep(20)
        x = yp.servers.find(name =  dicoval['sql'])
        w = x.networks['private_3'][0]
        v = x.status
        c.execute("INSERT INTO mysql VALUES (?, ?, ?, ?, ?)",('1', now, dicoval['sql'], w, v,))
        conn.commit()
        pass

def webserverinit(name):
        """ Launch Apache Server"""
        yp.servers.create(
        name, dicoval['default_image'],
        dicoval['default_flavor'],
        security_groups=['apache_secure'],
        key_name='youpaas_key',
        userdata = open(dicoval['apache-init-file']))
        print 'web server'
        time.sleep(30)

try:
        a = yp.servers.find(name = dicoval['apache'])
        b = a.status
        if b == 'ACTIVE':
                print 'web server already start'
        else:
                time.sleep(1)
except:
        webserverinit(dicoval['apache'])
        time.sleep(20)
        a = yp.servers.find(name =  dicoval['apache'])
        b = a.networks['private_3'][0]
        v = a.status
        c.execute("INSERT INTO apache VALUES (?, ?, ?, ?)",(now, dicoval['apache'], b, v,))
        conn.commit()
        pass

def datanginx():
        """ User-data for Nginx Server"""
        os.system('rm -rf /tmp/*')
        os.system('cp nginx-data-init /tmp/nginx-data-init.txt')
        m = yp.servers.find(name = dicoval['apache'])
        n = m.networks['private_3'][0]
        du = dicoval['tmpnginxone']
        f = open( du, 'r')
        chaine = f.read()
        result = chaine.replace("apacheip", n)
        f = open(dicoval['tmpnginxone'],'w')
        f.write(result)
        f.close()

try:
        a = yp.servers.find(name = dicoval['nginx'])
        b = a.status
        if b == 'ACTIVE':
                print 'nginx server already start'
        else:
                time.sleep(1)
except:
        datanginx()
        time.sleep(2)
        pass

def nginxinit(name, userdata):
        """ Launch Nginx Server"""
        yp.servers.create(
        name, dicoval['default_image'],
        dicoval['default_flavor'],
        security_groups=['nginx_secure'],
        key_name='youpaas_key',
        userdata = open(userdata))
        print 'nginx server'
        time.sleep(15)

try:
        a = yp.servers.find(name = dicoval['nginx'])
        b = a.status
        if b == 'ACTIVE':
                print 'nginx server already start'
        else:
                time.sleep(2)
except:
        datanginx()
        nginxinit(dicoval['nginx'], dicoval['tmpnginxone'])
        time.sleep(20)
        x = yp.servers.find(name =  dicoval['nginx'])
        w = x.networks['private_3'][0]
        v = x.status
        c.execute("INSERT INTO nginx VALUES (?, ?, ?, ?)",(now, dicoval['nginx'], w, v,))
        conn.commit()
        pass
def allservers():
        """Displays all servers of tenant"""
        servers = yp.servers.list()
        for s in servers:
             s.get()
             print '%s %s' % (s.name, s.status)
        time.sleep(1)

now = datetime.datetime.now()

def associp(name):
        """ Associate Floating IP in Nginx """
        ip = yp.floating_ips.create(pool = dicoval['pool'])
        name.add_floating_ip(ip.ip)
        print '-- initialisation complete --'
try:
        a = yp.servers.find(name = dicoval['nginx'])
        b = a.id
        i = yp.floating_ips.find(instance_id = b)
        j = i.instance_id
        if b == j:
                print 'public ip already attribute'
        else:
                time.sleep(2)
except:
        servers = yp.servers.list()
        associp(servers[0])
        time.sleep(10)
        ai = yp.servers.find(name =  dicoval['apache'])
        bi = ai.networks['private_3'][0]
        bo = '0'
        x = yp.servers.find(name =  dicoval['nginx'])
        w = x.networks['private_3'][0]
        c.execute("INSERT INTO floatip VALUES (?, ?, ?)",(now, dicoval['nginx'], w,))
        c.execute("INSERT INTO request VALUES (?, ?, ?)",(dicoval['apache'], bi, bo,))
        c.execute("INSERT INTO request VALUES (?, ?, ?)",(dicoval['secapache'], bi, bo,))
        c.execute("INSERT INTO request VALUES (?, ?, ?)",('all_servers', bi, bo,))
        conn.commit()
        pass

print '-- wait a few minutes --'

time.sleep(60)

def countreq(names):
        """Function that counts the number of requests for the second web server apache """
        a = yp.servers.find(name = names)
        b = a.networks['private_3'][0]
        h = ":8080/server-status -o req_value2"
        os.system("rm -rf nbre_req2 cnt_req2 req_value2")
        os.system("curl --http1 http://"+ b + h)
        os.system("touch nbre_req2")
        os.system("touch cnt_req2")
        os.system("touch req_value2")
        var = 'requests currently being processed'
        fichier = open("req_value2","r")
        for ligne in fichier:
                if var in ligne:
                        print ligne
                        file = open("nbre_req2","w")
                        file.write(ligne)
                        file.close()
        fichier.close()
        os.system("cat nbre_req2 | sed -n '1p'| sed 's/<dt>//' |cut -d 'r' -f1 > cnt_req2")
        os.system("rm -rf nbre_req2 ")
        try:
                path = open('cnt_req2','rb')
                ligne = path.readline()
                counts = ligne[0:3]
                count2 = float(counts)
                triapa = count + count2
                triapas = float(triapa)
                print '.'
                time.sleep(1)
        except:
                pass

while True:
        """ The function counts the number of requests for the first web server apache. """
        a = yp.servers.find(name = dicoval['apache'])
        b = a.networks['private_3'][0]
        h = ":8080/server-status -o req_value | clear"
        os.system("rm -rf nbre_req cnt_req req_value")
        os.system("curl --http1 http://"+ b + h)
        os.system("touch nbre_req")
        os.system("touch cnt_req")
        os.system("touch req_value")
        var = 'requests currently being processed'
        fichier = open("req_value","r")
        for ligne in fichier:
                if var in ligne:
                        print ligne
                        file = open("nbre_req","w")
                        file.write(ligne)
                        file.close()
        fichier.close()
        os.system("cat nbre_req | sed -n '1p'| sed 's/<dt>//' |cut -d 'r' -f1 > cnt_req")
        os.system("rm -rf nbre_req")
        time.sleep(1)
        try:
                ae = yp.servers.find(name = dicoval['secapache'])
                be = ae.status
                if be == 'ACTIVE':
                        countreq(dicoval['secapache'])
                else:
                        print 'Pas active'
        except:
                pass

        try:
                path = open('cnt_req','rb')
                ligne = path.readline()
                counts = ligne[0:3]
                count = float(counts)
                reqs = dicoval['req']
                county = float(reqs)
                ae = yp.servers.find(name = dicoval['apache'])
                be = ae.status
                if be == 'ACTIVE':
                        c.execute("UPDATE request SET nombre=? WHERE hostname=?", ( count, dicoval['apache'],))
                        conn.commit()
                        time.sleep(1)
                else:
                        print '.no update request'
                        pass
        except:
                pass

        try:
                a = yp.servers.find(name = dicoval['secapache'])
                b = a.status
                if b == 'ACTIVE':
                        path = open('cnt_req','rb')
                        ligne = path.readline()
                        counts = ligne[0:3]
                        count = float(counts)
                        print 'number of requests web server 1'
                        print count
                        path = open('cnt_req2','rb')
                        ligne = path.readline()
                        counts = ligne[0:3]
                        count2 = float(counts)
                        print 'number of requests web server 2'
                        print count2
                        last = count + count2
                        lasts = float(last)
                        count = lasts
                        print 'all requests web server 1 and 2'
                        print count
                        time.sleep(1)
                        c.execute("UPDATE request SET nombre=? WHERE hostname=?", ( count,'all_servers',))
                        c.execute("UPDATE request SET nombre=? WHERE hostname=?", ( count2, dicoval['secapache'],))
                        conn.commit()
                else:
                        print '.'
        except:
                pass

        if count >= county:
                print("- Overload -")
                try:
                        a = yp.servers.find(name = dicoval['secapache'])
                        b = a.status
                        if b == 'ACTIVE':
                                print ''
                        else:
                                print ''
                except:
                        webserverinit(dicoval['secapache'])
                        time.sleep(20)
                        now = datetime.datetime.now()
                        x = yp.servers.find(name =  dicoval['secapache'])
                        w = x.networks['private_3'][0]
                        v = x.status
                        c.execute("INSERT INTO seconde_apache VALUES (?, ?, ?, ?)",(now, dicoval['secapache'], w, v,))
                        conn.commit()
                        print ''
                        time.sleep(5)
                        m = yp.servers.find(name = dicoval['nginx'])
                        n = m.networks['private_3'][1]
                        print n
                        time.sleep(10)
                        p = yp.servers.find(name = dicoval['apache'])
                        r = p.networks['private_3'][0]
                        print r
                        time.sleep(10)
                        a = yp.servers.find(name = dicoval['secapache'])
                        b = a.networks['private_3'][0]
                        print b
                        time.sleep(10)
                        #fin
                        pass
                try:
                        print '.ud'
                        os.system('rm -rf /tmp/*')
                        os.system('cp nginx-data-sec-apache.txt /tmp/nginx-data-sec-apache.txt')
                        f = open(dicoval['tmpnginx'],'r')
                        chaine = f.read()
                        result = chaine.replace("apacheip", n)
                        f = open(dicoval['tmpnginx'],'w')
                        f.write(result)
                        f.close()
                        f = open(dicoval['tmpnginx'],'r')
                        chaine = f.read()
                        result = chaine.replace("varapache1", r)
                        f = open(dicoval['tmpnginx'],'w')
                        f.write(result)
                        f.close()
                        f = open(dicoval['tmpnginx'],'r')
                        chaine = f.read()
                        result = chaine.replace("varapache2", b)
                        f = open(dicoval['tmpnginx'],'w')
                        f.write(result)
                        f.close()
                except:
                        pass

                try:
                        a = yp.servers.find(name = dicoval['secnginx'])
                        b = a.status
                except:
                        nginxinit(dicoval['secnginx'], dicoval['tmpnginx'])
                        time.sleep(15)
                        now = datetime.datetime.now()
                        x = yp.servers.find(name =  dicoval['secnginx'])
                        w = x.networks['private_3'][0]
                        v = x.status
                        c.execute("INSERT INTO seconde_nginx VALUES (?, ?, ?, ?)",(now, dicoval['secnginx'], w, v,))
                        conn.commit()
                        time.sleep(45)
                        pass

                def removeip(name, address):
                        """ Remove Floating IP in Nginx """
                        name.remove_floating_ip(address)
                try:
                        a = yp.servers.find(name = dicoval['nginx'])
                        b = a.id
                        i = yp.floating_ips.find(instance_id = b)
                        j = i.instance_id
                        h = i.ip
                        if b == j:
                                servers = yp.servers.list()
                                removeip(servers[0], h)
                        else:
                                time.sleep(1)
                except:
                        print ''

                try:
                        l = yp.servers.find(name = dicoval['nginx'])
                        m = l.id
                        yp.servers.delete(m)
                        c.execute("UPDATE nginx SET state=? WHERE hostname=?", ('DOWN', dicoval['nginx'],))
                        conn.commit()
                except:
                        pass

                def allocateip(names, addresss):
                        """ Allocate Floating IP in Second Nginx """
                        names.add_floating_ip(addresss)

                try:
                        i = yp.floating_ips.list()
                        z = i[0]
                        h = z.ip
                        servers = yp.servers.list()
                        allocateip(servers[0], h)
                        print 'attribute public ip in the new proxy'
                        print 'website up'
                        time.sleep(60)
                except:
                        print '.go'
                        time.sleep(1)
        else:
                def nginxreinit():
                        """ Demarrage du proxy aveca premiere configuration"""
                        datanginx()
                        nginxinit(dicoval['nginx'], dicoval['tmpnginxone'])
                        time.sleep(15)
                        x = yp.servers.find(name =  dicoval['nginx'])
                        w = x.networks['private_3'][0]
                        c.execute("UPDATE nginx SET hostip=? WHERE hostname=?", (w, dicoval['nginx'],))
                        conn.commit()
                        time.sleep(60)

                try:
                        print '- normal load -'
                        time.sleep(1)
                except:
                        pass
                        print '- normal load -'
                        time.sleep(1)

        try:
                apa02 = yp.servers.find(name = dicoval['secapache'])
                apastatus = apa02.status
                if count < county and apastatus == 'ACTIVE':
                        nginxreinit()
                        time.sleep(30)
                        c.execute("DELETE FROM seconde_apache WHERE hostname='YouPaaSApache02'")
                        c.execute("DELETE FROM seconde_nginx WHERE hostname='YouPaaSNginx02'")
                        c.execute("UPDATE request SET nombre=? WHERE hostname=?", ( '0','all_servers',))
                        c.execute("UPDATE request SET nombre=? WHERE hostname=?", ( '0', dicoval['secapache'],))
                        conn.commit()
                        l = yp.servers.find(name = dicoval['secapache'])
                        m = yp.servers.find(name = dicoval['secnginx'])
                        n = l.id
                        o = m.id
                        yp.servers.delete(n)
                        yp.servers.delete(o)
                        time.sleep(10)
                        c.execute("UPDATE nginx SET state=? WHERE hostname=?", ( 'ACTIVE', dicoval['nginx'],))
                        conn.commit()
                        try:
                                i = yp.floating_ips.list()
                                z = i[0]
                                h = z.ip
                                servers = yp.servers.list()
                                allocateip(servers[0], h)
                                time.sleep(1)
                        except:
                                print ''
                                time.sleep(1)
                else:
                        print ''
        except:
                pass

conn.commit()
path.close()
c.close()
