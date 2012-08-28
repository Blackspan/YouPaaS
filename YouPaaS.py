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
                c.execute("CREATE TABLE mysqlserv(id INTEGER PRIMARY KEY, date text, hostname text, hostip text, state real)")
                c.execute("CREATE TABLE apacheserv(date text, hostname text, hostip text, state real)")
                c.execute("CREATE TABLE nginxserv(date text, hostname text, hostip text, state real)")
                c.execute("CREATE TABLE floatip(date text, hostip text)")
                conn.commit()
                print 'Creation de la base de donnees'
except:
        print 'Base de donnees existante'
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
        time.sleep(10)
        #""" Apache """
        apache = yp.security_groups.find(name='apache_secure')
        apache_id = apache.id
        yp.security_group_rules.create( apache_id, 'tcp', '22', '22', dicoval['cidr'] )
        yp.security_group_rules.create( apache_id, 'tcp', '8080', '8080', dicoval['cidr'] )
        yp.security_group_rules.create( apache_id, 'tcp', '3306', '3306', dicoval['cidr'] )
        yp.security_group_rules.create( apache_id, 'tcp', '21', '21', dicoval['cidr'] )
        time.sleep(10)
        #""" Nginx """
        nginx = yp.security_groups.find(name='nginx_secure')
        nginx_id = nginx.id
        yp.security_group_rules.create( nginx_id, 'tcp', '22', '22', dicoval['cidr'] )
        yp.security_group_rules.create( nginx_id, 'tcp', '80', '8080', '0.0.0.0/0' )
        time.sleep(10)
except:
        print 'Access and Security Ok'
else:
        print '.'

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
        print 'MySQL Server'
        time.sleep(30)
        x = yp.servers.find(name =  dicoval['sql'])
        w = x.networks['private_3'][0]
        v = x.status
        c.execute("INSERT INTO mysqlserv VALUES (?, ?, ?, ?, ?)",('1', now, dicoval['sql'], w, v,))
        conn.commit()
try:
        a = yp.servers.find(name = dicoval['sql'])
        b = a.status
        if b == 'ACTIVE':
                print 'MySQL Server deja Ok'
        else:
                time.sleep(2)
except:
        print 'Launch'
        sqlinit(dicoval['sql'])
        time.sleep(20)
        pass

def webserverinit(name):
        """ Launch Apache Server"""
        yp.servers.create(
        name, dicoval['default_image'],
        dicoval['default_flavor'],
        security_groups=['apache_secure'],
        key_name='youpaas_key',
        userdata = open(dicoval['apache-init-file']))
        print 'Web Server'
        time.sleep(30)
        a = yp.servers.find(name =  dicoval['apache'])
        b = a.networks['private_3'][0]
        v = a.status
        c.execute("INSERT INTO apacheserv VALUES (?, ?, ?, ?)",(now, dicoval['apache'], b, v,))
        conn.commit()

try:
        a = yp.servers.find(name = dicoval['apache'])
        b = a.status
        if b == 'ACTIVE':
                print 'Web Server deja Ok'
        else:
                time.sleep(1)
except:
        print 'Launch'
        webserverinit(dicoval['apache'])
        time.sleep(20)
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
                print 'Nginx deja Ok'
        else:
                time.sleep(1)
except:
        print 'Launch user data nginx init'
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
        print 'Nginx Server'
        time.sleep(15)
        x = yp.servers.find(name =  dicoval['sql'])
        w = x.networks['private_3'][0]
        v = x.status
        c.execute("INSERT INTO nginxserv VALUES (?, ?, ?, ?)",(now, dicoval['nginx'], w, v,))
        conn.commit()

try:
        a = yp.servers.find(name = dicoval['nginx'])
        b = a.status
        if b == 'ACTIVE':
                print 'Nginx Server deja Ok'
        else:
                time.sleep(2)
except:
        print 'Launch'
        datanginx()
        nginxinit(dicoval['nginx'], dicoval['tmpnginxone'])
        time.sleep(20)
        pass
def allservers():
        """Affiche tous les serveurs du tenant"""
        servers = yp.servers.list()
        for s in servers:
             s.get()
             print '%s %s' % (s.name, s.status)
        time.sleep(1)

def associp(name):
        """ Associate Floating IP in Nginx """
        ip = yp.floating_ips.create(pool = dicoval['pool'])
        name.add_floating_ip(ip.ip)
        print '------ Complete ------'
try:
        a = yp.servers.find(name = dicoval['nginx'])
        b = a.id
        i = yp.floating_ips.find(instance_id = b)
        j = i.instance_id
        if b == j:
                print 'Ip Flottante deja attribue au proxy'
        else:
                time.sleep(2)
except:
        print 'Association Floating IP'
        servers = yp.servers.list()
        associp(servers[0])
        pass

time.sleep(30)

def triapache(namos):
        """ Fonction apache """
        a = yp.servers.find(name = namos)
        b = a.networks['private_3'][0]
        h = ":8080/server-status -o req_value2 | clear"
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
        os.system("rm -rf nbre_req2")
        try:
                path = open('cnt_req2','rb')
                ligne = path.readline()
                counts = ligne[0:3]
                count2 = float(counts)
        except:
                pass

while True:
        """ Fonction apache """
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
                path = open('cnt_req','rb')
                ligne = path.readline()
                counts = ligne[0:3]
                count = float(counts)
                reqs = dicoval['req']
                county = float(reqs)
                time.sleep(1)
        except:
                pass
        if count >= county:
                print("-- Overload --")
                try:
                        a = yp.servers.find(name = dicoval['secapache'])
                        b = a.status
                        if b == 'ACTIVE':
                                print '.'
                        else:
                                print '.'
                except:
                        webserverinit(dicoval['secapache'])
                        time.sleep(20)
                        pass

                print(".")
                try:
                        m = yp.servers.find(name = dicoval['nginx'])
                        n = m.networks['private_3'][1]
                        p = yp.servers.find(name = dicoval['apache'])
                        r = p.networks['private_3'][0]
                        a = yp.servers.find(name = dicoval['secapache'])
                        b = a.networks['private_3'][0]
                except:
                        pass

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
                print(".")

                try:
                        a = yp.servers.find(name = dicoval['secnginx'])
                        b = a.status
                        if b == 'ACTIVE':
                                print '.'
                        else:
                                print '.'
                except:
                        print '.'
                        nginxinit(dicoval['secnginx'], dicoval['tmpnginx'])
                        time.sleep(15)
                        pass

                print(".")
                os.system('rm -rf /tmp/*')

                #deallocate ip first nginx
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
                                print '.'
                                servers = yp.servers.list()
                                removeip(servers[0], h)
                        else:
                                time.sleep(1)
                except:
                        print '.'

                #delete the first server nginx
                try:
                        l = yp.servers.find(name = dicoval['nginx'])
                        m = l.id
                        yp.servers.delete(m)
                        print(".")
                except:
                        pass

                #allocate second nginx
                def allocateip(names, addresss):
                        """ Allocate Floating IP in Second Nginx """
                        names.add_floating_ip(addresss)

                try:
                        i = yp.floating_ips.list()
                        z = i[0]
                        h = z.ip
                        servers = yp.servers.list()
                        allocateip(servers[0], h)
                        time.sleep(1)
                except:
                        print '.'
                        time.sleep(1)
                # Troisieme apache provisoire
                try:
                        apacount = yp.servers.find(name = dicoval['secapache'])
                        apacounts = apacount.status
                        if apacounts == 'ACTIVE':
                                triapache(dicoval['secapache'])
                        else:
                                print '.'
                except:
                        pass
        else:
                def nginxreinit():
                        """ Demarrage du proxy aveca premiere configuration"""
                        datanginx()
                        nginxinit(dicoval['nginx'], dicoval['tmpnginxone'])
                        time.sleep(15)
                try:
                        c.execute("DROP TABLE secapache")
                        c.execute("DROP TABLE secnginx")
                        conn.commit()
                except:
                        pass
                        print '-- Charge normale --'
                        time.sleep(1)

        try:
                apa02 = yp.servers.find(name = dicoval['secapache'])
                apastatus = apa02.status
                if count <= county and apastatus == 'ACTIVE':
                        nginxreinit()
                        l = yp.servers.find(name = dicoval['secapache'])
                        m = yp.servers.find(name = dicoval['secnginx'])
                        n = l.id
                        o = m.id
                        yp.servers.delete(n)
                        yp.servers.delete(o)
                        time.sleep(10)
                        try:
                                i = yp.floating_ips.list()
                                z = i[0]
                                h = z.ip
                                servers = yp.servers.list()
                                allocateip(servers[0], h)
                                time.sleep(1)
                        except:
                                print '.'
                                time.sleep(1)
                else:
                        print '.'
        except:
                pass

conn.commit()
path.close()
