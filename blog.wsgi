#!/usr/bin/python3.8
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/blog/")

from blog import app as application
application.secret_key = 'aman@1234#'
