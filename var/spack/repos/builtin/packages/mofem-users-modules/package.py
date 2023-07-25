# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack import *


class MofemUsersModules(CMakePackage):
    """MofemUsersModules creates installation environment for user-provided
    modules and extends of mofem-cephas package. For more information how to
    work with Spack and MoFEM see
    http://mofem.eng.gla.ac.uk/mofem/html/install_spack.html"""

    homepage = "http://mofem.eng.gla.ac.uk"
    git = "https://likask@bitbucket.org/mofem/users-modules-cephas.git"

    version('master', branch='master')
    version('develop', branch='develop')
    version('lukasz', branch='lukasz/develop')
    version('karol', branch='karol/develop')
    version('0.14.0', branch='Version0.14.0')
    version('0.13.2', branch='Version0.13.2')
    version('0.13.0', branch='Version0.13.0')
    version('0.12.3', branch='Version0.12.3')
    version('0.12.2', branch='Version0.12.2')
    version('0.12.1', branch='Version0.12.1')
    version('0.12.0', branch='Version0.12.0')
    version('0.11.1', branch='Version0.11.1')
    version('0.11.0', branch='Version0.11.0')
    version('0.10.0', branch='Version0.10.0')
    version('0.9.2', branch='Version0.9.2')
    version('0.9.1', tag='v0.9.1-release')
    version('0.9.0', commit='173cefb39de9699935568d5d33db4b51a8813ef6')
    version('0.8.23', commit='12d9df7fd31e95b90d245e1eee055769424e04a9')
    version('0.8.21', commit='21825107ca949bd7ec5ea7bbd523bd2fd890be7f')
    version('0.8.20', commit='1b43c08113a8f4c77cd25ee2f4071660a1a79695')
    version('0.8.19', commit='0e79a7be9369ec2cd63301f5ed939a1b5d5c1fdc')
    version('0.8.18', commit='860be021ca6891477166e14c56cfeeb087e967ff')
    version('0.8.17', commit='60b2341f1635f595d571096dd8c70a7cf7538aeb')
    version('0.8.16', commit='f6af51ad7db5b5dbc9d9acc6e753277a857c9f24')
    version('0.8.15', commit='4843b2d92ec21ad100a8d637698f56b3a2e14af3')
    version('0.8.14', commit='cfaa32133c574a31beaeb36202d033280521ddff')
    version('0.8.12', commit='7b2ce5595a95d1b919f50103513c44bb2bc9e6d2')
    version('0.8.11', commit='329b06d758137f1ec830f157d383b5ea415963de')
    version('0.8.10', commit='ca03a8222b20f9c8ff93a2d6f4c3babbcfde2058')
    version('0.8.8', commit='eb40f3c218badcd528ab08ee952835fb2ff07fd3')
    version('0.8.7', commit='a83b236f26f258f4d6bafc379ddcb9503088df56')

    maintainers = ['likask']

    variant('install_id', default="0",
        description='Internal install ID used by Jenkins')
    variant('copy_user_modules', default=True,
        description='Copy user modules directory instead linking')
    variant('docker', default=False, description='Build in docker volume')
    variant('mgis', default=False, description='Build with mgis package (MFront)')

    extends('mofem-cephas')
    depends_on('mofem-cephas@0.14.0', when='@0.14.0:0.14.99')
    depends_on('mofem-cephas@0.13.2', when='@0.13.2:0.13.99')
    depends_on('mofem-cephas@0.13.0', when='@0.13.0:0.13.1')
    depends_on('mofem-cephas@0.12.1', when='@0.12.2:0.12.3')
    depends_on('mofem-cephas@0.12.0', when='@0.12.1')
    depends_on('mofem-cephas@0.12.0', when='@0.12.0')
    depends_on('mofem-cephas@0.11.1', when='@0.11.1')
    depends_on('mofem-cephas@0.11.0', when='@0.11.0')
    depends_on('mofem-cephas@0.10.0', when='@0.10.0')
    depends_on('mofem-cephas@0.9.2', when='@0.9.2')
    depends_on('mofem-cephas@0.9.1', when='@0.9.1')
    depends_on('mofem-cephas@0.9.0', when='@0.9.0')
    depends_on('mofem-cephas@0.8.23:0.8.99', when='@0.8.23')
    depends_on('mofem-cephas@0.8.21:0.8.22', when='@0.8.21')
    depends_on('mofem-cephas@0.8.20', when='@0.8.20')
    depends_on('mofem-cephas@0.8.19', when='@0.8.19')
    depends_on('mofem-cephas@0.8.18', when='@0.8.18')   
    depends_on('mofem-cephas@0.8.17', when='@0.8.17')
    depends_on('mofem-cephas@0.8.16', when='@0.8.16')
    depends_on('mofem-cephas@0.8.15', when='@0.8.15')
    depends_on('mofem-cephas@0.8.14', when='@0.8.14')
    depends_on('mofem-cephas@0.8.12:0.8.13', when='@0.8.12')
    depends_on('mofem-cephas@0.8.11', when='@0.8.11')
    depends_on('mofem-cephas@0.8.10', when='@0.8.10')
    depends_on('mofem-cephas@0.8.8:0.8.9', when='@0.8.8')
    depends_on('mofem-cephas@0.8.7', when='@0.8.7')
    depends_on('mofem-cephas@lukasz', when='@lukasz')
    depends_on('mofem-cephas@develop', when='@develop')
    depends_on('mofem-cephas@master', when='@master')
    depends_on('mofem-cephas@develop', when='@karol')
    
    # MGIS
    depends_on('mgis~python~fortran', when='+mgis')
    depends_on('tfel~python~python_bindings~fortran', when='+mgis')

    variant('shared', default=False,
            description='Builds a shared version of the library')
    
    # Build variants
    variant('basic_fe', default=True, description='Build basic finite elements') 
    variant('basic_tutorials', default=True, description='Build basic tutorials') 
    
    variant('build_tut_fun0', default=True, description='Build tutorial')
    variant('build_tut_fun1', default=True, description='Build tutorial')
    variant('build_tut_fun2', default=True, description='Build tutorial')
    variant('build_tut_msh1', default=True, description='Build tutorial')
    variant('build_tut_msh2', default=True, description='Build tutorial')
    variant('build_tut_scl0', default=True, description='Build tutorial')
    variant('build_tut_scl1', default=True, description='Build tutorial')
    variant('build_tut_scl2', default=True, description='Build tutorial')
    variant('build_tut_scl3', default=True, description='Build tutorial')
    variant('build_tut_scl4', default=True, description='Build tutorial')
    variant('build_tut_scl5', default=True, description='Build tutorial')
    variant('build_tut_scl6', default=True, description='Build tutorial')
    variant('build_tut_scl7', default=True, description='Build tutorial')
    variant('build_tut_scl8', default=True, description='Build tutorial')
    variant('build_tut_scl9', default=True, description='Build tutorial')
    variant('build_tut_scl10', default=True, description='Build tutorial')
    variant('build_tut_scl11', default=True, description='Build tutorial')
    variant('build_tut_clx0', default=True, description='Build tutorial')
    variant('build_tut_vec0', default=True, description='Build tutorial')
    variant('build_tut_vec1', default=True, description='Build tutorial')
    variant('build_tut_vec2', default=True, description='Build tutorial')
    variant('build_tut_vec3', default=True, description='Build tutorial')
    variant('build_tut_vec4', default=True, description='Build tutorial')
    variant('build_tut_vec5', default=True, description='Build tutorial')
    variant('build_tut_vec6', default=True, description='Build tutorial')
    variant('build_tut_mix0', default=True, description='Build tutorial')
    variant('build_tut_mix1', default=True, description='Build tutorial')
    variant('build_tut_max0', default=True, description='Build tutorial')
    variant('build_tut_max1', default=True, description='Build tutorial')
    variant('build_tut_adv0', default=True, description='Build tutorial')
    variant('build_tut_adv1', default=True, description='Build tutorial')
    variant('build_tut_adv2', default=True, description='Build tutorial')
    variant('build_tut_cor0to1', default=True, description='Build tutorial')
    variant('build_tut_cor2to5', default=True, description='Build tutorial')
    variant('build_tut_cor6', default=True, description='Build tutorial')
    variant('build_tut_cor7', default=True, description='Build tutorial')
    variant('build_tut_cor8', default=True, description='Build tutorial')
    variant('build_tut_cor9', default=True, description='Build tutorial')
    variant('build_tut_cor10', default=True, description='Build tutorial')

    def setup_build_environment(self, env):
        env.set('CTEST_OUTPUT_ON_FAILURE', '1')

    @property
    def build_directory(self):
        spec = self.spec
        build_type = spec.variants['build_type'].value
        build_dir = 'um-build-%s-%s' % (build_type,spec.dag_hash(7))
        if '+docker' in spec:
          return join_path('/mofem_install',build_dir)
        else:
          return join_path(self.stage.path, build_dir)

    def cmake_args(self):
        spec = self.spec
        from_variant = self.define_from_variant

        options = []

        # obligatory options
        options.extend([
            '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
            '-DMPI_RUN_FLAGS=--allow-run-as-root',
            '-DWITH_SPACK=YES'])

        options.append(self.define(
            'MOFEM_DIR', spec['mofem-cephas'].prefix.users_module))
        options.append(self.define_from_variant(
            'STAND_ALLONE_USERS_MODULES', 'copy_user_modules'))
        options.append(
            self.define_from_variant('BUILD_SHARED_LIBS', 'shared'))
        
        options.append(
            from_variant('BUILD_BASIC_FINITE_ELEMENTS', 'basic_fe'))
        options.append(
            from_variant('BUILD_TUTORIALS', 'basic_tutorials'))
        
        if '+mgis' in spec:
            options.append('-DMGIS_DIR:PATH=%s' % spec['mgis'].prefix)
            options.append('-DTFEL_DIR:PATH=%s' % spec['tfel'].prefix)

        for name, v in spec.variants.items():
            if (name.startswith('build_tut_')):
                if '+basic_tutorials' in spec:
                    options.append(
                        from_variant(name.upper(), name))
                else:
                    options.append(
                        from_variant(name.upper(), 'basic_tutorials'))
                

        return options

    # This function is not needed to run code installed by extension, nor in
    # the install process. However, the source code of users modules is
    # necessary to compile other sub-modules. Also, for users like to have
    # access to source code to play, change and make it. Having source code at
    # hand one can compile in own build directory it in package view when the
    # extension is activated.
    @run_after('install')
    def copy_source_code(self):
        source = self.stage.source_path
        prefix = self.prefix
        install_tree(source, prefix.users_modules)

    def check(self):
        """Searches the CMake-generated Makefile for the target ``test``
        and runs it if found.
        """
        with working_dir(self.build_directory):
            ctest(parallel=False)