from setuptools import setup, find_packages

setup(
    name="uvp_dataset",
    version="0.1.0",
    packages=find_packages(),
    install_requires=open('requirements.txt').read().splitlines(),
    extras_require={
        'mongodb': ['pymongo>=3.12.0'],
        'redis': ['redis>=4.3.0'],
        's3': ['boto3>=1.24.0'],
    },
    python_requires='>=3.7',
)