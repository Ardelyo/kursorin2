#!/usr/bin/env python3
"""
KURSORIN - Webcam-Based Human-Computer Interaction System
Setup configuration for package installation.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = (this_directory / "requirements.txt").read_text().splitlines()
requirements = [r.strip() for r in requirements if r.strip() and not r.startswith("#")]

setup(
    name="kursorin",
    version="1.0.0",
    author="Ardellio Satria Anindito",
    author_email="email.ardellio@contoh.com",
    description="Affordable Webcam-Based Human-Computer Interaction System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/kursorin",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/kursorin/issues",
        "Documentation": "https://github.com/yourusername/kursorin/docs",
        "Source Code": "https://github.com/yourusername/kursorin",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "scripts"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Adaptive Technologies",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "isort>=5.12.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "mkdocs>=1.4.0",
            "mkdocs-material>=9.0.0",
            "mkdocstrings>=0.20.0",
        ],
        "gpu": [
            "tensorflow-gpu>=2.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kursorin=kursorin.__main__:main",
            "kursorin-cli=kursorin.cli:main",
        ],
        "gui_scripts": [
            "kursorin-gui=kursorin.app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "kursorin": [
            "assets/icons/*.ico",
            "assets/icons/*.png",
            "assets/sounds/*.wav",
            "assets/calibration/*.png",
        ],
    },
    zip_safe=False,
    keywords=[
        "eye-tracking",
        "head-tracking",
        "hand-tracking",
        "accessibility",
        "human-computer-interaction",
        "computer-vision",
        "mediapipe",
        "webcam",
        "hands-free",
        "assistive-technology",
    ],
)
