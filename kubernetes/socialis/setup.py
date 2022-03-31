from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="socialis",
        packages=find_packages(),
        include_package_data=True,
        version="1.0.0",
        entry_points={"console_scripts": ["ava = ava:main"]},
        author="Louis Beaumont",
        author_email="louis.beaumont@langa.me",
        url="https://github.com/langa-me/langame-worker",
        install_requires=[
            "grpcio",
            "firebase-admin",
            "fire",
            "transformers",
            "torch",
            "websocket-client",
            "discord",
            "deep-translator",
        ],
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.6",
        ],
    )
