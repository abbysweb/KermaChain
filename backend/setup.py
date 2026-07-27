from setuptools import setup, find_packages

setup(
    name="kermachain",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "cryptography>=41.0.0",
        "jcs>=1.0.0",
        "aiohttp>=3.9.0",
    ],
    entry_points={
        "console_scripts": [
            "kermachain=kerma.main:main",
        ],
    },
    description="KermaChain - A Python P2P Blockchain Node (Marabu Protocol)",
    author="Abdullah Al Mamun",
    author_email="mamun.swe.de@gmail.com",
    url="https://github.com/abbysweb/KermaChain",
)
