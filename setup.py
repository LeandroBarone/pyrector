import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyrector",
    version="0.1.1",
    author="Leandro Barone",
    author_email="web@leandrobarone.com.ar",
    description="A thin, opinionated Python library for building short-form videos.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LeandroBarone/pyrector",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    install_requires=['moviepy'],
)
