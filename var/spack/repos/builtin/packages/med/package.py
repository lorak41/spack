# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack import *


class Med(CMakePackage):
    """The MED file format is a specialization of the HDF5 standard."""

    homepage = "https://docs.salome-platform.org/latest/dev/MEDCoupling/user/html/index.html"
    
    maintainers = ['likask', 'hoangnguyence']

    version('3.2.0', 'eb61df92f0624feb6328f517cd756a23', url='http://files.salome-platform.org/Salome/other/med-3.2.0.tar.gz')
    version('3.3.1', '4981a02fa50b1a487a022804512631ff', url='http://files.salome-platform.org/Salome/other/med-3.3.1.tar.gz')
    version('4.0.0', 'ef903d0dc165fc72818ab264ebb6e8ba', url='http://files.salome-platform.org/Salome/other/med-4.0.0.tar.gz')

    variant('api23', default=True, description='Enable API2.3')

    depends_on('mpi')
    depends_on('hdf5@:1.8.19+mpi', when='@:3.99.99')
    depends_on('hdf5@:1.10.5+mpi', when='@4.0.0:') 

    # FIXME This is minimal installation.

    def cmake_args(self):
        spec = self.spec

        options = []

        if '+api23' in spec:
            options.extend([
                '-DCMAKE_CXX_FLAGS:STRING=-DMED_API_23=1',
                '-DCMAKE_C_FLAGS:STRING=-DMED_API_23=1',
                '-DMED_API_23=1'])

        options.extend([
            '-DMEDFILE_USE_MPI=YES'
            '-DMEDFILE_BUILD_TESTS={0}'.format(
                'ON' if self.run_tests else 'OFF'),
            '-DMEDFILE_BUILD_PYTHON=OFF',
            '-DMEDFILE_INSTALL_DOC=OFF',
            '-DMEDFILE_BUILD_SHARED_LIBS=OFF',
            '-DMEDFILE_BUILD_STATIC_LIBS=ON',
            '-DCMAKE_Fortran_COMPILER='])

        options.extend([
            '-DHDF5_ROOT_DIR=%s' % spec['hdf5'].prefix,
            '-DMPI_ROOT_DIR=%s' % spec['mpi'].prefix])

        return options
