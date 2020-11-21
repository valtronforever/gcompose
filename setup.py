import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gcompose",
    version="0.1.0",
    author="Valentin Osipenko",
    author_email="valtron.forever@gmail.com",
    description="Docker-compose gui",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/valtronforever/gcompose",
    packages=setuptools.find_packages(),
    package_data={
        "gcompose.windows": ["*.glade"],
        "gcompose.widgets": ["*.glade"],
    },
    include_package_data=True,
    scripts=['bin/gcompose'],
    install_requires=[
        'pydantic',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
