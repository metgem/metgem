import os

DOMAIN = "CNRS"
ORGANIZATION = "ICSN"
APPLICATION = "MetGem"
MAJOR = 1
MINOR = 3
MICRO = 0
RELEASE = ""
VERSION = f"{MAJOR}.{MINOR}.{MICRO}{RELEASE}"
FULLVERSION = VERSION

if os.path.exists('.git'):
    import subprocess

    # Borrowed from numpy's setup.py: https://github.com/numpy/numpy/blob/master/setup.py#L70-L92
    # Return the git revision as a string
    def git_version():
        def _minimal_ext_cmd(cmd):
            # construct minimal environment
            env = {}
            for k in ['SYSTEMROOT', 'PATH', 'HOME']:
                v = os.environ.get(k)
                if v is not None:
                    env[k] = v
            # LANGUAGE is used on win32
            env['LANGUAGE'] = 'C'
            env['LANG'] = 'C'
            env['LC_ALL'] = 'C'
            return subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env).communicate()[0]

        try:
            out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
            revision = out.strip().decode('ascii')
        except OSError:
            revision = "Unknown"

        return revision

    GIT_REVISION = git_version()
    FULLVERSION += '.dev0+' + GIT_REVISION[:10]
