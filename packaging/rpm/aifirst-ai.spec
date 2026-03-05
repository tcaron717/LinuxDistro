Name:           aifirst-ai
Version:        0.1.0
Release:        1%{?dist}
Summary:        AI CLI tool for AI-first Fedora spin

License:        MIT
URL:            https://example.invalid/aifirst-ai
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

Requires:       python3 >= 3.9

%description
aifirst-ai is a lightweight CLI utility that provides Linux-focused AI interactions
for an AI-first Fedora spin, with provider support for local and API-backed models.

%prep
%autosetup -n %{name}-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
mkdir -p %{buildroot}/etc/aifirst
install -m 0644 configs/aifirst-ai.json %{buildroot}/etc/aifirst/aifirst-ai.json

%files
%license LICENSE
%doc README.md
/etc/aifirst/aifirst-ai.json
%{_bindir}/aifirst-ai
%{python3_sitelib}/aifirst_ai/
%{python3_sitelib}/aifirst_ai-*.dist-info/

%changelog
* Thu Mar 05 2026 AI First Fedora Team <maintainer@example.invalid> - 0.1.0-1
- Initial RPM package
