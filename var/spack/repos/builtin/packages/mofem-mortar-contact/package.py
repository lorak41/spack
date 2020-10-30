# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack import *


class MofemSoftmech(CMakePackage):
    """mofem softmech library"""

    homepage = "http://mofem.eng.gla.ac.uk"
    git = "https://IgnatiosAthanasiadis@bitbucket.org/mofem/mortar_contact.git"

    maintainers = ['likask', 'IgnatiosAthanasiadis']

    version('develop', branch='develop')
    version('0.10.0', branch='Version0.10.0')

    variant('copy_user_modules', default=True,
        description='Copy user modules directory instead linking')

    extends('mofem-cephas')
    depends_on("mofem-users-modules", type=('build', 'link', 'run'))

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
            '-DEXTERNAL_MODULES_BUILD=YES',
            '-DUM_INSTALL_BREFIX=%s' % spec['mofem-users-modules'].prefix,
            '-DEXTERNAL_MODULE_SOURCE_DIRS=%s' % source,
            '-DSTAND_ALLONE_USERS_MODULES=%s' %
            ('YES' if '+copy_user_modules' in spec else 'NO')])

        # build tests
        options.append('-DMOFEM_UM_BUILD_TESTS={0}'.format(
            'ON' if self.run_tests else 'OFF'))

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
        install_tree(source, prefix.ext_users_modules.softmech)
