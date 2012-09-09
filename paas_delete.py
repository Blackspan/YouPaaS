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


""" Parameter OpenStack """
yp = client.Client(dicoval['user_os'], dicoval['password_os'],  dicoval['tenant_os'], dicoval['authurl_os'], service_type="compute")


try:
	os.system('rm youpaas_key.pem req_value cnt_req youpaas.db req_value2 cnt_req2')
	l = yp.servers.find(name = dicoval['nginx'])
        m = l.id
        yp.servers.delete(m)
	l = yp.servers.find(name = dicoval['apache'])
        m = l.id
        yp.servers.delete(m)
	l = yp.servers.find(name = dicoval['sql'])
        m = l.id
        yp.servers.delete(m)
except:
	pass

