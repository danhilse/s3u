from setuptools import setup, find_packages
import subprocess
import sys

# Check for FFmpeg at install time (optional)
try:
    subprocess.check_output(['ffmpeg', '-version'], stderr=subprocess.STDOUT)
    subprocess.check_output(['ffprobe', '-version'], stderr=subprocess.STDOUT)
except (subprocess.SubprocessError, FileNotFoundError):
    print("WARNING: FFmpeg and/or FFprobe not found. Image optimization features will not work.")
    print("Please install FFmpeg: https://ffmpeg.org/download.html")

setup(
    name="s3u",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aioboto3",
        "pyperclip",
        "questionary",  # For interactive menus
        "tqdm",         # Needed for progress tracking
        "boto3",        # Base dependency for S3 operations
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "flake8",
            "black",
        ],
    },
    entry_points={
        'console_scripts': [
            's3u=s3u.cli:run_cli',
        ],
    },
    python_requires=">=3.7",
    author="Daniel Hilse",
    author_email="danhilse@gmail.com",
    description="S3 Upload Utility - Optimize images and upload files to S3",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="s3, upload, aws, utility, images, optimization, cloudfront",
    url="https://github.com/danhilse/s3u",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Topic :: Utilities",
    ],
)