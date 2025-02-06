# Summary

This example starts from a spatial clustering of the [Arctic MFC](https://marine.copernicus.eu/about/producers/arctic-mfc)
of the [Copernicus Marine Service](https://marine.copernicus.eu/), originally
provided by the [Nansen Center](https://nersc.no/en/) as `smoothed_ecoregion_6_iteration.nc`.

For each of the clusters, a water column simulation is run using the `gotm`
([General Ocean Turbulence Model](https://gotm.net)) transport engine.
The clusters are connected in a network based on volume transport across their
boundaries, as reconstructed from horizontal velocities from the CMEMS ARC MFC
physics hindcast.

# Installation

* Install [`fabmos`](https://github.com/BoldingBruggeman/fabmos/wiki)

* Install [the Copernicus Marine Toolbox](https://toolbox-docs.marine.copernicus.eu/)
  and [login](https://toolbox-docs.marine.copernicus.eu/en/v2.0.0/usage/login-usage.html)

* Install [the Climate Data Store (CDS) Application Program Interface (API)](https://cds.climate.copernicus.eu/how-to-api)
  and set up its personal access token

* Make sure you have a local copy of the test cases repository:
  
   `git clone https://github.com/BoldingBruggeman/fabmos-cases.git`


# Run
* Go to the "arctic-clusters" test case:

  `cd fabmos-cases/arctic-clusters`

* Activate the fabmos Python environment:
  
  `conda activate fabmos`

* Run the download script that retrieves ERA5 (meteorology), GLODAP
  (initialization) and CMEMS (velocities):

  `python download.py`

  This script will download over 120 GB of data, so make sure you have
  sufficient disk space. If necessary, change the download directory by
  changing `TARGET_DIR` in the script.

* Run the preprocessing script that interpolates GLODAP to the Arctic grid,
  averages ERA5 over each cluster and infers cluster connectivity from CMEMS
  velocities:

  `python preprocess.py`

  This script processes large chunks of meteorological data for efficiency.
  If this causes you to run out of memory, try reducing the `chunksize`
  parameter in the script.

* Run the simulation:

   `python run.py`.

  For subsequent simulations you could try to speed things up by running in
  parallel:
  
  `mpiexec -n <NCORES> python run.py`
  
  Here, `<NCORES>` is the number of CPU cores to use.

* To explore the results, open the `plot.ipynb` notebook, for instance, with
  `jupyter lab plot.ipynb`. You may need to install JupyterLab first in your
  conda environment with `conda install -c conda-forge jupyterlab`

# Notes

* This example was originally run with the exact same ECOSMO version that
  underpinned the CMEMS hindcast used for clustering. This ECOSMO version
  is available as [commit a8d6383 from https://github.com/nansencenter/nersc/tree/TP2_reanalysis_2023](https://github.com/nansencenter/nersc/tree/a8d6383ab236be8761cbb6ac69ae632f8fdedbae)
    