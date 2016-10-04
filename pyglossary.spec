%global __python /usr/bin/python3
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "import sys; from distutils.sysconfig import get_python_lib; sys.stdout.write(get_python_lib())")}

Name:           pyglossary
Version:        master
Release:        1%{?dist}
Summary:        Working on glossaries (dictionary databases)

Group:          Applications/Productivity
License:        GPLv3
URL:            https://github.com/ilius/pyglossary
Source0:        pyglossary-%{version}.tar.gz

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

%description
Working on glossaries (dictionary databases) using python. Including editing
glossaries and converting theme between many formats such as: Tabfile StarDict
format xFarDic format "Babylon Builder" source format Omnidic format and etc.

%prep
%setup -q

%install
python3 setup.py install --root=%{buildroot} --prefix=%{_prefix}

desktop-file-install --vendor fedora                            \
        --dir %{buildroot}%{_datadir}/applications              \
        --delete-original										\
        %{buildroot}%{_datadir}/applications/pyglossary.desktop

%clean
rm -rf %{buildroot}

%files
%{_bindir}/pyglossary
%{_datadir}/applications/fedora-pyglossary.desktop
%{_datadir}/pixmaps/pyglossary.png
%{_datadir}/pyglossary/
%{_datadir}/doc/pyglossary/
%{python_sitelib}/pyglossary/*
