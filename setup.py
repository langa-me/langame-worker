from setuptools import setup, find_packages

if __name__ == "__main__":
    # https://github.com/mautrix/telegram/blob/master/setup.py
    with open("optional-requirements.txt", encoding="utf-8") as reqs:
        extras_require = {}
        current = []
        for line in reqs.read().splitlines():
            if line.startswith("#/"):
                extras_require[line[2:]] = current = []
            elif not line or line.startswith("#"):
                continue
            else:
                current.append(line)

    extras_require["all"] = list({dep for deps in extras_require.values() for dep in deps})


    setup(
        name="langame",
        packages=find_packages(),
        include_package_data=True,
        version="1.2.1",
        description="",
        install_requires=[
            "firebase_admin",
            "requests",
        ],
        extras_require=extras_require,
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Topic :: Scientific/Engineering :: Artificial Intelligence",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.6",
        ],
    )