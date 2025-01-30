import os.path
import copernicusmarine
import pygetm.input.glodap
import pygetm.input.era5
import run

TARGET_DIR = "."  # Target dir for downloads (~120 GB!)

MINYEAR = 2015
MAXYEAR = 2020

if __name__ == "__main__":
    domain = run.get_domain(cluster=False)

    # GLODAP initial conditions (global)
    pygetm.input.glodap.download_and_process(os.path.join(TARGET_DIR, "glodap.nc"))

    # ERA5 meteorology (lat-lon recangle encompassing original domain)
    lon = domain.lon[1::2, 1::2]
    lat = domain.lat[1::2, 1::2]
    era_year2path = pygetm.input.era5.get(
        lon.min(),
        lon.max(),
        lat.min(),
        lat.max(),
        MINYEAR,
        MAXYEAR,
        variables=("t2m", "d2m", "u10", "v10", "sp", "tcc", "siconc"),
        target_dir=os.path.join(TARGET_DIR, "era5"),
    )

    # CMEMS currents to infer cluster connectivity (entire Arctic MFC)
    copernicusmarine.subset(
        dataset_id="cmems_mod_arc_phy_my_topaz4_P1M",
        variables=["vxo", "vyo"],
        start_datetime=f"{MINYEAR}-01-01T00:00:00",
        end_datetime=f"{MAXYEAR + 1}-01-01T00:00:00",
        output_filename="flow.nc",
        output_directory=os.path.join(TARGET_DIR, "cmems"),
    )
