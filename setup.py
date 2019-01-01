import os, setuptools, subprocess

# Construct the redo input files, including redo.version, if we're
# starting from the original redo source dir.  If we're running
# from the python pip package, the files already exist, so we
# skip this step.
mydir = os.path.dirname(__file__)
script = os.path.join(mydir, 'do')
verfile = os.path.join(mydir, 'redo/version/_version.py')
if os.path.exists(script) and not os.path.exists(verfile):
    subprocess.check_call([script])


import redo.version


def read(fname):
    return open(os.path.join(mydir, fname)).read()

    
# FIXME: we probably need to build redo/sh on the target system, somehow.
setuptools.setup(
    name = 'redo-tools',
    version = redo.version.TAG.replace('-', '+', 1),
    python_requires='>=2.7, <3.0',
    author = 'Avery Pennarun',
    author_email = 'apenwarr@gmail.com',
    description = ('djb redo: a recursive, general purpose build system.'),
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    license = 'Apache',
    keywords = 'redo redo-ifchange make dependencies build system compiler',
    url = 'https://github.com/apenwarr/redo',
    packages = setuptools.find_packages(),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Utilities',
    ],
    entry_points = {
        'console_scripts': [
            'redo=redo.cmd_redo:main',
            'redo-always=redo.cmd_always:main',
            'redo-ifchange=redo.cmd_ifchange:main',
            'redo-ifcreate=redo.cmd_ifcreate:main',
            'redo-log=redo.cmd_log:main',
            'redo-ood=redo.cmd_ood:main',
            'redo-sources=redo.cmd_sources:main',
            'redo-stamp=redo.cmd_stamp:main',
            'redo-targets=redo.cmd_targets:main',
            'redo-unlocked=redo.cmd_unlocked:main',
            'redo-whichdo=redo.cmd_whichdo:main',
        ],
    },
)
