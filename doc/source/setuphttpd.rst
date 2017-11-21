.. _`Setup web server for running RESTful API`:

Setup web server for running RESTful API
****************************************

Each z/VM Cloud Connector API is exposed through a RESTful interface, higher level
systems can manage z/VM by consuming these RESTful APIs directly.

This document describes how to setup web server for hosting the z/VM Cloud Connector RESTful APIs.

The recommended deployment for z/VM Cloud Connector is to have a real web server such as
Apache HTTPD or nginx handle the HTTP connections and proxy requests to the independent
z/VM SDK server running under a wsgi container such as uwsgi. 

The detailed setup steps for each type of web server product is out of this document's range,
you can refer to the specific guide of your chosen web server. This guide would take Apache and uwsgi
on RHEL7.2 as a sample about the deployment process, you can setup your own web server similarly.

Installation
============

The following packages need to be installed:

* Apache httpd server
* uwsgi
* Apache modules for wsgi: mod_wsgi

Configuration
=============

Configure uwsgi
---------------

Usually the configuration can be placed at /etc/uwsgi.d/ folder, for example, named as
/etc/uwsgi.d/your_config.ini. Update the file to match your system configuration.

The sample below indicated the uwsgi service will be running at port 35000
so apache server can connect port 35000 and communicate with it

.. code-block:: text

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
    wsgi-file = /usr/bin/zvmsdk-wsgi
    logger = file:/var/log/zvmsdk/zvmsdk-wsgi.log
    pidfile = /tmp/zvmsdk-wsgi.pid
    socket = /tmp/zvmsdk-wsgi.socket

Start z/VM Cloud Connector in uwsgi
-----------------------------------

* Create a uwsgi service

  Use following sample to create a uwsgi service for running the z/VM Cloud Connector.
  For RHEL7.2, put this file as /usr/lib/systemd/system/zvmsdk-wsgi.service.

.. code-block:: text

    [Unit]
    Description=z/VM Cloud Connector uwsgi
    After=syslog.target network.target httpd.service

    [Service]
    Type=simple
    ExecStart=/usr/sbin/uwsgi --ini /etc/uwsgi.d/your_config.ini
    ExecReload=/usr/sbin/uwsgi --reload /etc/uwsgi.d/your_config.ini
    ExecStop=/usr/sbin/uwsgi --stop /etc/uwsgi.d/your_config.ini

    [Install]
    WantedBy=multi-user.target

* Start zvmsdk uwsgi service

.. code-block:: text

    #systemctl start zvmsdk-wsgi.service

Configure Apache
----------------

Use the following sample as a start for apache to proxy requests to z/VM Cloud Connector
wsgi service, copy the content to  /etc/httpd/conf.d/zvmsdk.conf and update the file to match
your system and requirements.

Under this sample's configuration settings, the httpd server will listen on port 8080
and any incoming request on it will be redirected to zvmsdk wsgi which is listening
at port 35000

.. code-block:: text

    Listen 8080

    <VirtualHost *:8080>
       ProxyPass / uwsgi://127.0.0.1:35000/
    </VirtualHost>

    ProxyPass / uwsgi://127.0.0.1:35000/

SSL is strongly recommended for security considerations. Refer to the specific web server
documentation on how to enable SSL.

Start Apache service
--------------------

.. code-block:: text

    #systemctl start httpd.service

Verification
============

Verify your settings after restart httpd servers (assume you are using above
configurations), if are you able to see similar output below, it means the zvmsdk
http service is running well.

.. code-block:: text

    user@ubuntu1:~$curl localhost:8080
    {"versions": [{"min_version": "1.0", "version": "1.0", "max_version": "1.0"}]}
