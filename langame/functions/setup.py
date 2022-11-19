from setuptools import setup, find_packages

with open("requirements.txt") as f:
    required = f.read().splitlines()

if __name__ == "__main__":
    setup(
        name="common",
        packages=find_packages(),
        include_package_data=True,
        version="1.0.0",
        description="",
        install_requires=required,
    )
