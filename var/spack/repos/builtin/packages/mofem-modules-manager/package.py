# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack import *


class MofemModulesManager(CMakePackage):
    """mofem modules manager module"""

    homepage = "http://mofem.eng.gla.ac.uk"
    git = "https://karol41@bitbucket.org/mofem/mofem_modules-manager.git"

    maintainers = ['karol41', 'likask']

    version('develop', branch='develop')
    version('master', branch='master')
    version('0.13.0', branch='Version0.13.0')

    extends('mofem-cephas')

    variant('install_id', values=int, default=118, description='Internal install Id used by Jenkins')
    variant('copy_user_modules', default=True,
        description='Copy user modules directory instead linking')
    variant('mofem-mortar-contact', default=False, description='Build with MoFEM mortar contact module')
    variant('mofem-multifield-plasticity', default=False, description='Build with multifield plasticity')
    variant('mofem-mfront-interface', default=False, description='Build with mgis package (MFront)')
    variant('mofem-hdiv-contact', default=False, description='Build with hdiv contact module')


    depends_on("mofem-users-modules", type=('build', 'link', 'run'))
    depends_on('mofem-users-modules@develop', when='@develop')

    # the modules
    depends_on('mofem-mortar-contact', when='+mofem-mortar-contact')
    depends_on('mofem-multifield-plasticity', when='+mofem-multifield-plasticity')
    depends_on('mofem-mfront-interface', when='+mofem-mfront-interface')
    depends_on('mofem-hdiv-contact', when='+mofem-hdiv-contact')

   # MGIS
    depends_on('mgis~python~fortran', when='+mofem-mfront-interface')
    depends_on('tfel~python~python_bindings~fortran', when='+mofem-mfront-interface')

    # depends_on('mgis@1.1~python~fortran', when='+mgis @1.1')
    # The CMakeLists.txt installed with mofem - cephas package set cmake
    # environment to install extension from extension repository.It searches
    # for modules in user provides paths, for example in Spack source path.Also
    # it finds all cmake exported targets installed in lib directory, which are
    # built with dependent extensions, f.e.mofem - users - modules or others if
    # needed.
    @property
    def root_cmakelists_dir(self):
        """The relative path to the directory containing CMakeLists.txt

        This path is relative to the root of the extracted tarball,
        not to the ``build_directory``. Defaults to the current directory.

        :return: directory containing CMakeLists.txt
        """
        spec = self.spec
        return spec['mofem-users-modules'].prefix.users_modules

    def cmake_args(self):
        spec = self.spec
        source = self.stage.source_path

        options = []

        # obligatory options
        options.extend([
            '-DWITH_SPACK=YES',
            '-DMPI_RUN_FLAGS=--allow-run-as-root',
            '-DEXTERNAL_MODULES_BUILD=YES',
            '-DUM_INSTALL_PREFIX=%s' % spec['mofem-users-modules'].prefix,
            '-DUM_INSTALL_BREFIX=%s' % spec['mofem-users-modules'].prefix,
            '-DEXTERNAL_MODULE_SOURCE_DIRS=%s' % source,
            '-DSTAND_ALLONE_USERS_MODULES=%s' %
            ('YES' if '+copy_user_modules' in spec else 'NO')])

        # build tests
        options.append('-DMOFEM_UM_BUILD_TESTS={0}'.format(
            'ON' if self.run_tests else 'OFF'))
            
        options.append('-DMODULES_MANAGER:PATH=%s' % spec['mofem-modules-manager'].prefix)

        return options

    # This function is not needed to run code installed by extension, nor in
    # the install process. However, for users like to have access to source
    # code to play, change and make it. Having source code at hand one can
    # compile in own build directory it in package view when the extension is
    # activated.
    @run_after('install')
    def copy_source_code(self):
        source = self.stage.source_path
        prefix = self.prefix
        install_tree(source, prefix.ext_users_modules.modules_manager)

    def check(self):
        """Searches the CMake-generated Makefile for the target ``test``
        and runs it if found.
        """
        with working_dir(self.build_directory):
            ctest(parallel=False)