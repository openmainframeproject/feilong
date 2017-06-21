%define name zhcp

Summary: System z hardware control point (zHCP)
Name: %{name}
Version: %(cat zhcp/Version)
Release: snap%(date +"%Y%m%d%H%M")
Source: zhcp-build.tar.gz
Vendor: IBM
License: IBM Copyright 2012, 2016 Eclipse Public License
Group: System/tools
BuildRoot: %{_tmppath}/zhcp
Prefix: /opt/zhcp

%description
The System z hardware control point (zHCP) is a set of APIs to interface with 
z/VM SMAPI. It is used by xCAT to manage virtual machines running Linux on 
System z.
%define builddate %(date)

%prep
tar -zxvf ../SOURCES/zhcp-build.tar.gz -C ../BUILD/ --strip 1

%build
make

%install
make install
make post
make clean

mkdir -p $RPM_BUILD_ROOT/usr/bin
ln -sfd %{prefix}/bin/smcli $RPM_BUILD_ROOT/usr/bin
chmod 644 $RPM_BUILD_ROOT/usr/bin/smcli
mkdir -p $RPM_BUILD_ROOT/usr/share/man/man1/
cp smcli.1.gz $RPM_BUILD_ROOT/usr/share/man/man1/
mkdir -p $RPM_BUILD_ROOT/var/opt/zhcp
cp config/tracing.conf $RPM_BUILD_ROOT/var/opt/zhcp
cp config/settings.conf $RPM_BUILD_ROOT/var/opt/zhcp
mkdir -p $RPM_BUILD_ROOT/etc/ld.so.conf.d
cp config/zhcp.conf $RPM_BUILD_ROOT/etc/ld.so.conf.d
chmod -R 755 zhcp/bin/*
chmod -R 755 zhcp/lib/*
cp -rf zhcp/bin/* $RPM_BUILD_ROOT/opt/zhcp/bin
cp zhcp/lib/* $RPM_BUILD_ROOT/opt/zhcp/lib
echo "zhcp version: "%{version} "Built on: "%{builddate} > $RPM_BUILD_ROOT/opt/zhcp/version

%post

# Create log file for zHCP
mkdir -p /var/log/zhcp
touch /var/log/zhcp/zhcp.log

# syslog located in different directories in Red Hat/SUSE
ZHCP_LOG_HEADER="# Logging for xCAT zHCP"
ZHCP_LOG="/var/log/zhcp/zhcp.log"
echo "Configuring syslog"

# SUSE Linux Enterprise Server
if [ -e "/etc/init.d/syslog" ]; then
    # Syslog is the standard for log messages
    grep ${ZHCP_LOG} /etc/syslog.conf > /dev/null || (echo -e "\n${ZHCP_LOG_HEADER}\nlocal5.*        ${ZHCP_LOG}" >> /etc/syslog.conf)
elif [ -e "/opt/ibm/cmo/version" ]; then
    grep ${ZHCP_LOG} /etc/rsyslog.conf > /dev/null || (echo -e "\n${ZHCP_LOG_HEADER}\nlocal5.*        ${ZHCP_LOG}" >> /etc/rsyslog.conf)
fi
if [ -e "/etc/syslog-ng/syslog-ng.conf" ]; then
    # Syslog-ng is the replacement for syslogd
    grep ${ZHCP_LOG} /etc/syslog-ng/syslog-ng.conf > /dev/null || (echo -e "\n${ZHCP_LOG_HEADER}\n\
filter f_xcat_zhcp  { facility(local5); };\n\
destination zhcplog { file(\"${ZHCP_LOG}\"); };\n\
log { source(src); filter(f_xcat_zhcp); destination(zhcplog); };" >> /etc/syslog-ng/syslog-ng.conf)
fi

# Red Hat Enterprise Linux
if [ -e "/etc/rc.d/init.d/rsyslog" ]; then
    grep ${ZHCP_LOG} /etc/rsyslog.conf > /dev/null || (echo -e "\n${ZHCP_LOG_HEADER}\nlocal5.*        ${ZHCP_LOG}" >> /etc/rsyslog.conf)
fi

# Restart syslog
if [ -e "/etc/rc.d/init.d/rsyslog" ]; then
    /etc/rc.d/init.d/rsyslog restart
elif [ -e "/opt/ibm/cmo/version" ]; then
    service rsyslog restart
else
    /etc/init.d/syslog restart
fi

/sbin/ldconfig

%preun
# Delete man page and smcli command
rm -rf /usr/share/man/man1/smcli.1.gz

%files
# Files provided by this package
%defattr(-,root,root)
/opt/zhcp/*
%config(noreplace) /usr/bin/smcli
%config(noreplace) /usr/share/man/man1/smcli.1.gz
%config(noreplace) /var/opt/zhcp/tracing.conf
%config(noreplace) /var/opt/zhcp/settings.conf
%config(noreplace) /etc/ld.so.conf.d/zhcp.conf
