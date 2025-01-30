import os.path
import glob
import logging

import fabmos.input.cluster
import pygetm.input.glodap

import run
from download import TARGET_DIR as DATA_DIR

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
    ERA_FILES = os.path.join(DATA_DIR, "era5", "era5_????.nc")
    for infile in glob.glob(ERA_FILES):
        outfile = f"{os.path.basename(infile)[:-3]}.nc"
        logger.info(f"Averaging {infile} and saving to {outfile}...")
        fabmos.input.cluster.average(
            domain,
            infile,
            outfile,
            chunksize=24 * 20,
            averager=fabmos.input.cluster.average_uv,
            periodic_lon=True,
            logger=logger,
        )
