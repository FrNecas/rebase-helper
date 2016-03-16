How to use rebase-helper for Upstream Monitoring systems
========================================================

The page describes an integration rebase-helper into an upstream monitoring systems.
Of course you need to install rebase-helper package
- either as RPM::

  dnf install rebase-helper

- from GitHub::

  git clone https://github.com/phracek/rebase-helper

Nowadays we supporting only koji build systems as a support for upstream monitoring systems.
But time changes and we are opened for the another build systems.

- Patch the new sources and run koji scratch build
-- Python API usage::

   from rebasehelper.application import Application
   cli = CLI([‘--non-interactive, ‘--builds-nowait’, ‘-buildtool’, ‘fedpkg’, upstream_version])
   rh = Application(cli)
   rh.set_upstream_monitoring() # Switch rebase-helper to upstream release monitoring mode.
   rh.run()
   rh.get_rebasehelper_data() # Get all information about the results
-- Bash usage::

    rebase-helper --non-interactive --builds-nowait --buildtool fedpkg upstream_version

- Download logs and RPMs for comparing with checkers
-- Python API usage::

   cli = CLI([‘--non-interactive, ‘--builds-nowait’, ‘--fedpkg-build-tasks old_id,new-id])
   rh.run() # Downloads RPMs, logs and runs checkers and provides logs.
   rh.get_rebasehelper_data() # Get all information about the results
-- Bash usage::

   rebase-helper --non-interactive --builds-nowait --fedpkg-build-tasks old_id,new-id

