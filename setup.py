from setuptools import setup, find_packages

setup(
    name="kerma",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "cryptography>=41.0.0",
        "jcs>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "kerma=kerma.main:main",
        ],
    },
    description="KermaChain - A Python P2P Blockchain Node Implementation",
    author="Abdullah Al Mamun",
    author_email="mamun.swe.de@gmail.com",
    url="https://github.com/abbysweb/KermaChain",
    project_urls={
        "Source": "https://github.com/abbysweb/KermaChain",
        "ORCID": "https://orcid.org/0009-0006-7473-0024",
    },
)
