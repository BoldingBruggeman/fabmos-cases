import os.path
import logging

import xarray as xr
from dask.diagnostics import ProgressBar

import fabmos.input.cluster
import pygetm.input.glodap

import run
from download import TARGET_DIR as DATA_DIR, MINYEAR, MAXYEAR

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    domain = run.get_domain(cluster=True)

    # Interpolate GLODAP to the original model grid, but wait with averaging
    # over clusters until runtime, as we need the vertical layer distribution
    pygetm.input.glodap.regrid(
        os.path.join(DATA_DIR, "glodap.nc"),
        domain.full_lon,
        domain.full_lat,
        "glodap_ip.nc",
        clamp=True,
        logger=logger,
    )

    # Calculate transport between clusters from CMEMS velocities
    FLOW_FILE = os.path.join(DATA_DIR, "cmems", "flow.nc")
    u = fabmos.input.from_nc(FLOW_FILE, "vxo")
    v = fabmos.input.from_nc(FLOW_FILE, "vyo")
    fabmos.input.cluster.get_connectivity(
        domain, u, v, "connections.nc", periodic_lon=True, logger=logger
    )

    # Average ERA5 per cluster (special treatment of wind components u10 and
    # v10 to preserve average wind speed)
    for year in range(MINYEAR, MAXYEAR + 1):
        era_files = os.path.join(DATA_DIR, "era5", f"era5_*_{year}.nc")
        outfile = f"era5_{year}.nc"
        logger.info(f"Averaging {year} and saving to {outfile}...")
        with xr.open_mfdataset(era_files, compat="no_conflicts") as ds:
            ds_av = fabmos.input.cluster.average(
                domain,
                ds,
                outfile,
                chunksize=24 * 20,
                averagers={("u10", "v10"): fabmos.input.cluster.average_uv},
                periodic_lon=True,
                logger=logger,
            )
            with ProgressBar():
                ds_av.to_netcdf(outfile, mode="w")