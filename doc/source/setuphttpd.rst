..
 Copyright Contributors to the Feilong Project.
 SPDX-License-Identifier: CC-BY-4.0

.. _`Setup web server for running RESTful API`:

Setup web server for running RESTful API
****************************************

Introduction
============

Each Feilong API is exposed through a RESTful interface, higher level
systems can manage z/VM by consuming these RESTful APIs directly.

This chapter describes how to setup a web server for hosting the Feilong RESTful APIs.

The recommended deployment for Feilong is to have a web server such as
Apache httpd or nginx handle the HTTP connections and proxy requests to the independent
z/VM SDK server running under a wsgi container such as uwsgi
or directly connected via Apache's wsgi module.

The detailed setup steps for each type of web server is out of this document's range,
you can refer to the specific guide of your chosen web server. This guide walks you through
the deployment process, either:
 * with premade packages (which use the mod_wsgi method);
 * manually, with uwsgi;
 * or manually, with Apache's mod_wsgi.

This matrix represents the successful setup of different web servers across three Linux distributions.
The last section of this chapter details about using tokens to enhance security.

====================== ================= ================= =================
Tested                 RHEL 9.4          SLES 15 SP6       Ubuntu 24.04
====================== ================= ================= =================
Apache2 + uwsgi        ✓                                   ✓
Apache2 + mod_wsgi     ✓                 ✓                 ✓
nginx + uwsgi                                                   
====================== ================= ================= =================

Installing from packages
========================

Redhat Enterprise Linux
-----------------------

The following instructions are for RHEL 9.4.
The RPM packages can be downloaded from https://download.opensuse.org/repositories/Virtualization:/feilong/AlmaLinux_9/

Before installing the necessary packages, it is important to set up the EPEL repository.
**Important:** Ensure that the EPEL repository is enabled to access additional packages.

.. code-block:: text

    # dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm


Install the downloaded packages using the `yum` or `dnf` command

..code-block:: text

    # dnf install zthin-<version>-<release>.s390x.rpm
    # dnf install zvmsdk-<version>-<release>.noarch.rpm

If not already done, enable the automatic startup of the Apache server, and then start it:

..code-block:: text

    # systemctl enable httpd
    # systemctl start  httpd

Finally, you can verify if the installation works as intended by making a curl request from your workstation

..code-block:: text

    $ curl http://<your server ip address>:8080/

By default, Feilong will listen on port 8080.
To change that, you need to modify both Apache configuration and firewall rules.


SUSE Linux Enterprise Server
----------------------------

The following instructions are for SLES15 SP5.
The RPM packages can be downloaded from https://download.opensuse.org/repositories/Virtualization:/feilong/SLE_15_SP5/



Install the downloaded packages using the `zypper` command

..code-block:: text

    # zypper install zthin-<version>-<release>.s390x.rpm
    # zypper install zvmsdk-<version>-<release>.noarch.rpm

If not already done, enable the automatic startup of the Apache server, and then start it:

..code-block:: text

    # systemctl enable apache2
    # systemctl start  apache2

Finally, you can verify if the installation works as intended by making a curl request from your workstation

..code-block:: text

    $ curl http://<your server ip address>:8080/

By default, Feilong will listen on port 8080.
To change that, you need to modify both Apache configuration and firewall rules.

Ubuntu
------

(to be written).


Apache2 + uwsgi
===============

Installation
------------
The following packages need to be installed:

* Apache httpd server
* Apache modules: mod_proxy_uwsgi
* uwsgi
* uwsgi plugin for python: uwsgi-plugin-python

Configure uwsgi
---------------

Usually the configuration can be placed at /etc/uwsgi.d/ folder, for example, named as
/etc/uwsgi.d/your_config.ini. Update the file to match your system configuration.

The sample below indicated the uwsgi service will be running at port 35000
so apache server can connect port 35000 and communicate with it

.. literalinclude:: ../../data/uwsgi-zvmsdk.conf

Start Feilong in uwsgi
----------------------

* Create a uwsgi service

  Use following sample to create a uwsgi service for running the Feilong.
  For RHEL7.2, put this file as /usr/lib/systemd/system/zvmsdk-wsgi.service.

  .. code-block:: text

      [Unit]
      Description=Feilong uwsgi
      After=syslog.target network.target httpd.service

      [Service]
      Type=simple
      ExecStart=/usr/sbin/uwsgi --ini /etc/uwsgi.d/your_config.ini
      ExecReload=/usr/sbin/uwsgi --reload /etc/uwsgi.d/your_config.ini
      ExecStop=/usr/sbin/uwsgi --stop /etc/uwsgi.d/your_config.ini

      [Install]
      WantedBy=multi-user.target

* Enable zvmsdk uwsgi service

  .. code-block:: text

      #systemctl enable zvmsdk-wsgi.service

* Start zvmsdk uwsgi service

  .. code-block:: text

      #systemctl start zvmsdk-wsgi.service

* Verify zvmsdk uwsgi service status

  Verify the zvmsdk uwsgi service is started normally and the status is active (running)
  in the following command output.

  .. code-block:: text

      [root@0822rhel7 ~]# systemctl status zvmsdk-wsgi.service
      ● zvmsdk-wsgi.service - Feilong uwsgi
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

Use the following sample as a start for apache to proxy requests to Feilong
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
------------

Verify your settings after restart httpd servers (assume you are using above
configurations), if are you able to see similar output below, it means the zvmsdk
http service is running well.

.. code-block:: text

    # curl http://localhost:8080/
    {"rs": 0, "overallRC": 0, "modID": null, "rc": 0, "output": {"min_version": "1.0", "version": "1.0", "max_version": "1.0"}, "errmsg": ""}


Apache2 + mod_wsgi
==================

Installation
------------
The following packages need to be installed:

* apache2
* libapache2-mod-wsgi

Configuration
-------------

Create a vhost for Feilong in Apache. Copy the following content to
/etc/apache2/sites-available/zvmsdk_wsgi.conf and update the file to match your system and requirements.

Then execute command "a2ensite zvmsdk_wsgi" to enable the site.

.. code-block:: text

    Listen 8080
    <VirtualHost *:8080>
        WSGIDaemonProcess zvmsdkwsgi user=zvmsdk group=zvmsdk processes=2 threads=5
            WSGIProcessGroup zvmsdkwsgi

        WSGIScriptAlias / /usr/bin/zvmsdk-wsgi
        <Directory /usr/lib/python2.7/dist-packages/zvmsdk/sdkwsgi>
            Require all granted
        </Directory>

        <Directory /usr/bin>
        <Files zvmsdk-wsgi>
            Require all granted
        </Files>
        </Directory>
    </VirtualHost>

SSL is strongly recommended for security considerations. Refer to the specific web server 
documentation on how to enable SSL.

* Start Apache service

  .. code-block:: text

      #systemctl start apache2.service

Verification
------------

Verify your settings after restart httpd servers (assume you are using above
configurations), if are you able to see similar output below, it means the zvmsdk
http service is running well.

.. code-block:: text

    # curl http://localhost:8080/
    {"rs": 0, "overallRC": 0, "modID": null, "rc": 0, "output": {"min_version": "1.0", "version": "1.0", "max_version": "1.0"}, "errmsg": ""}


.. _`TokenUsage`:


Securing Connections with Tokens
================================

When you sending requests, you can use token authenticaion to enhance security of the connection between client and server.
Feilong use admin-token to authicate the safety of the connection instead of username&password.
In other words, admin-token is what you can think as a combination of traditional username&password.

On client side, users should use this admin-token to request for a temporary token first. Then users can use
this temporary token to send requests.

On server side, admninistrators are responsible for creating admin-token file. The admin-token will be stored
in this file. Users can get admin-token by contacting administrator.

Setup Server Side
-----------------

* Create admin-token file

  Administrators can use zvmsdk-gentoken tool to create admin-token file.

  Fox example, initialize one token file:

  .. code-block:: text

     # /usr/bin/zvmsdk-gentoken

  zvmsdk-gentoken use **/etc/zvmsdk/token.dat** as default path of token file. You can also specify your own token file path:

  .. code-block:: text

     # /usr/bin/zvmsdk-gentoken /new/path/of/token/file

  The commands above will initialize one token file and write a random admin-token into it.

  This tool can also help you update the content of token file:

  .. code-block:: text

     # /usr/bin/zvmsdk-gentoken -u

  If you don't assign a file path, zvmsdk-gentoken will update the file of default token path. You can update specified
  file by this way:

  .. code-block:: text

     # /usr/bin/zvmsdk-gentoken -u /new/path/of/token/file

  **NOTE:** please remember to change token file's owner to user **zvmsdk** after operating it.

* Update Configuration file

  After creating admin-token file, configuration should be updated to let the server know the path of token file.

  In configuration file, you can assign token file path by change the value of ``token_path`` which is in wsgi section.

  What's more, you should let server know we have changed the way of authentication by setting value of ``auth`` item
  in the wsgi section to ``token``, just like ``auth=token``.

  If you want to disable token authentication, just change ``auth`` to value ``none``.

Setup Client Side
-----------------

  On client side, you need to get the admin-token stored in the admin-token file. Just As what we have talked above,
  admin-token file is generated on server side. Users should contact the administrator for admin-token before sending
  requests. Then users can put the admin_token into the ``X-Admin-Token`` field in headers of request object for
  passing the authentication.

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

  You can see the temporary token is in the ``X-Auth-Token`` field.

  Then you can send normal RESTful requests using this temporary token to pass the authentication. 

  For example:

  .. code-block:: text

     # curl http://localhost:8080/ -H "Content-Type:application/json" -H 'X-Auth-Token:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MTI1NDQyODJ9.TVlcQb_QuUPJ37cRyzZqroR6kLZ-5zH2-tliIkhsQ1A'
     {"rs": 0, "overallRC": 0, "modID": null, "rc": 0, "output": {"min_version": "1.0", "version": "1.0", "max_version": "1.0"}, "errmsg": ""}
