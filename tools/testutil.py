#!/usr/bin/env python3
"""
/*
 * This file is part of rdp2tcp
 *
 * Copyright (C) 2025, jnqpblc
 *
 */
Shared helpers for the rdp2tcp test scripts.

Integration tests need a live RDP session and a running controller, and they
create/delete real tunnels. They are therefore opt-in: set the environment
variable RDP2TCP_RUN_INTEGRATION=1 (or pass --run) to actually execute them.
When not enabled they print a SKIPPED notice and exit 0 without pretending to
have verified anything.
"""

import os
import sys

ENABLE_ENV = 'RDP2TCP_RUN_INTEGRATION'


def integration_enabled(argv=None):
    argv = sys.argv if argv is None else argv
    return os.environ.get(ENABLE_ENV) == '1' or '--run' in argv


def require_integration(name):
    """Exit 0 with a SKIPPED message unless integration tests are enabled."""
    if integration_enabled():
        return
    sys.stderr.write(
        f"SKIPPED: {name} is an integration test that creates/deletes real "
        f"tunnels against a live endpoint.\n"
        f"         Set {ENABLE_ENV}=1 (or pass --run) to execute it.\n")
    sys.exit(0)
