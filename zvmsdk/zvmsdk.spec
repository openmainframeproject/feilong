%define name python-zvm-sdk

Summary: IBM z/VM cloud connector
Name: %{name}
Version: 0.3.0
Release: snap%(date +"%Y%m%d%H%M")
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
python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --record=INSTALLED_FILES

%clean
rm -rf %{buildroot}
%files -f INSTALLED_FILES
%defattr(-,root,root)

