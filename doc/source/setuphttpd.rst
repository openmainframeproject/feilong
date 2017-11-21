.. _`Setup for running RESTful API`:

Setup for running RESTful API
*****************************

Each z/VM Cloud Connector API is exposed through a RESTful interface, higher level
systems can manage z/VM by consuming these RESTful APIs directly.

This document describes how to setup httpd service for z/VM Cloud Connector RESTful API.

httpd server
============

Though the SDK APIs can be run using independent scripts that
provide eventlet-based HTTP servers, it is generally considered better
performance and flexible to run them using a generic HTTP server that
supports WSGI_ (such as Apache_ or nginx_).

https (TLS and SSL) settings are transparent to zvm sdk REST API setting,
please refer to specific HTTP server document for more info.

.. _WSGI: https://www.python.org/dev/peps/pep-3333/
.. _apache: http://httpd.apache.org/
.. _nginx: http://nginx.org/en/

uwsgi server
============

uwsgi_ via mod_proxy_uwsgi_ is recommended to be used

.. _uwsgi: https://uwsgi-docs.readthedocs.io/
.. _mod_proxy_uwsgi: http://uwsgi-docs.readthedocs.io/en/latest/Apache.html#mod-proxy-uwsgi

Sample configuration and steps based on Apache
==============================================

* make sure installed following items::

   - apache httpd server
   - uwsgi and apache modules for uwsgi 

* Create a uwsgi configuration file, usually the configuration can be placed
  at /etc/uwsgi.d/ folder, for example, /etc/uwsgi.d/your_config_file,
  The sample below indicated the uwsgi service will be running at port 35000
  so apache server can connect to port 35000 and communicate with it::

   [uwsgi]
   chmod-socket = 666
   uwsgi-socket = 127.0.0.1:35000
   lazy-apps = true
   add-header = Connection: close
   buffer-size = 65535
   thunder-lock = true
   plugins = python
   enable-threads = true
   exit-on-reload = true
   die-on-term = true
   master = true
   processes = 2
   wsgi-file = /usr/local/bin/sdk-api

* Create a uwsgi service, following sample is based on RHEL and you can 
  create a file /lib/systemd/system/zvmsdk.service, the following contents
  are reference input; for other distribution please refer to their system
  service architecture::

   [Unit]
   Description=zvm sdk uwsgi
   After=syslog.target network.target httpd.service

   [Service]
   Type=simple
   User=your_user
   ExecStart=/usr/sbin/uwsgi --ini /etc/uwsgi.d/your_config_file
   ExecReload=/usr/sbin/uwsgi --reload /etc/uwsgi.d/your_config_file
   ExecStop=/usr/sbin/uwsgi --stop /etc/uwsgi.d/your_config_file

   [Install]
   WantedBy=multi-user.target

* Start the uwsgi service created at above step::

   /bin/systemctl restart  zvmsdk.service

* Create Apache setting, for example in RHEL, /etc/httpd/conf.d/zvmsdk.conf;
  the following contents means the zvmsdk httpd service will running at port 8080
  and any incoming request will be redirected to zvmsdk uwsgi which is listening
  at port 35000::

   Listen 8080

   <VirtualHost *:8080>
      ProxyPass / uwsgi://127.0.0.1:35000/
   </VirtualHost>

   ProxyPass / uwsgi://127.0.0.1:35000/

* Restart httpd service::

  /bin/systemctl restart httpd.service

* Verify your settings after restart httpd servers (assume you are using above
  configurations), if are you able to see similar output below, it means the zvmsdk
  http service is running well::

   user@ubuntu1:~$curl localhost:8080
   {"versions": [{"min_version": "1.0", "version": "1.0", "max_version": "1.0"}]}
