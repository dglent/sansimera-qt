Name:           sansimera-qt
Version:        0.4.0
Release:        %mkrel 1
Group:          Network/News
Summary:        Events from the site www.sansimera.gr
License:        GPLv3
URL:            https://github.com/dglent/sansimera-qt
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python-qt5-devel
BuildRequires:  python3
BuildRequires:  imagemagick

Requires:       python3-qt5
Requires:       python3-sip
Requires:       python3-pillow
Requires:       python3-beautifulsoup4
Requires:       python3-urllib3
Requires:       python3-requests
Requires:       wget


%description
A Qt system tray application which shows the events back in the history
from the website www.sansimera.gr

%prep
%setup -q

%build
pyrcc5 -o qrc_resources.py resources.qrc

%install
mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/sansimera-qt << EOF
#!/usr/bin/bash

cd %{_datadir}/sansimera-qt
python3 sansimera.py
EOF
chmod +x %{buildroot}%{_bindir}/sansimera-qt

#-------------------------------------------
mkdir -p %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/%{name}.desktop << EOF
[Desktop Entry]
Name=Sansimera-qt
Comment=Σαν σήμερα
Exec=sansimera-qt
Icon=sansimera
Path=/usr/bin/sansimera
Type=Application
StartupNotify=true
Categories=Network;Qt;
EOF
#-------------------------------------------
for file in `ls images`; do
    %__install -D images/$file %{buildroot}%{_datadir}/%{name}/images/$file
done
for file in *.py; do
    %__install -D $file %{buildroot}%{_datadir}/%{name}/$file
done
#--------------------------------------------
install -D -m644 images/sansimera.png %{buildroot}%{_iconsdir}/sansimera.png
mkdir -p %{buildroot}%{_iconsdir}/hicolor/{16x16,32x32}/apps
convert -scale 16x16 images/sansimera.png %{buildroot}%{_iconsdir}/hicolor/16x16/apps/sansimera.png
convert -scale 32x32 images/sansimera.png %{buildroot}%{_iconsdir}/hicolor/32x32/apps/sansimera.png

%files
%dir %{_datadir}/%{name}
%dir %{_datadir}/%{name}/images
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/%{name}/images/*
%{_iconsdir}/*
%{_datadir}/%{name}/*
