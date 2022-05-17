import setuptools

# Nasty but effective way to set __version__
__version__=None
exec(open("transomics2cytoscape/_version.py").read())

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="transomics2cytoscape",
    version=__version__,
    author="Kozo Nishida",
    author_email="kozo.nishida@gmail.com",
    maintainer='Kozo Nishida',
    maintainer_email='kozo.nishida@gmail.com',
    description="An automation for 3D Trans-Omic network visualization with Cytoscape",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="hhttps://github.com/ecell/transomics2cytoscape-py",
    license='MIT License',
    keywords=['data visualization', 'visualization',
              'bioinformatics', 'graph', 'network'],
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        'py4cytoscape'
    ],
    classifiers=[
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Visualization'
    ],
    python_requires='>=3.7',
    test_suite='tests',
)
