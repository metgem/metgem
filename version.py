import os

DOMAIN = "CNRS"
ORGANIZATION = "ICSN"
APPLICATION = "HDiSpeC"
MAJOR = 0
MINOR = 9
MICRO = 0
VERSION = f"{MAJOR}.{MINOR}.{MICRO}"
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
            out = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env).communicate()[0]
            return out

        try:
            out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
            GIT_REVISION = out.strip().decode('ascii')
        except OSError:
            GIT_REVISION = "Unknown"

        return GIT_REVISION

    GIT_REVISION = git_version()
    FULLVERSION += '.dev0+' + GIT_REVISION[:10]
