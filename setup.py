import setuptools

setuptools.setup(
    name='piggia',
    version='0.2.0',
    url='https://github.com/esrice/piggia',
    license='GPL-3.0',
    packages=['piggia'],
    install_requires=[
        'pyyaml',
        'Flask',
        'Flask-WTF',
        'spidev',
        'matplotlib',
    ],
    python_requires='>=3',
    entry_points={
        'console_scripts': [
            'app=piggia.app:main',
            'controller=piggia.controller:main',
        ],
    },
)
