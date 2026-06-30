#!/usr/bin/env python3

import os
import shutil
import subprocess

from setuptools import Command, setup
from setuptools.command.build_py import build_py


class BuildQrc(Command):
    description = "build Qt resource module"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        source = "sansimera_qt/resources.qrc"
        target = "sansimera_qt/qrc_resources.py"
        pyrcc5 = shutil.which("pyrcc5")

        if pyrcc5 is None:
            if os.path.exists(target):
                self.announce(f"pyrcc5 not found, using existing {target}", level=2)
                return
            raise RuntimeError("pyrcc5 is required to build qrc_resources.py")

        self.announce(f"building {target} from {source}", level=2)
        subprocess.check_call([pyrcc5, "-o", target, source])


class BuildPy(build_py):
    def run(self):
        self.run_command("build_qrc")
        super().run()


setup(
    name="sansimera_qt",
    version="1.2.2",
    description="A system tray application for the namedays and the events of the day back in the history",
    author="Dimitrios Glentadakis",
    author_email="dglent@free.fr",
    url="https://github.com/dglent/sansimera-qt",
    license="GPLv3",
    packages=["sansimera_qt"],
    package_data={
        "sansimera_qt": ["images/*.png"],
    },
    keywords=["eortologio", "qt", "trayicon", "history", "events", "san simera"],
    install_requires=[
        "PyQt5",
        "PyQtWebEngine",
        "Pillow",
        "beautifulsoup4",
        "requests",
        "lxml",
    ],
    python_requires=">=3.6",
    cmdclass={
        "build_qrc": BuildQrc,
        "build_py": BuildPy,
    },
    data_files=[
        ("/usr/share/applications", ["share/sansimera-qt.desktop"]),
        ("/usr/share/icons", ["sansimera_qt/images/sansimera-qt.png"]),
        (
            "/usr/share/sansimera_qt/images",
            [
                "sansimera_qt/images/application-exit.png",
                "sansimera_qt/images/dialog-information.png",
                "sansimera_qt/images/go-next-view.png",
                "sansimera_qt/images/go-previous-view.png",
                "sansimera_qt/images/preferences-desktop-notification-bell.png",
                "sansimera_qt/images/sansimera-qt.png",
                "sansimera_qt/images/view-refresh.png",
                "sansimera_qt/images/preferences-system-windows.png",
            ],
        ),
        ("/usr/share/doc/sansimera-qt", ["README.md", "LICENSE.md"]),
    ],
    scripts=["bin/sansimera-qt"],
    zip_safe=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Other Audience",
        "Natural Language :: Greek",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
)
