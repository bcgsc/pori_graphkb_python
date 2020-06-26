from setuptools import find_packages, setup

# Dependencies required to use your package
INSTALL_REQS = ['requests==2.22.0', 'typing_extensions>=3.7.4.2']

# Dependencies required only for running tests
TEST_REQS = ['pytest', 'pytest-runner', 'pytest-cov']

DOC_REQS = ['mkdocs', 'markdown_refdocs', 'mkdocs-material']

# Dependencies required for deploying to an index server
DEPLOYMENT_REQS = ['twine', 'wheel']

DEV_REQS = (
    TEST_REQS
    + DEPLOYMENT_REQS
    + ['black', 'flake8', 'flake8-annotations', 'isort', 'mypy']
    + DOC_REQS
)
long_description = ''

try:
    import os

    with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as fh:
        long_description = fh.read()
except Exception:
    pass


setup(
    name='graphkb',
    version='1.3.4',
    description='python adapter for interacting with the GraphKB API',
    url='https://github.com/bcgsc/pori_graphkb_python',
    packages=find_packages(),
    package_data={"graphkb": ["py.typed"]},
    install_requires=INSTALL_REQS,
    extras_require={'dev': DEV_REQS, 'deploy': DEPLOYMENT_REQS, 'test': TEST_REQS, 'doc': DOC_REQS},
    python_requires='>=3.6',
    author_email='graphkb@bcgsc.ca',
    test_suite='tests',
    tests_require=TEST_REQS,
    long_description=long_description,
    long_description_content_type='text/markdown',
)
