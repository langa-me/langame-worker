from setuptools import setup, find_packages
from pathlib import Path

if __name__ == "__main__":
    with Path(Path(__file__).parent, "README.md").open(encoding="utf-8") as file:
        long_description = file.read()

    setup(
        name="langame",
        packages=find_packages(),
        include_package_data=True,
        version="1.0.0",
        description="",
        long_description=long_description,
        long_description_content_type="text/markdown",
        data_files=[(".", ["README.md"])],
        install_requires=[
            "firebase_admin",
            "openai",
            "beautifulsoup4",
            "confuse",
            "algoliasearch",
            "markdown",
            "plotly",
            "matplotlib",
            "ipykernel",
            "numpy",
            "kaggle",
            "pytrends"
        ],
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.6",
        ],
    )