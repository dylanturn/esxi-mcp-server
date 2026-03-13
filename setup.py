"""Setup configuration for ESXi MCP Server."""

from setuptools import setup, find_packages

import os

_here = os.path.abspath(os.path.dirname(__file__))

try:
    with open(os.path.join(_here, "README.md"), "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = ""

try:
    with open(os.path.join(_here, "requirements.txt"), "r", encoding="utf-8") as fh:
        requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
except FileNotFoundError:
    requirements = []

setup(
    name="esxi-mcp-server",
    version="0.0.1",
    author="Bright8192",
    description="A VMware ESXi/vCenter management server based on MCP (Model Control Protocol)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dylanturn/esxi-mcp-server",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "esxi-mcp-server=esxi_mcp_server.__main__:main",
        ],
    },
)
