"""Setup script for Gmail Semantic Email CLI."""
from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

setup(
    name="semantic-email-cli",
    version="1.0.0",
    description="Gmail CLI for managing and searching emails with semantic search",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "gmail-cli=main:app",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
