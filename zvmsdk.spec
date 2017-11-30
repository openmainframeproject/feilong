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
tar -zxvf ../SOURCES/python-zvm-sdk.tar.gz -C ../BUILD/ --strip 1

%build
python setup.py build

%install

mkdir -p %{buildroot}/etc/zvmsdk
mkdir -p %{buildroot}/var/log/zvmsdk
mkdir -p %{buildroot}/var/lib/zvmsdk

python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --record=INSTALLED_FILES --prefix=


%clean
rm -rf %{buildroot}
%files -f INSTALLED_FILES
%defattr(-,root,root)

%attr(644, zvmsdk, zvmsdk) /etc/zvmsdk
%attr(644, zvmsdk, zvmsdk) /var/log/zvmsdk
%attr(755, zvmsdk, zvmsdk) /var/lib/zvmsdk

%pre
# if user zvmsdk not exist, add zvmsdk user
/usr/bin/getent passwd zvmsdk || /usr/sbin/useradd -r -d /var/lib/zvmsdk -m -U zvmsdk

%postun
/usr/sbin/userdel zvmsdk

rm -fr /var/lib/zvmsdk
rm -fr /var/log/zvmsdk
rm -fr /etc/zvmsdk
rm -fr /etc/zvmsdk

