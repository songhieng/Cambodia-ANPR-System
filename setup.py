"""
Cambodia ANPR System - Setup Configuration
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="cambodia-anpr",
    version="2.0.0",
    author="Cambodia ANPR Team",
    description="Production-ready Automatic Number Plate Recognition system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests", "outputs", "logs"]),
    python_requires=">=3.8",
    install_requires=[
        "ultralytics>=8.0.114",
        "opencv-python>=4.7.0",
        "easyocr>=1.7.0",
        "numpy>=1.24.3",
        "scipy>=1.10.1",
        "filterpy>=1.4.5",
        "gradio>=3.50.0",
        "streamlit>=1.28.0",
        "firebase-admin>=6.0.0",
        "python-dotenv>=1.0.0",
        "pandas>=2.0.0",
        "pytest>=7.4.0"
    ],
    entry_points={
        'console_scripts': [
            'anpr-cli=apps.cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
