%define aname sansimera_qt

Name:           sansimera-qt
Version:        1.2.2
Release:        %mkrel 1
Group:          Network/News
Summary:        Namedays and events of the day back in the history
License:        GPLv3
URL:            https://github.com/dglent/sansimera-qt
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python3-qt6-devel
BuildRequires:  python3
BuildRequires:  python3-setuptools
BuildRequires:  imagemagick

Requires:       python3-qt6
Requires:       python3-qt6-webengine
Requires:       python3-qt6-webenginecore
Requires:       python3-qt6-webenginewidgets
Requires:       python3-pillow
Requires:       python3-beautifulsoup4
Requires:       python3-requests
Requires:       python3-lxml


%description
A Qt system tray application which shows the events back in the history
from the website www.sansimera.gr and the namedays from www.eortologio.gr

%prep
%setup -q

%build
%py_build

%install
%py_install
%__mkdir -p %{buildroot}%{_iconsdir}/hicolor/{16x16,32x32}/apps
convert -scale 16x16 sansimera_qt/images/sansimera-qt.png %{buildroot}%{_iconsdir}/hicolor/16x16/apps/sansimera-qt.png
convert -scale 32x32 sansimera_qt/images/sansimera-qt.png %{buildroot}%{_iconsdir}/hicolor/32x32/apps/sansimera-qt.png


%files
%license %{_datadir}/doc/%{name}/LICENSE.md
%doc README.md
%{_datadir}/%{aname}/images/
%{_bindir}/%{name}
%{_iconsdir}/%{name}.png
%{python3_sitelib}/%{aname}-%{version}-py*.egg-info
%{python3_sitelib}/%{aname}/
%{_datadir}/applications/%{name}.desktop
%{_iconsdir}/hicolor/*/apps/sansimera-qt.png
