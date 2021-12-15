from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="langame",
        packages=find_packages(),
        include_package_data=True,
        version="1.0.0",
        description="",
        install_requires=[
            "firebase_admin",
            "openai",
            "confuse",
            "transformers",
        ],
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.6",
        ],
    )