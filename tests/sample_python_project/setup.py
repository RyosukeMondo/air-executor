"""Setup file for sample Python project."""

from setuptools import setup, find_packages

setup(
    name="sample-python-project",
    version="0.1.0",
    description="Sample Python project for testing multi-language orchestrator",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        'test': [
            'pytest>=7.0.0',
            'pytest-cov>=3.0.0',
        ],
    },
)
