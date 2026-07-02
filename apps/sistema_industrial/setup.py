from setuptools import find_packages, setup

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="sistema_industrial",
    version="0.1.0",
    description="Industrial integration app over ERPNext",
    author="SistemaIndustrial",
    author_email="costaratti@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
