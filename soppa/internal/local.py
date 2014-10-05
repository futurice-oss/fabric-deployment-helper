import os

from fabric.api import env, task

def local_deploy(prompt=True):
    from soppa.operating import Operating
    from soppa.internal.runner.default import Runner
    c = {
    'local_deployment': True,
    'nginx_user': 'nobody',
    'nginx_group': 'nobody',
    'supervisor_user': 'nobody',
    'host': 'localhost',
    'host_string': None,
    'hosts':[],
    'prompt_password':True if prompt else False,
    }

    operating = Operating(env)
    if operating.is_a('darwin'):
        osx_settings = osx_local_settings()
        c.update(osx_settings)

    return c

def osx_local_settings():
    c = {
    'use_sudo': True,
    'deploy_group': 'wheel',
    }

    env.shell = "/bin/bash -c" # default: -l -c

    # MySQL-python will fail due unknown compiler flags in OSX Mavericks
    os.environ['CFLAGS'] = '-Qunused-arguments'
    os.environ['CPPFLAGS'] = '-Qunused-arguments'
    # to run Django commands from fabfile need settings configured
    os.environ['DJANGO_SETTINGS_MODULE'] = getattr(env, 'django_settings', 'settings')

    return c

import fcntl,select,subprocess,os,errno,shlex

# Helper function to add the O_NONBLOCK flag to a file descriptor
def make_async(fd):
    fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)

# Helper function to read some data from a file descriptor, ignoring EAGAIN errors
def read_async(fd):
    try:
        return fd.read()
    except IOError, e:
        if e.errno != errno.EAGAIN:
            raise e
        else:
            return ''

def expand_args(command):
    """Parses command strings and returns a Popen-ready list."""
    splitter = shlex.shlex(command)
    splitter.whitespace = '|'
    splitter.whitespace_split = True
    command = []

    while True:
        token = splitter.get_token()
        if token:
            command.append(token)
        else:
            break
    command = list(map(shlex.split, command))
    return command.pop()

def run(command, cwd=None, shell=True, **kwargs):
    if not shell:
        command = expand_args(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, shell=shell)
    make_async(process.stdout)
    make_async(process.stderr)

    stdout = str()
    stderr = str()
    returnCode = None

    while True:
        # Wait for data to become available
        select.select([process.stdout, process.stderr], [], [])

        # Try reading some data from each
        stdoutPiece = read_async(process.stdout)
        stderrPiece = read_async(process.stderr)

        if stdoutPiece:
            print stdoutPiece,
        if stderrPiece:
            print stderrPiece,

        stdout += stdoutPiece
        stderr += stderrPiece
        returnCode = process.poll()

        if returnCode != None:
            return (returnCode, stdout, stderr)
