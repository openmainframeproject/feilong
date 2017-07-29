******************************
Env setup for SDK httpd server
******************************

This is the document that describe the setup of using http service
of zvm sdk (zvm cloud connector).

============
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

============
uwsgi server
============

uwsgi_ via mod_proxy_uwsgi_ is recommended to be used

.. _uwsgi: https://uwsgi-docs.readthedocs.io/
.. _mod_proxy_uwsgi: http://uwsgi-docs.readthedocs.io/en/latest/Apache.html#mod-proxy-uwsgi

==========================================
Sample configuration steps based on apache
==========================================

* make sure installed following items
   - apache httpd server
   - uwsgi and apache modules for uwsgi 

* Create a uwsgi configuration file (your_config_file)::

   [uwsgi]
   chmod-socket = 666
   # socket = /var/run/uwsgi/sdk-api.socket
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

* Create a uwsgi service::

   [Unit]
   Description=zvm sdk uwsgi
   After=syslog.target network.target httpd.service

   [Service]
   Type=simple
   User=your_user
   ExecStart=/usr/sbin/uwsgi --ini /etc/your_config_file
   ExecReload=/usr/sbin/uwsgi --reload /tmp/your_pid_file
   ExecStop=/usr/sbin/uwsgi --stop /tmp/your_pid_file

   [Install]
   WantedBy=multi-user.target

* Start the uwsgi service created at above step

* Create Apache setting, e.g /etc/apache2/sites-available/010-sdkapi.conf::

   Listen 8080

   <VirtualHost *:8080>
      ProxyPass / uwsgi://127.0.0.1:35000/
   </VirtualHost>

   ProxyPass / uwsgi://127.0.0.1:35000/

* Verify your settings after restart apache servers::

   user@ubuntu1:~$curl localhost:8080
   {"versions": [{"min_version": "1.0", "version": "1.0", "max_version": "1.0"}]}
