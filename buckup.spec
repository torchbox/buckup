%global srcname buckup
Name:           %{srcname}
Version:        0.1a7
Summary:        Command line tool to create S3 buckets easily.
License:        BSD
URL:            https://github.com/torchbox/buckup
Release:        1%{?dist}
Source0:        https://github.com/torchbox/buckup/archive/v%{version}.tar.gz
BuildArch:      noarch
Requires:       python3-boto3
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-wheel

%description
Command line tool to create S3 buckets easily.

%prep
%autosetup -p 1
rm -rf buckup.egg-info

%build
%py3_build

%install
%py3_install

%files
%license LICENSE
%doc README.rst
%{_bindir}/%{srcname}
%{python3_sitelib}/%{srcname}
%{python3_sitelib}/%{srcname}-%{version}-*.egg-info
