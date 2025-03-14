from setuptools import setup, find_packages

setup(
    name="s3u",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aioboto3",
        "pyperclip",
    ],
    entry_points={
        'console_scripts': [
            's3u=s3u.cli:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for uploading files to S3 with automatic renaming and CloudFront URL generation",
    keywords="aws, s3, upload, cloudfront",
    python_requires=">=3.7",
)