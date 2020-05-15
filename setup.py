from setuptools import find_packages, setup

# Dependencies required to use your package
INSTALL_REQS = ['requests==2.22.0']

# Dependencies required only for running tests
TEST_REQS = ['pytest', 'pytest-runner', 'pytest-cov']

DOC_REQS = ['mkdocs', 'markdown_refdocs', 'mkdocs-material']

# Dependencies required for deploying to an index server
DEPLOYMENT_REQS = ['twine', 'wheel']

DEV_REQS = (
    TEST_REQS + DEPLOYMENT_REQS + ['black', 'flake8', 'flake8-annotations', 'isort'] + DOC_REQS
)


setup(
    name='graphkb',
    version='1.3.0',
    packages=find_packages(),
    install_requires=INSTALL_REQS,
    extras_require={'dev': DEV_REQS, 'deploy': DEPLOYMENT_REQS, 'test': TEST_REQS, 'doc': DOC_REQS},
    python_requires='>=3.6',
    author_email='creisle@bcgsc.ca',
    dependency_links=[],
    test_suite='tests',
    tests_require=TEST_REQS,
    entry_points={'console_scripts': []},
)
