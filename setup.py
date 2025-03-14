from setuptools import setup, find_packages

setup(
    name="s3u",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "aioboto3",
        "pyperclip",
        "questionary",  # Added for interactive menus
    ],
    entry_points={
        'console_scripts': [
            's3u=s3u.cli:run_cli',  # Use the synchronous wrapper function
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="S3 Upload Utility - Optimize images and upload files to S3",
    keywords="s3, upload, aws, utility, images",
    url="https://github.com/yourusername/s3u",
)