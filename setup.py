from setuptools import setup, find_packages

setup(
    name="aegistruth",
    version="1.0.0",
    description="Autonomous Multi-Modal AI Forensics, Deepfake Detection & Fact Verification Sentinel",
    author="AegisTruth Core Team",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic",
        "numpy",
        "scipy",
        "pillow",
        "python-multipart",
        "websockets",
        "jinja2"
    ],
    entry_points={
        "console_scripts": [
            "aegistruth=aegistruth.cli:main",
        ],
    },
    python_requires=">=3.10",
)
