# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
from six import StringIO

import pytest

import llnl.util.filesystem as fs

import spack.hash_types as ht
import spack.modules
import spack.environment as ev

from spack.cmd.env import _env_create
from spack.spec import Spec
from spack.main import SpackCommand

from spack.spec_list import SpecListError
from spack.test.conftest import MockPackage, MockPackageMultiRepo
import spack.util.spack_json as sjson


# everything here uses the mock_env_path
pytestmark = pytest.mark.usefixtures(
    'mutable_mock_env_path', 'config', 'mutable_mock_packages')

env        = SpackCommand('env')
install    = SpackCommand('install')
add        = SpackCommand('add')
remove     = SpackCommand('remove')
concretize = SpackCommand('concretize')
stage      = SpackCommand('stage')
uninstall  = SpackCommand('uninstall')
find       = SpackCommand('find')


def check_mpileaks_and_deps_in_view(viewdir):
    """Check that the expected install directories exist."""
    assert os.path.exists(str(viewdir.join('.spack', 'mpileaks')))
    assert os.path.exists(str(viewdir.join('.spack', 'libdwarf')))


def check_viewdir_removal(viewdir):
    """Check that the uninstall/removal worked."""
    assert (not os.path.exists(str(viewdir.join('.spack'))) or
            os.listdir(str(viewdir.join('.spack'))) == ['projections.yaml'])


@pytest.fixture()
def env_deactivate():
    yield
    spack.environment._active_environment = None
    os.environ.pop('SPACK_ENV', None)


def test_add():
    e = ev.create('test')
    e.add('mpileaks')
    assert Spec('mpileaks') in e.user_specs


def test_env_list(mutable_mock_env_path):
    env('create', 'foo')
    env('create', 'bar')
    env('create', 'baz')

    out = env('list')

    assert 'foo' in out
    assert 'bar' in out
    assert 'baz' in out

    # make sure `spack env list` skips invalid things in var/spack/env
    mutable_mock_env_path.join('.DS_Store').ensure(file=True)
    out = env('list')

    assert 'foo' in out
    assert 'bar' in out
    assert 'baz' in out
    assert '.DS_Store' not in out


def test_env_remove(capfd):
    env('create', 'foo')
    env('create', 'bar')

    out = env('list')
    assert 'foo' in out
    assert 'bar' in out

    foo = ev.read('foo')
    with foo:
        with pytest.raises(spack.main.SpackCommandError):
            with capfd.disabled():
                env('remove', '-y', 'foo')
        assert 'foo' in env('list')

    env('remove', '-y', 'foo')
    out = env('list')
    assert 'foo' not in out
    assert 'bar' in out

    env('remove', '-y', 'bar')
    out = env('list')
    assert 'foo' not in out
    assert 'bar' not in out


def test_concretize():
    e = ev.create('test')
    e.add('mpileaks')
    e.concretize()
    env_specs = e._get_environment_specs()
    assert any(x.name == 'mpileaks' for x in env_specs)


def test_env_install_all(install_mockery, mock_fetch):
    e = ev.create('test')
    e.add('cmake-client')
    e.concretize()
    e.install_all()
    env_specs = e._get_environment_specs()
    spec = next(x for x in env_specs if x.name == 'cmake-client')
    assert spec.package.installed


def test_env_install_single_spec(install_mockery, mock_fetch):
    env('create', 'test')
    install = SpackCommand('install')

    e = ev.read('test')
    with e:
        install('cmake-client')

    e = ev.read('test')
    assert e.user_specs[0].name == 'cmake-client'
    assert e.concretized_user_specs[0].name == 'cmake-client'
    assert e.specs_by_hash[e.concretized_order[0]].name == 'cmake-client'


def test_env_install_same_spec_twice(install_mockery, mock_fetch, capfd):
    env('create', 'test')

    e = ev.read('test')
    with capfd.disabled():
        with e:
            install('cmake-client')
            out = install('cmake-client')
            assert 'is already installed in' in out


def test_remove_after_concretize():
    e = ev.create('test')

    e.add('mpileaks')
    e.concretize()

    e.add('python')
    e.concretize()

    e.remove('mpileaks')
    assert Spec('mpileaks') not in e.user_specs
    env_specs = e._get_environment_specs()
    assert any(s.name == 'mpileaks' for s in env_specs)

    e.add('mpileaks')
    assert any(s.name == 'mpileaks' for s in e.user_specs)

    e.remove('mpileaks', force=True)
    assert Spec('mpileaks') not in e.user_specs
    env_specs = e._get_environment_specs()
    assert not any(s.name == 'mpileaks' for s in env_specs)


def test_remove_command():
    env('create', 'test')
    assert 'test' in env('list')

    with ev.read('test'):
        add('mpileaks')
        assert 'mpileaks' in find()
        assert 'mpileaks@' not in find()
        assert 'mpileaks@' not in find('--show-concretized')

    with ev.read('test'):
        remove('mpileaks')
        assert 'mpileaks' not in find()
        assert 'mpileaks@' not in find()
        assert 'mpileaks@' not in find('--show-concretized')

    with ev.read('test'):
        add('mpileaks')
        assert 'mpileaks' in find()
        assert 'mpileaks@' not in find()
        assert 'mpileaks@' not in find('--show-concretized')

    with ev.read('test'):
        concretize()
        assert 'mpileaks' in find()
        assert 'mpileaks@' not in find()
        assert 'mpileaks@' in find('--show-concretized')

    with ev.read('test'):
        remove('mpileaks')
        assert 'mpileaks' not in find()
        # removed but still in last concretized specs
        assert 'mpileaks@' in find('--show-concretized')

    with ev.read('test'):
        concretize()
        assert 'mpileaks' not in find()
        assert 'mpileaks@' not in find()
        # now the lockfile is regenerated and it's gone.
        assert 'mpileaks@' not in find('--show-concretized')


def test_environment_status(capfd, tmpdir):
    with capfd.disabled():
        with tmpdir.as_cwd():
            assert 'No active environment' in env('status')

            with ev.create('test'):
                assert 'In environment test' in env('status')

            with ev.Environment('local_dir'):
                assert os.path.join(os.getcwd(), 'local_dir') in env('status')

                e = ev.Environment('myproject')
                e.write()
                with tmpdir.join('myproject').as_cwd():
                    with e:
                        assert 'in current directory' in env('status')


def test_to_lockfile_dict():
    e = ev.create('test')
    e.add('mpileaks')
    e.concretize()
    context_dict = e._to_lockfile_dict()

    e_copy = ev.create('test_copy')

    e_copy._read_lockfile_dict(context_dict)
    assert e.specs_by_hash == e_copy.specs_by_hash


def test_env_repo():
    e = ev.create('test')
    e.add('mpileaks')
    e.write()

    with ev.read('test'):
        concretize()

    package = e.repo.get('mpileaks')
    assert package.name == 'mpileaks'
    assert package.namespace == 'builtin.mock'


def test_user_removed_spec():
    """Ensure a user can remove from any position in the spack.yaml file."""
    initial_yaml = StringIO("""\
env:
  specs:
  - mpileaks
  - hypre
  - libelf
""")

    before = ev.create('test', initial_yaml)
    before.concretize()
    before.write()

    # user modifies yaml externally to spack and removes hypre
    with open(before.manifest_path, 'w') as f:
        f.write("""\
env:
  specs:
  - mpileaks
  - libelf
""")

    after = ev.read('test')
    after.concretize()
    after.write()

    env_specs = after._get_environment_specs()
    read = ev.read('test')
    env_specs = read._get_environment_specs()

    assert not any(x.name == 'hypre' for x in env_specs)


def test_init_from_lockfile(tmpdir):
    """Test that an environment can be instantiated from a lockfile."""
    initial_yaml = StringIO("""\
env:
  specs:
  - mpileaks
  - hypre
  - libelf
""")
    e1 = ev.create('test', initial_yaml)
    e1.concretize()
    e1.write()

    e2 = ev.Environment(str(tmpdir), e1.lock_path)

    for s1, s2 in zip(e1.user_specs, e2.user_specs):
        assert s1 == s2

    for h1, h2 in zip(e1.concretized_order, e2.concretized_order):
        assert h1 == h2
        assert e1.specs_by_hash[h1] == e2.specs_by_hash[h2]

    for s1, s2 in zip(e1.concretized_user_specs, e2.concretized_user_specs):
        assert s1 == s2


def test_init_from_yaml(tmpdir):
    """Test that an environment can be instantiated from a lockfile."""
    initial_yaml = StringIO("""\
env:
  specs:
  - mpileaks
  - hypre
  - libelf
""")
    e1 = ev.create('test', initial_yaml)
    e1.concretize()
    e1.write()

    e2 = ev.Environment(str(tmpdir), e1.manifest_path)

    for s1, s2 in zip(e1.user_specs, e2.user_specs):
        assert s1 == s2

    assert not e2.concretized_order
    assert not e2.concretized_user_specs
    assert not e2.specs_by_hash


def test_init_with_file_and_remove(tmpdir):
    """Ensure a user can remove from any position in the spack.yaml file."""
    path = tmpdir.join('spack.yaml')

    with tmpdir.as_cwd():
        with open(str(path), 'w') as f:
            f.write("""\
env:
  specs:
  - mpileaks
""")

        env('create', 'test', 'spack.yaml')

    out = env('list')
    assert 'test' in out

    with ev.read('test'):
        assert 'mpileaks' in find()

    env('remove', '-y', 'test')

    out = env('list')
    assert 'test' not in out


def test_env_with_config():
    test_config = """\
env:
  specs:
  - mpileaks
  packages:
    mpileaks:
      version: [2.2]
"""
    spack.package_prefs.PackagePrefs.clear_caches()

    _env_create('test', StringIO(test_config))

    e = ev.read('test')
    ev.prepare_config_scope(e)
    e.concretize()

    assert any(x.satisfies('mpileaks@2.2')
               for x in e._get_environment_specs())


def test_env_with_included_config_file():
    test_config = """\
env:
  include:
  - ./included-config.yaml
  specs:
  - mpileaks
"""
    spack.package_prefs.PackagePrefs.clear_caches()

    _env_create('test', StringIO(test_config))
    e = ev.read('test')

    with open(os.path.join(e.path, 'included-config.yaml'), 'w') as f:
        f.write("""\
packages:
  mpileaks:
    version: [2.2]
""")

    ev.prepare_config_scope(e)
    e.concretize()

    assert any(x.satisfies('mpileaks@2.2')
               for x in e._get_environment_specs())


def test_env_with_included_config_scope():
    config_scope_path = os.path.join(ev.root('test'), 'config')
    test_config = """\
env:
  include:
  - %s
  specs:
  - mpileaks
""" % config_scope_path

    spack.package_prefs.PackagePrefs.clear_caches()
    _env_create('test', StringIO(test_config))

    e = ev.read('test')

    fs.mkdirp(config_scope_path)
    with open(os.path.join(config_scope_path, 'packages.yaml'), 'w') as f:
        f.write("""\
packages:
  mpileaks:
    version: [2.2]
""")

    ev.prepare_config_scope(e)
    e.concretize()

    assert any(x.satisfies('mpileaks@2.2')
               for x in e._get_environment_specs())


def test_env_config_precedence():
    test_config = """\
env:
  packages:
    libelf:
      version: [0.8.12]
  include:
  - ./included-config.yaml
  specs:
  - mpileaks
"""

    spack.package_prefs.PackagePrefs.clear_caches()

    _env_create('test', StringIO(test_config))
    e = ev.read('test')

    with open(os.path.join(e.path, 'included-config.yaml'), 'w') as f:
        f.write("""\
packages:
  mpileaks:
    version: [2.2]
  libelf:
    version: [0.8.11]
""")

    ev.prepare_config_scope(e)
    e.concretize()

    # ensure included scope took effect
    assert any(
        x.satisfies('mpileaks@2.2') for x in e._get_environment_specs())

    # ensure env file takes precedence
    assert any(
        x.satisfies('libelf@0.8.12') for x in e._get_environment_specs())


def test_included_config_precedence():
    test_config = """\
env:
  include:
  - ./high-config.yaml  # this one should take precedence
  - ./low-config.yaml
  specs:
  - mpileaks
"""
    spack.package_prefs.PackagePrefs.clear_caches()

    _env_create('test', StringIO(test_config))
    e = ev.read('test')

    with open(os.path.join(e.path, 'high-config.yaml'), 'w') as f:
        f.write("""\
packages:
  libelf:
    version: [0.8.10]  # this should override libelf version below
""")

    with open(os.path.join(e.path, 'low-config.yaml'), 'w') as f:
        f.write("""\
packages:
  mpileaks:
    version: [2.2]
  libelf:
    version: [0.8.12]
""")

    ev.prepare_config_scope(e)
    e.concretize()

    assert any(
        x.satisfies('mpileaks@2.2') for x in e._get_environment_specs())

    assert any(
        [x.satisfies('libelf@0.8.10') for x in e._get_environment_specs()])


def test_bad_env_yaml_format(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  spacks:
    - mpileaks
""")

    with tmpdir.as_cwd():
        with pytest.raises(spack.config.ConfigFormatError) as e:
            env('create', 'test', './spack.yaml')
        assert './spack.yaml:2' in str(e)
        assert "'spacks' was unexpected" in str(e)


def test_env_loads(install_mockery, mock_fetch):
    env('create', 'test')

    with ev.read('test'):
        add('mpileaks')
        concretize()
        install('--fake')

    with ev.read('test'):
        env('loads', 'test')

    e = ev.read('test')

    loads_file = os.path.join(e.path, 'loads')
    assert os.path.exists(loads_file)

    with open(loads_file) as f:
        contents = f.read()
        assert 'module load mpileaks' in contents


@pytest.mark.disable_clean_stage_check
def test_stage(mock_stage, mock_fetch, install_mockery):
    env('create', 'test')
    with ev.read('test'):
        add('mpileaks')
        add('zmpi')
        concretize()
        stage()

    root = str(mock_stage)

    def check_stage(spec):
        spec = Spec(spec).concretized()
        for dep in spec.traverse():
            stage_name = "%s-%s-%s" % (dep.name, dep.version, dep.dag_hash())
            assert os.path.isdir(os.path.join(root, stage_name))

    check_stage('mpileaks')
    check_stage('zmpi')


def test_env_commands_die_with_no_env_arg():
    # these fail in argparse when given no arg
    with pytest.raises(SystemExit):
        env('create')
    with pytest.raises(SystemExit):
        env('remove')

    # these have an optional env arg and raise errors via tty.die
    with pytest.raises(spack.main.SpackCommandError):
        env('loads')

    # This should NOT raise an error with no environment
    # it just tells the user there isn't an environment
    env('status')


def test_env_blocks_uninstall(mock_stage, mock_fetch, install_mockery):
    env('create', 'test')
    with ev.read('test'):
        add('mpileaks')
        install('--fake')

    out = uninstall('mpileaks', fail_on_error=False)
    assert uninstall.returncode == 1
    assert 'used by the following environments' in out


def test_uninstall_removes_from_env(mock_stage, mock_fetch, install_mockery):
    env('create', 'test')
    with ev.read('test'):
        add('mpileaks')
        add('libelf')
        install('--fake')

    test = ev.read('test')
    assert any(s.name == 'mpileaks' for s in test.specs_by_hash.values())
    assert any(s.name == 'libelf' for s in test.specs_by_hash.values())

    with ev.read('test'):
        uninstall('-ya')

    test = ev.read('test')
    assert not test.specs_by_hash
    assert not test.concretized_order
    assert not test.user_specs


def create_v1_lockfile_dict(roots, all_specs):
    test_lockfile_dict = {
        "_meta": {
            "lockfile-version": 1,
            "file-type": "spack-lockfile"
        },
        "roots": list(
            {
                "hash": s.dag_hash(),
                "spec": s.name
            } for s in roots
        ),
        # Version one lockfiles use the dag hash without build deps as keys,
        # but they write out the full node dict (including build deps)
        "concrete_specs": dict(
            (s.dag_hash(), s.to_node_dict(hash=ht.build_hash))
            for s in all_specs
        )
    }
    return test_lockfile_dict


@pytest.mark.usefixtures('config')
def test_read_old_lock_and_write_new(tmpdir):
    build_only = ('build',)

    y = MockPackage('y', [], [])
    x = MockPackage('x', [y], [build_only])

    mock_repo = MockPackageMultiRepo([x, y])
    with spack.repo.swap(mock_repo):
        x = Spec('x')
        x.concretize()

        y = x['y']

        test_lockfile_dict = create_v1_lockfile_dict([x], [x, y])

        test_lockfile_path = str(tmpdir.join('test.lock'))
        with open(test_lockfile_path, 'w') as f:
            sjson.dump(test_lockfile_dict, stream=f)

        _env_create('test', test_lockfile_path, with_view=False)

        e = ev.read('test')
        hashes = set(e._to_lockfile_dict()['concrete_specs'])
        # When the lockfile is rewritten, it should adopt the new hash scheme
        # which accounts for all dependencies, including build dependencies
        assert hashes == set([
            x.build_hash(),
            y.build_hash()])


@pytest.mark.usefixtures('config')
def test_read_old_lock_creates_backup(tmpdir):
    """When reading a version-1 lockfile, make sure that a backup of that file
    is created.
    """
    y = MockPackage('y', [], [])

    mock_repo = MockPackageMultiRepo([y])
    with spack.repo.swap(mock_repo):
        y = Spec('y')
        y.concretize()

        test_lockfile_dict = create_v1_lockfile_dict([y], [y])

        env_root = tmpdir.mkdir('test-root')
        test_lockfile_path = str(env_root.join(ev.lockfile_name))
        with open(test_lockfile_path, 'w') as f:
            sjson.dump(test_lockfile_dict, stream=f)

        e = ev.Environment(str(env_root))
        assert os.path.exists(e._lock_backup_v1_path)
        with open(e._lock_backup_v1_path, 'r') as backup_v1_file:
            lockfile_dict_v1 = sjson.load(backup_v1_file)
        # Make sure that the backup file follows the v1 hash scheme
        assert y.dag_hash() in lockfile_dict_v1['concrete_specs']


@pytest.mark.usefixtures('config')
def test_indirect_build_dep():
    """Simple case of X->Y->Z where Y is a build/link dep and Z is a
    build-only dep. Make sure this concrete DAG is preserved when writing the
    environment out and reading it back.
    """
    default = ('build', 'link')
    build_only = ('build',)

    z = MockPackage('z', [], [])
    y = MockPackage('y', [z], [build_only])
    x = MockPackage('x', [y], [default])

    mock_repo = MockPackageMultiRepo([x, y, z])

    def noop(*args):
        pass
    setattr(mock_repo, 'dump_provenance', noop)

    with spack.repo.swap(mock_repo):
        x_spec = Spec('x')
        x_concretized = x_spec.concretized()

        _env_create('test', with_view=False)
        e = ev.read('test')
        e.add(x_spec)
        e.concretize()
        e.write()

        e_read = ev.read('test')
        x_env_hash, = e_read.concretized_order

        x_env_spec = e_read.specs_by_hash[x_env_hash]
        assert x_env_spec == x_concretized


@pytest.mark.usefixtures('config')
def test_store_different_build_deps():
    r"""Ensure that an environment can store two instances of a build-only
Dependency:

        x       y
       /| (l)   | (b)
  (b) | y       z2
       \| (b)              # noqa: W605
        z1

    """
    default = ('build', 'link')
    build_only = ('build',)

    z = MockPackage('z', [], [])
    y = MockPackage('y', [z], [build_only])
    x = MockPackage('x', [y, z], [default, build_only])

    mock_repo = MockPackageMultiRepo([x, y, z])

    def noop(*args):
        pass
    setattr(mock_repo, 'dump_provenance', noop)

    with spack.repo.swap(mock_repo):
        y_spec = Spec('y ^z@3')
        y_concretized = y_spec.concretized()

        x_spec = Spec('x ^z@2')
        x_concretized = x_spec.concretized()

        # Even though x chose a different 'z', it should choose the same y
        # according to the DAG hash (since build deps are excluded from
        # comparison by default). Although the dag hashes are equal, the specs
        # are not considered equal because they compare build deps.
        assert x_concretized['y'].dag_hash() == y_concretized.dag_hash()

        _env_create('test', with_view=False)
        e = ev.read('test')
        e.add(y_spec)
        e.add(x_spec)
        e.concretize()
        e.write()

        e_read = ev.read('test')
        y_env_hash, x_env_hash = e_read.concretized_order

        y_read = e_read.specs_by_hash[y_env_hash]
        x_read = e_read.specs_by_hash[x_env_hash]

        assert x_read['z'] != y_read['z']


def test_env_updates_view_install(
        tmpdir, mock_stage, mock_fetch, install_mockery):
    view_dir = tmpdir.mkdir('view')
    env('create', '--with-view=%s' % view_dir, 'test')
    with ev.read('test'):
        add('mpileaks')
        install('--fake')

    check_mpileaks_and_deps_in_view(view_dir)


def test_env_without_view_install(
        tmpdir, mock_stage, mock_fetch, install_mockery):
    # Test enabling a view after installing specs
    env('create', '--without-view', 'test')

    test_env = ev.read('test')
    with pytest.raises(spack.environment.SpackEnvironmentError):
        test_env.default_view

    view_dir = tmpdir.mkdir('view')

    with ev.read('test'):
        add('mpileaks')
        install('--fake')

        env('view', 'enable', str(view_dir))

    # After enabling the view, the specs should be linked into the environment
    # view dir
    check_mpileaks_and_deps_in_view(view_dir)


def test_env_config_view_default(
        tmpdir, mock_stage, mock_fetch, install_mockery):
    # This config doesn't mention whether a view is enabled
    test_config = """\
env:
  specs:
  - mpileaks
"""

    _env_create('test', StringIO(test_config))

    with ev.read('test'):
        install('--fake')

    e = ev.read('test')
    # Try retrieving the view object
    view = e.default_view.view()
    assert view.get_spec('mpileaks')


def test_env_updates_view_install_package(
        tmpdir, mock_stage, mock_fetch, install_mockery):
    view_dir = tmpdir.mkdir('view')
    env('create', '--with-view=%s' % view_dir, 'test')
    with ev.read('test'):
        install('--fake', 'mpileaks')

    assert os.path.exists(str(view_dir.join('.spack/mpileaks')))


def test_env_updates_view_add_concretize(
        tmpdir, mock_stage, mock_fetch, install_mockery):
    view_dir = tmpdir.mkdir('view')
    env('create', '--with-view=%s' % view_dir, 'test')
    install('--fake', 'mpileaks')
    with ev.read('test'):
        add('mpileaks')
        concretize()

    check_mpileaks_and_deps_in_view(view_dir)


def test_env_updates_view_uninstall(
        tmpdir, mock_stage, mock_fetch, install_mockery):
    view_dir = tmpdir.mkdir('view')
    env('create', '--with-view=%s' % view_dir, 'test')
    with ev.read('test'):
        install('--fake', 'mpileaks')

    check_mpileaks_and_deps_in_view(view_dir)

    with ev.read('test'):
        uninstall('-ay')

    check_viewdir_removal(view_dir)


def test_env_updates_view_uninstall_referenced_elsewhere(
        tmpdir, mock_stage, mock_fetch, install_mockery):
    view_dir = tmpdir.mkdir('view')
    env('create', '--with-view=%s' % view_dir, 'test')
    install('--fake', 'mpileaks')
    with ev.read('test'):
        add('mpileaks')
        concretize()

    check_mpileaks_and_deps_in_view(view_dir)

    with ev.read('test'):
        uninstall('-ay')

    check_viewdir_removal(view_dir)


def test_env_updates_view_remove_concretize(
        tmpdir, mock_stage, mock_fetch, install_mockery):
    view_dir = tmpdir.mkdir('view')
    env('create', '--with-view=%s' % view_dir, 'test')
    install('--fake', 'mpileaks')
    with ev.read('test'):
        add('mpileaks')
        concretize()

    check_mpileaks_and_deps_in_view(view_dir)

    with ev.read('test'):
        remove('mpileaks')
        concretize()

    check_viewdir_removal(view_dir)


def test_env_updates_view_force_remove(
        tmpdir, mock_stage, mock_fetch, install_mockery):
    view_dir = tmpdir.mkdir('view')
    env('create', '--with-view=%s' % view_dir, 'test')
    with ev.read('test'):
        install('--fake', 'mpileaks')

    check_mpileaks_and_deps_in_view(view_dir)

    with ev.read('test'):
        remove('-f', 'mpileaks')

    check_viewdir_removal(view_dir)


def test_env_activate_view_fails(
        tmpdir, mock_stage, mock_fetch, install_mockery, env_deactivate):
    """Sanity check on env activate to make sure it requires shell support"""
    out = env('activate', 'test')
    assert "To initialize spack's shell commands:" in out


def test_stack_yaml_definitions(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, callpath]
  specs:
    - $packages
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        test = ev.read('test')

        assert Spec('mpileaks') in test.user_specs
        assert Spec('callpath') in test.user_specs


@pytest.mark.regression('12095')
def test_stack_yaml_definitions_write_reference(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, callpath]
    - indirect: [$packages]
  specs:
    - $packages
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')

        with ev.read('test'):
            concretize()
        test = ev.read('test')

        assert Spec('mpileaks') in test.user_specs
        assert Spec('callpath') in test.user_specs


def test_stack_yaml_add_to_list(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, callpath]
  specs:
    - $packages
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            add('-l', 'packages', 'libelf')

        test = ev.read('test')

        assert Spec('libelf') in test.user_specs
        assert Spec('mpileaks') in test.user_specs
        assert Spec('callpath') in test.user_specs


def test_stack_yaml_remove_from_list(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, callpath]
  specs:
    - $packages
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            remove('-l', 'packages', 'mpileaks')

        test = ev.read('test')

        assert Spec('mpileaks') not in test.user_specs
        assert Spec('callpath') in test.user_specs


def test_stack_yaml_remove_from_list_force(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, callpath]
  specs:
    - matrix:
        - [$packages]
        - [^mpich, ^zmpi]
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            concretize()
            remove('-f', '-l', 'packages', 'mpileaks')
            find_output = find('-c')

        assert 'mpileaks' not in find_output

        test = ev.read('test')
        assert len(test.user_specs) == 2
        assert Spec('callpath ^zmpi') in test.user_specs
        assert Spec('callpath ^mpich') in test.user_specs


def test_stack_yaml_attempt_remove_from_matrix(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages:
        - matrix:
            - [mpileaks, callpath]
            - [target=be]
  specs:
    - $packages
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with pytest.raises(SpecListError):
            with ev.read('test'):
                remove('-l', 'packages', 'mpileaks')


def test_stack_concretize_extraneous_deps(tmpdir, config, mock_packages):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [libelf, mpileaks]
    - install:
        - matrix:
            - [$packages]
            - ['^zmpi', '^mpich']
  specs:
    - $install
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            concretize()

        test = ev.read('test')

        for user, concrete in test.concretized_specs():
            assert concrete.concrete
            assert not user.concrete
            if user.name == 'libelf':
                assert not concrete.satisfies('^mpi', strict=True)
            elif user.name == 'mpileaks':
                assert concrete.satisfies('^mpi', strict=True)


def test_stack_concretize_extraneous_variants(tmpdir, config, mock_packages):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [libelf, mpileaks]
    - install:
        - matrix:
            - [$packages]
            - ['~shared', '+shared']
  specs:
    - $install
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            concretize()

        test = ev.read('test')

        for user, concrete in test.concretized_specs():
            assert concrete.concrete
            assert not user.concrete
            if user.name == 'libelf':
                assert 'shared' not in concrete.variants
            if user.name  == 'mpileaks':
                assert (concrete.variants['shared'].value ==
                        user.variants['shared'].value)


def test_stack_definition_extension(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [libelf, mpileaks]
    - packages: [callpath]
  specs:
    - $packages
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')

        test = ev.read('test')

        assert Spec('libelf') in test.user_specs
        assert Spec('mpileaks') in test.user_specs
        assert Spec('callpath') in test.user_specs


def test_stack_definition_conditional_false(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [libelf, mpileaks]
    - packages: [callpath]
      when: 'False'
  specs:
    - $packages
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')

        test = ev.read('test')

        assert Spec('libelf') in test.user_specs
        assert Spec('mpileaks') in test.user_specs
        assert Spec('callpath') not in test.user_specs


def test_stack_definition_conditional_true(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [libelf, mpileaks]
    - packages: [callpath]
      when: 'True'
  specs:
    - $packages
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')

        test = ev.read('test')

        assert Spec('libelf') in test.user_specs
        assert Spec('mpileaks') in test.user_specs
        assert Spec('callpath') in test.user_specs


def test_stack_definition_conditional_with_variable(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [libelf, mpileaks]
    - packages: [callpath]
      when: platform == 'test'
  specs:
    - $packages
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')

        test = ev.read('test')

        assert Spec('libelf') in test.user_specs
        assert Spec('mpileaks') in test.user_specs
        assert Spec('callpath') in test.user_specs


def test_stack_definition_complex_conditional(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [libelf, mpileaks]
    - packages: [callpath]
      when: re.search(r'foo', hostname) and env['test'] == 'THISSHOULDBEFALSE'
  specs:
    - $packages
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')

        test = ev.read('test')

        assert Spec('libelf') in test.user_specs
        assert Spec('mpileaks') in test.user_specs
        assert Spec('callpath') not in test.user_specs


def test_stack_definition_conditional_invalid_variable(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [libelf, mpileaks]
    - packages: [callpath]
      when: bad_variable == 'test'
  specs:
    - $packages
""")
    with tmpdir.as_cwd():
        with pytest.raises(NameError):
            env('create', 'test', './spack.yaml')


def test_stack_definition_conditional_add_write(tmpdir):
    filename = str(tmpdir.join('spack.yaml'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [libelf, mpileaks]
    - packages: [callpath]
      when: platform == 'test'
  specs:
    - $packages
""")
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            add('-l', 'packages', 'zmpi')

        test = ev.read('test')

        packages_lists = list(filter(lambda x: 'packages' in x,
                                     test.yaml['env']['definitions']))

        assert len(packages_lists) == 2
        assert 'callpath' not in packages_lists[0]['packages']
        assert 'callpath' in packages_lists[1]['packages']
        assert 'zmpi' in packages_lists[0]['packages']
        assert 'zmpi' not in packages_lists[1]['packages']


def test_stack_combinatorial_view(tmpdir, mock_fetch, mock_packages,
                                  mock_archive, install_mockery):
    filename = str(tmpdir.join('spack.yaml'))
    viewdir = str(tmpdir.join('view'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, callpath]
    - compilers: ['%%gcc', '%%clang']
  specs:
    - matrix:
        - [$packages]
        - [$compilers]

  view:
    combinatorial:
      root: %s
      projections:
        'all': '{name}/{version}-{compiler.name}'""" % viewdir)
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            install()

        test = ev.read('test')
        for spec in test._get_environment_specs():
            assert os.path.exists(
                os.path.join(viewdir, spec.name, '%s-%s' %
                             (spec.version, spec.compiler.name)))


def test_stack_view_select(tmpdir, mock_fetch, mock_packages,
                           mock_archive, install_mockery):
    filename = str(tmpdir.join('spack.yaml'))
    viewdir = str(tmpdir.join('view'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, callpath]
    - compilers: ['%%gcc', '%%clang']
  specs:
    - matrix:
        - [$packages]
        - [$compilers]

  view:
    combinatorial:
      root: %s
      select: ['%%gcc']
      projections:
        'all': '{name}/{version}-{compiler.name}'""" % viewdir)
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            install()

        test = ev.read('test')
        for spec in test._get_environment_specs():
            if spec.satisfies('%gcc'):
                assert os.path.exists(
                    os.path.join(viewdir, spec.name, '%s-%s' %
                                 (spec.version, spec.compiler.name)))
            else:
                assert not os.path.exists(
                    os.path.join(viewdir, spec.name, '%s-%s' %
                                 (spec.version, spec.compiler.name)))


def test_stack_view_exclude(tmpdir, mock_fetch, mock_packages,
                            mock_archive, install_mockery):
    filename = str(tmpdir.join('spack.yaml'))
    viewdir = str(tmpdir.join('view'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, callpath]
    - compilers: ['%%gcc', '%%clang']
  specs:
    - matrix:
        - [$packages]
        - [$compilers]

  view:
    combinatorial:
      root: %s
      exclude: [callpath]
      projections:
        'all': '{name}/{version}-{compiler.name}'""" % viewdir)
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            install()

        test = ev.read('test')
        for spec in test._get_environment_specs():
            if not spec.satisfies('callpath'):
                assert os.path.exists(
                    os.path.join(viewdir, spec.name, '%s-%s' %
                                 (spec.version, spec.compiler.name)))
            else:
                assert not os.path.exists(
                    os.path.join(viewdir, spec.name, '%s-%s' %
                                 (spec.version, spec.compiler.name)))


def test_stack_view_select_and_exclude(tmpdir, mock_fetch, mock_packages,
                                       mock_archive, install_mockery):
    filename = str(tmpdir.join('spack.yaml'))
    viewdir = str(tmpdir.join('view'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, callpath]
    - compilers: ['%%gcc', '%%clang']
  specs:
    - matrix:
        - [$packages]
        - [$compilers]

  view:
    combinatorial:
      root: %s
      select: ['%%gcc']
      exclude: [callpath]
      projections:
        'all': '{name}/{version}-{compiler.name}'""" % viewdir)
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            install()

        test = ev.read('test')
        for spec in test._get_environment_specs():
            if spec.satisfies('%gcc') and not spec.satisfies('callpath'):
                assert os.path.exists(
                    os.path.join(viewdir, spec.name, '%s-%s' %
                                 (spec.version, spec.compiler.name)))
            else:
                assert not os.path.exists(
                    os.path.join(viewdir, spec.name, '%s-%s' %
                                 (spec.version, spec.compiler.name)))


def test_view_link_roots(tmpdir, mock_fetch, mock_packages, mock_archive,
                         install_mockery):
    filename = str(tmpdir.join('spack.yaml'))
    viewdir = str(tmpdir.join('view'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, callpath]
    - compilers: ['%%gcc', '%%clang']
  specs:
    - matrix:
        - [$packages]
        - [$compilers]

  view:
    combinatorial:
      root: %s
      select: ['%%gcc']
      exclude: [callpath]
      link: 'roots'
      projections:
        'all': '{name}/{version}-{compiler.name}'""" % viewdir)
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            install()

        test = ev.read('test')
        for spec in test._get_environment_specs():
            if spec in test.roots() and (spec.satisfies('%gcc') and
                                         not spec.satisfies('callpath')):
                assert os.path.exists(
                    os.path.join(viewdir, spec.name, '%s-%s' %
                                 (spec.version, spec.compiler.name)))
            else:
                assert not os.path.exists(
                    os.path.join(viewdir, spec.name, '%s-%s' %
                                 (spec.version, spec.compiler.name)))


def test_view_link_all(tmpdir, mock_fetch, mock_packages, mock_archive,
                       install_mockery):
    filename = str(tmpdir.join('spack.yaml'))
    viewdir = str(tmpdir.join('view'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, callpath]
    - compilers: ['%%gcc', '%%clang']
  specs:
    - matrix:
        - [$packages]
        - [$compilers]

  view:
    combinatorial:
      root: %s
      select: ['%%gcc']
      exclude: [callpath]
      link: 'all'
      projections:
        'all': '{name}/{version}-{compiler.name}'""" % viewdir)
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            install()

        test = ev.read('test')
        for spec in test._get_environment_specs():
            if spec.satisfies('%gcc') and not spec.satisfies('callpath'):
                assert os.path.exists(
                    os.path.join(viewdir, spec.name, '%s-%s' %
                                 (spec.version, spec.compiler.name)))
            else:
                assert not os.path.exists(
                    os.path.join(viewdir, spec.name, '%s-%s' %
                                 (spec.version, spec.compiler.name)))


def test_stack_view_activate_from_default(tmpdir, mock_fetch, mock_packages,
                                          mock_archive, install_mockery,
                                          env_deactivate):
    filename = str(tmpdir.join('spack.yaml'))
    viewdir = str(tmpdir.join('view'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, cmake]
    - compilers: ['%%gcc', '%%clang']
  specs:
    - matrix:
        - [$packages]
        - [$compilers]

  view:
    default:
      root: %s
      select: ['%%gcc']""" % viewdir)
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            install()

        shell = env('activate', '--sh', 'test')
        assert 'PATH' in shell
        assert os.path.join(viewdir, 'bin') in shell


def test_stack_view_no_activate_without_default(tmpdir, mock_fetch,
                                                mock_packages, mock_archive,
                                                install_mockery,
                                                env_deactivate):
    filename = str(tmpdir.join('spack.yaml'))
    viewdir = str(tmpdir.join('view'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, cmake]
    - compilers: ['%%gcc', '%%clang']
  specs:
    - matrix:
        - [$packages]
        - [$compilers]

  view:
    not-default:
      root: %s
      select: ['%%gcc']""" % viewdir)
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            install()

        shell = env('activate', '--sh', 'test')
        assert 'PATH' not in shell
        assert viewdir not in shell


def test_stack_view_multiple_views(tmpdir, mock_fetch, mock_packages,
                                   mock_archive, install_mockery,
                                   env_deactivate):
    filename = str(tmpdir.join('spack.yaml'))
    default_viewdir = str(tmpdir.join('default-view'))
    combin_viewdir = str(tmpdir.join('combinatorial-view'))
    with open(filename, 'w') as f:
        f.write("""\
env:
  definitions:
    - packages: [mpileaks, cmake]
    - compilers: ['%%gcc', '%%clang']
  specs:
    - matrix:
        - [$packages]
        - [$compilers]

  view:
    default:
      root: %s
      select: ['%%gcc']
    combinatorial:
      root: %s
      exclude: [callpath %%gcc]
      projections:
        'all': '{name}/{version}-{compiler.name}'""" % (default_viewdir,
                                                        combin_viewdir))
    with tmpdir.as_cwd():
        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            install()

        shell = env('activate', '--sh', 'test')
        assert 'PATH' in shell
        assert os.path.join(default_viewdir, 'bin') in shell

        test = ev.read('test')
        for spec in test._get_environment_specs():
            if not spec.satisfies('callpath%gcc'):
                assert os.path.exists(
                    os.path.join(combin_viewdir, spec.name, '%s-%s' %
                                 (spec.version, spec.compiler.name)))
            else:
                assert not os.path.exists(
                    os.path.join(combin_viewdir, spec.name, '%s-%s' %
                                 (spec.version, spec.compiler.name)))


def test_env_activate_sh_prints_shell_output(
        tmpdir, mock_stage, mock_fetch, install_mockery, env_deactivate
):
    """Check the shell commands output by ``spack env activate --sh``.

    This is a cursory check; ``share/spack/qa/setup-env-test.sh`` checks
    for correctness.
    """
    env('create', 'test', add_view=True)

    out = env('activate', '--sh', 'test')
    assert "export SPACK_ENV=" in out
    assert "export PS1=" not in out
    assert "alias despacktivate=" in out

    out = env('activate', '--sh', '--prompt', 'test')
    assert "export SPACK_ENV=" in out
    assert "export PS1=" in out
    assert "alias despacktivate=" in out


def test_env_activate_csh_prints_shell_output(
        tmpdir, mock_stage, mock_fetch, install_mockery, env_deactivate
):
    """Check the shell commands output by ``spack env activate --csh``."""
    env('create', 'test', add_view=True)

    out = env('activate', '--csh', 'test')
    assert "setenv SPACK_ENV" in out
    assert "setenv set prompt" not in out
    assert "alias despacktivate" in out

    out = env('activate', '--csh', '--prompt', 'test')
    assert "setenv SPACK_ENV" in out
    assert "set prompt=" in out
    assert "alias despacktivate" in out
