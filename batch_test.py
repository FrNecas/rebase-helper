import json
import logging
import os
import re
import shutil
import sys
import tempfile
import traceback

import git
import rpm
import six

from rebasehelper.cli import CLI
from rebasehelper.application import Application
from rebasehelper.exceptions import RebaseHelperError
from rebasehelper.logger import logger, LoggerHelper
from rebasehelper.settings import REBASE_HELPER_RESULTS_DIR


CLONE_URL = 'https://src.fedoraproject.org/rpms'

PACKAGES = [
    'perl-Config-MVP-Slicer',
    'perl-Date-Manip',
    'perl-Net-GitHub',
    'portpub',
    'postgresql',
    'python-mysql',
    'python-simpleline',
    'python-subunit2sql',
    'rakudo-zef',
    'rtags',
    'setup',
    'streameye',
    'syncthing',
    'valabind',
    'votca-xtp',
]


def clone_dist_git(package, basedir):
    url = '{}/{}'.format(CLONE_URL, package)
    workdir = os.path.join(basedir, package)
    if os.path.isdir(workdir):
        shutil.rmtree(workdir)
    try:
        repo = git.Repo.clone_from(url, workdir)
    except git.exc.GitCommandError:
        return None, None
    return repo, workdir


def find_latest_rebase(repo, workdir):
    def get_version(stream):
        with tempfile.NamedTemporaryFile() as f:
            f.write(stream.read())
            f.flush()
            spec = rpm.spec(f.name)
            return spec.sourceHeader[rpm.RPMTAG_VERSION].decode()
    spec = [f for f in os.listdir(workdir) if os.path.splitext(f)[1] == '.spec']
    if not spec:
        return None, None, None
    for commit in repo.iter_commits(paths=spec[0]):
        if not commit.parents:
            continue
        blob = [b for b in commit.parents[0].tree.blobs if b.name == spec[0]]
        if not blob:
            continue
        old_version = get_version(blob[0].data_stream)
        blob = [b for b in commit.tree.blobs if b.name == spec[0]]
        if not blob:
            continue
        new_version = get_version(blob[0].data_stream)
        if old_version == new_version:
            continue
        diff = repo.git.diff(commit.parents[0], commit, stdout_as_string=False)
        repo.git.checkout(commit.parents[0], force=True)
        return old_version, new_version, diff
    return None, None, None
    

def rebase(version):
    os.environ['LANG'] = 'en_US'
    for handler in logger.handlers:
        logger.removeHandler(handler)
    LoggerHelper.add_stream_handler(logger, logging.INFO)
    cli = CLI([
        '--non-interactive',
        '--disable-inapplicable-patches',
        '--build-retries', '1',
        '--buildtool', 'mock',
        '--outputtool', 'json',
        '--pkgcomparetool', 'rpmdiff,pkgdiff,abipkgdiff',
        '--color', 'never',
        version
    ])
    execution_dir, results_dir, debug_log_file = Application.setup(cli)
    app = Application(cli, execution_dir, results_dir, debug_log_file)
    app.run()


def analyze():
    def analyze_srpm_log(log):
        # TODO: just detect failure/success
        return {}
    def analyze_mock_output_log(log):
        # TODO: just detect failure/success
        return {}
    def analyze_root_log(log):
        # TODO: just detect failure/success
        return {}
    def analyze_build_log(log):
        error_re = re.compile(r'^error: Bad exit status from .+ \((%\w+)\)$')
        with open(log) as f:
            for line in f.readlines():
                match = error_re.match(line)
                if match:
                    return dict(section=match.group(1))
        return {}
    result = {}
    report_file = os.path.join(REBASE_HELPER_RESULTS_DIR, 'report.json')
    if not os.path.isfile(report_file):
        return result
    with open(report_file) as f:
        report = json.load(f)
        try:
            result['result'] = list(report['result'].keys())[0]
            for version in ['old', 'new']:
                if 'source_package_build_error' in report['builds'][version]:
                    result['build_failure'] = dict(version=version, kind='srpm')
                    for log in report['builds'][version]['logs']:
                        if 'build.log' in log and 'SRPM' in log:
                            result['build_failure'].update(analyze_srpm_log(log))
                elif 'binary_package_build_error' in report['builds'][version]:
                    result['build_failure'] = dict(version=version, kind='rpm')
                    for log in report['builds'][version]['logs']:
                        if 'mock_output.log' in log:
                            result['build_failure'].update(analyze_mock_output_log(log))
                        elif 'root.log' in log:
                            result['build_failure'].update(analyze_root_log(log))
                        elif 'build.log' in log and not 'SRPM' in log:
                            result['build_failure'].update(analyze_build_log(log))
        except KeyError:
            pass
    return result


def run(packages, basedir):
    def save_diff(diff):
        with open(os.path.join(basedir, '{}.patch'.format(package)), 'wb') as f:
            f.write(diff)
            f.write(b'\n')
    def save_data(data):
        with open(os.path.join(basedir, '{}.json'.format(package)), 'w') as f:
            json.dump(data, f, sort_keys=True, indent=4, separators=(',', ': '))
    for package in packages:
        data = dict(package=package)
        print('INFO: Processing package {}'.format(package))
        try:
            repo, workdir = clone_dist_git(package, basedir)
            if not repo:
                print('ERROR: Error cloning dist-git!')
                continue
            old_version, new_version, diff = find_latest_rebase(repo, workdir)
            if not old_version:
                print('ERROR: Latest rebase not found!')
                shutil.rmtree(workdir)
                continue
            save_diff(diff)
            data['old_version'] = old_version
            data['new_version'] = new_version
            os.chdir(workdir)
            try:
                rebase(new_version)
            except RebaseHelperError as e:
                data['rh-error'] = e.msg if e.msg else six.text_type(e)
            data.update(analyze())
            save_data(data)
        except Exception as e:
            data['exception'] = six.text_type(e)
            _, _, tb = sys.exc_info()
            data['traceback'] = traceback.format_tb(tb)
            save_data(data)


def main():
    run(PACKAGES, os.getcwd())


if __name__ == '__main__':
    main()
