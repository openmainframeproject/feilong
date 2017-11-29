%define name python-zvm-sdk

Summary: IBM z/VM cloud connector
Name: %{name}
Version: 0.3.0
Release: 1
Source: python-zvm-sdk.tar.gz
Vendor: IBM
License: ASL 2.0
Group: System/tools
BuildRoot: %{_tmppath}/python-zvm-sdk
Prefix: /opt/python-zvm-sdk

%description
The System z/VM cloud connector is a set of APIs to be used
by external
%define builddate %(date)

%prep
# if user zvmsdk not exist, add zvmsdk user
/usr/bin/getent passwd zvmsdk || /usr/sbin/useradd -r -d /var/lib/zvmsdk -m -U zvmsdk

tar -zxvf ../SOURCES/python-zvm-sdk.tar.gz -C ../BUILD/ --strip 1

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --record=INSTALLED_FILES

mkdir -p /var/lib/zvmsdk
chown -R zvmsdk:zvmsdk /var/lib/zvmsdk
chmod -R 755 /var/lib/zvmsdk

mkdir -p /var/log/zvmsdk
chown -R zvmsdk:zvmsdk /var/log/zvmsdk
chmod -R 755 /var/log/zvmsdk

mkdir -p /etc/zvmsdk
chown -R zvmsdk:zvmsdk /etc/zvmsdk
chmod -R 755 /etc/zvmsdk


%clean
rm -rf %{buildroot}
%files -f INSTALLED_FILES
%defattr(-,root,root)

%postun

