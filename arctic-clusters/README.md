This example starts from a spatial clustering of the [Arctic MFC](https://marine.copernicus.eu/about/producers/arctic-mfc) of the [Copernicus Marine Service](https://marine.copernicus.eu/), originally provided by the [Nansen Center](https://nersc.no/en/) as `smoothed_ecoregion_6_iteration.nc`.

For each of the clusters, a water column simulation is run using the `gotm` ([General Ocean Turbulence Model](https://gotm.net)) transport engine.

To run this example:

* [Install `fabmos`](https://github.com/BoldingBruggeman/fabmos/wiki)
* Make sure you have a local copy of the test cases repository with `git clone https://github.com/BoldingBruggeman/fabmos-cases.git`
* Go to the "arctic-clusters" test case: `cd fabmos-cases/arctic-clusters`
* Activate the fabmos Python environment with `conda activate fabmos`
* Obtain [GLODAPv2](https://doi.org/10.5194/essd-8-325-2016), which provides initial conditions for temperature, salinity and biogeochemistry. To do this, execute `python -m pygetm.input.glodap glodap.nc`
* Run the preprocessing script that interpolates GLODAP to the Arctic grid: `python preprocessing.py`
* Run the simulation with `python run.py`.

  The first time you run this script, it will download the necessary meteorological forcing. This may take a while.

  For subsequent simulations you could to speed things up by running in parallel: `mpiexec -n <NCORES> python run.py`, where `<NCORES>` is the number of CPU cores to use.
* To explore the results, open the `plot.ipynb` notebook, for instance, with `jupyter lab plot.ipynb`. You may need to install JupyterLab first in your conda environment with `conda install -c conda-forge jupyterlab`
