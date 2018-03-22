.. Copyright 2017,2018 IBM Corp. All Rights Reserved.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
..

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
* Apache modules: mod_proxy_uwsgi
* uwsgi
* uwsgi plugin for python: uwsgi-plugin-python


Configuration
=============

Configure uwsgi
---------------

Usually the configuration can be placed at /etc/uwsgi.d/ folder, for example, named as
/etc/uwsgi.d/your_config.ini. Update the file to match your system configuration.

The sample below indicated the uwsgi service will be running at port 35000
so apache server can connect port 35000 and communicate with it

.. literalinclude:: ../../data/uwsgi-zvmsdk.conf


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

* Verify zvmsdk uwsgi service status

  Verify the zvmsdk uwsgi service is started normally and the status is active (running)
  in the following command output.

  .. code-block:: text

      [root@0822rhel7 ~]# systemctl status zvmsdk-wsgi.service
      ● zvmsdk-wsgi.service - z/VM Cloud Connector uwsgi
         Loaded: loaded (/usr/lib/systemd/system/zvmsdk-wsgi.service; disabled; vendor preset: disabled)
         Active: active (running) since Tue 2017-11-21 21:58:06 EST; 13min ago
       Main PID: 7227 (uwsgi)
         CGroup: /system.slice/zvmsdk-wsgi.service
                 ├─7227 /usr/sbin/uwsgi --ini /etc/uwsgi.d/zvmsdk-wsgi.ini
                 ├─7229 /usr/sbin/uwsgi --ini /etc/uwsgi.d/zvmsdk-wsgi.ini
                 └─7230 /usr/sbin/uwsgi --ini /etc/uwsgi.d/zvmsdk-wsgi.ini

      Nov 21 21:58:06 0822rhel7 uwsgi[7227]: your server socket listen backlog is limited to 100 connections
      Nov 21 21:58:06 0822rhel7 uwsgi[7227]: your mercy for graceful operations on workers is 60 seconds
      Nov 21 21:58:06 0822rhel7 uwsgi[7227]: mapped 402621 bytes (393 KB) for 2 cores
      Nov 21 21:58:06 0822rhel7 uwsgi[7227]: *** Operational MODE: preforking ***
      Nov 21 21:58:06 0822rhel7 uwsgi[7227]: *** uWSGI is running in multiple interpreter mode ***
      Nov 21 21:58:06 0822rhel7 uwsgi[7227]: spawned uWSGI master process (pid: 7227)
      Nov 21 21:58:06 0822rhel7 uwsgi[7227]: spawned uWSGI worker 1 (pid: 7229, cores: 1)
      Nov 21 21:58:06 0822rhel7 uwsgi[7227]: spawned uWSGI worker 2 (pid: 7230, cores: 1)
      Nov 21 21:58:06 0822rhel7 uwsgi[7227]: *** no app loaded. going in full dynamic mode ***
      Nov 21 21:58:06 0822rhel7 uwsgi[7227]: *** no app loaded. going in full dynamic mode ***

  And the uwsgi process is listenning on port 35000:

  .. code-block:: text

      # netstat -anp | grep 35000
      tcp        0      0 127.0.0.1:35000         0.0.0.0:*               LISTEN      7227/uwsgi

      # curl -v http://127.0.0.1:35000/
      * About to connect() to 127.0.0.1 port 35000 (#0)
      *   Trying 127.0.0.1...
      * Connected to 127.0.0.1 (127.0.0.1) port 35000 (#0)
      > GET / HTTP/1.1
      > User-Agent: curl/7.29.0
      > Host: 127.0.0.1:35000
      > Accept: */*
      >
      * Empty reply from server
      * Connection #0 to host 127.0.0.1 left intact
      curl: (52) Empty reply from server

.. _`Configure Apache`:

Configure Apache
----------------

Use the following sample as a start for apache to proxy requests to z/VM Cloud Connector
wsgi service, copy the content to  /etc/httpd/conf.d/zvmsdk.conf and update the file to match
your system and requirements.

.. note::
    Sometimes the REST API call will takes some time to complete while the default timeout
    is not enough to complete the handle of the request, for example, `Apache Timeout`_
    shows the default timeout value of Apache httpd server is 60, administrator need to
    set a bigger value (for example 3600) to avoid time out error.

.. _Apache Timeout: https://httpd.apache.org/docs/2.4/mod/core.html#timeout

Under this sample's configuration settings, the httpd server will listen on port 8080
and any incoming request on it will be redirected to zvmsdk wsgi which is listening
at port 35000

.. code-block:: text

    LoadModule proxy_uwsgi_module modules/mod_proxy_uwsgi.so

    Listen 8080

    <VirtualHost *:8080>
       ProxyPass / uwsgi://127.0.0.1:35000/
    </VirtualHost>

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

    # curl http://localhost:8080/
    {"rs": 0, "overallRC": 0, "modID": null, "rc": 0, "output": {"min_version": "1.0", "version": "1.0", "max_version": "1.0"}, "errmsg": ""}

Token Usage
============

When you sending requests, you need a token to get access to the service.
To get the token, you need to get an admin-token from administrator which is stored in admin-token-file.

As an administrator, you are responsible for creating admin-token-file. You can use gen-token tool provided by ZVMConnector.
Fox example, initialize one token file:

.. code-block:: text

    # /usr/bin/gen-token

Gen-tool use **/etc/zvmsdk/token.dat** as default path of token file. You can also specify your own token file path:

.. code-block:: text

    # /usr/bin/gen-token /new/path/of/token/file

So, the commands above will initialize one token file and write a random admin-token into it.
This tool can also help you update the content of token file:

.. code-block:: text

    # /usr/bin/gen-token -u

If you don't assign a file path, gen-token will update the content of default token path.
You can update specified file by this way:

.. code-block:: text

    # /usr/bin/gen-token -u /new/path/of/token/file

After that, the path of token file represented by ``token_path`` should be configured in wsgi section of zvmsdk.conf
and ``auth`` item in the same section should also be set to ``token``, just like auth=token.
And if you want to disable authentication, just set ``auth`` to value ``none``.

As a client, you can get the admin-token stored in the admin-token-file and request for a token by putting the admin_token into the
``X-Admin-Token`` field in headers of request object.

An example to request for a token:

.. code-block:: text

    # curl http://localhost:8080/token -X POST -i -H "Content-Type:application/json" -H "X-Admin-Token:1234567890123456789012345678901234567890"
    HTTP/1.0 200 OK
    Date: Wed, 06 Dec 2017 06:11:22 GMT
    Server: WSGIServer/0.1 Python/2.7.5
    Content-Type: text/html; charset=UTF-8
    Content-Length: 0
    X-Auth-Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MTI1NDQyODJ9.TVlcQb_QuUPJ37cRyzZqroR6kLZ-5zH2-tliIkhsQ1A
    cache-control: no-cache

Then, you can send normal RESTful requests using the return X-Auth-Token field. For example:

.. code-block:: text

    # curl http://localhost:8080/ -H "Content-Type:application/json" -H 'X-Auth-Token:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MTI1NDQyODJ9.TVlcQb_QuUPJ37cRyzZqroR6kLZ-5zH2-tliIkhsQ1A'
    {"rs": 0, "overallRC": 0, "modID": null, "rc": 0, "output": {"min_version": "1.0", "version": "1.0", "max_version": "1.0"}, "errmsg": ""}

If you use ZVMConnector as a client, you can save admin-token-file as /etc/zvmsdk/token.dat and change this file's owner to user zvmsdk.
Now, you have a easier way to use token now:

.. code-block:: text

    >>> from zvmconnector import connector
    >>> conn = connector.ZVMConnector(port=8080)
    >>> conn.send_request('guest_list')
    {u'rs': 0, u'overallRC': 0, u'modID': None, u'rc': 0, u'output': [u'NAME1', u'NAME2'], u'errmsg': u'}

As you can see, you do not need to use them explicitly now because ZVMConnector use /etc/zvmsdk/token.dat as the default path.
You can specify your own token file path by this way:

.. code-block:: text

    >>> from zvmconnector import connector
    >>> conn = connector.ZVMConnector(port=8080, token_path='/your/own/path/token.dat')
