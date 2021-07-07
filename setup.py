from setuptools import find_packages, setup

import archiver

setup(
    name='archiver',
    version=archiver.version,
    description='Command-line preservation archiving tool for S3',
    author='Joshua A. Westgard',
    author_email="westgard@umd.edu",
    platforms=["any"],
    license="MIT",
    url="http://github.com/jwestgard/aws-archiver",
    packages=find_packages(),
    entry_points={
        'console_scripts': ['archiver=archiver.__main__:main']
        },
    install_requires=[i.strip() for i in open("requirements.txt").readlines()],
    python_requires='>=3.7',
    extras_require={  # Optional
       'dev': ['pycodestyle'],
       'test': [],
    }
)
