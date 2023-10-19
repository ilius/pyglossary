%global __python /usr/bin/python3
%{!?python_sitelib: %global python_sitelib %(%{__python} -c 'import sys, sysconfig; sys.stdout.write(sysconfig.get_paths()["purelib"])')}

Name:           pyglossary
Version:        master
Release:        1%{?dist}
Summary:        Working on glossaries (dictionary files)

Group:          Applications/Productivity
License:        GPLv3
URL:            https://github.com/ilius/pyglossary
Source0:        pyglossary-%{version}.tar.gz

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

%description
A tool for converting dictionary files aka glossaries.

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
