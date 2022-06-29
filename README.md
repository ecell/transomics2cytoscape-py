# transomics2cytoscape-py
Automation of the transomics 2.5D network visualization

## Install

```
pip install git+https://github.com/ecell/transomics2cytoscape-py
```

## Run

1. Install and launch [Cytoscape](https://cytoscape.org/).
2. Install [KEGGscape App](https://apps.cytoscape.org/apps/keggscape) on [Cytoscape App Manager](http://manual.cytoscape.org/en/stable/App_Manager.html).
2. Run Python interactive shell with `python` command.
3. Run the command in 1.
```
from transomics2cytoscape import transomics2cytoscape as t2c
t2c.create3Dnetwork("https://raw.githubusercontent.com/ecell/transomics2cytoscape/master/inst/extdata/usecase1/yugi2014.tsv")
```
