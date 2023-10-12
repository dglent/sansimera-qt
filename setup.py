#!/usr/bin/env python3

import os
from distutils.command.build import build
from distutils.core import setup


class BuildQm(build):
    os.system('pyrcc5 -o sansimera_qt/qrc_resources.py sansimera_qt/resources.qrc')


setup(
    name='sansimera_qt',
    version='1.1.0',
    description='A system tray application for the namedays and the events of the day back in the history',
    author='Dimitrios Glentadakis',
    author_email='dglent@free.fr',
    url='https://github.com/dglent/sansimera-qt',
    license='GPLv3',
    packages=['sansimera_qt'],
    keywords=['eortologio', 'qt', 'trayicon', 'history', 'events', 'san simera'],
    data_files=[
        (
            '/usr/share/applications',
            [
                'share/sansimera-qt.desktop'
            ]
        ),
        (
            '/usr/share/icons',
            [
                'sansimera_qt/images/sansimera-qt.png'
            ]
        ),
        (
            '/usr/share/sansimera_qt/images',
            [
                'sansimera_qt/images/application-exit.png',
                'sansimera_qt/images/dialog-information.png',
                'sansimera_qt/images/go-next-view.png',
                'sansimera_qt/images/go-previous-view.png',
                'sansimera_qt/images/preferences-desktop-notification-bell.png',
                'sansimera_qt/images/sansimera-qt.png',
                'sansimera_qt/images/view-refresh.png',
                'sansimera_qt/images/preferences-system-windows.png',
            ]
        ),
        (
            '/usr/share/doc/sansimera-qt',
            [
                'README.md',
                'LICENSE.md'
            ]
        )
    ],
    scripts=["bin/sansimera-qt"],
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Other Audience',
        'Natural Language :: Greek',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
