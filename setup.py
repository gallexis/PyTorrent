from setuptools import setup


with open("README.md", "r") as fh:
    long_description = ""
    header_count = 0
    for line in fh:
        if line.startswith("##"):
            header_count += 1
        if header_count < 2:
            long_description += line
        else:
            break

setup(
    name='pytorrent',
    version='0.0.1',
    author='Alexis Gallèpe',
    author_email="alexis.gallepe@gmail.com",
    description="A pure Python library for downloading torrents.",
    url='https://github.com/gallexis/pytorrent',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=["bittorrent", "peer-to-peer", "p2p", "bittorrent-client", "bittorrent-network", "peer-2-peer"],    
    python_requires=">=3.6",
    install_requires=[
        "bcoding == 1.5",
        "bitstring ~= 3.1.7",
        "requests >= 2.24.0",
        "pubsub == 0.1.2",
        "ipaddress == 1.0.23",
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ]
)
