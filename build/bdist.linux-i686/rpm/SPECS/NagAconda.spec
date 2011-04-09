%define name NagAconda
%define version 0.1
%define unmangled_version 0.1
%define unmangled_version 0.1
%define release 1

Summary: NagAconda is a Python Nagios wrapper.
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Shaun Thomas <sthomas@leapfrogonline.com>
Url: http://www.leapfrogonline.com/

%description

:mod:`NagAconda` -- Python Nagios Integration
=============================================

Nagios has been around for quite some time, but producing output it can
consume is something of a black art. Only the plugin documentation actually
explains what all the extra semicolons or extended formatting even means.

This is especially onerous when performance consuming add-ons expect a
specific structure before operating properly. This package strives to
greatly simplify the process of actually generating Nagios output.

.. automodule:: NagAconda.Plugin



%prep
%setup -n %{name}-%{unmangled_version} -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
