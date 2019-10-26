# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class PyBackportsWeakref(PythonPackage):
    """Backports of new features in Python's weakref module"""

    homepage = "https://github.com/PiDelport/backports.weakref"
    url      = "https://pypi.org/packages/source/b/backports.weakref/backports.weakref-1.0.post1.tar.gz"

    version('1.0.post1', sha256='bc4170a29915f8b22c9e7c4939701859650f2eb84184aee80da329ac0b9825c2')

    depends_on('py-setuptools', type='build')
