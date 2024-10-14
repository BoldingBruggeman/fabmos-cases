import datetime
import os.path

import netCDF4
import numpy as np

import fabmos
import fabmos.transport.gotm
import pygetm
import pygetm.input.igotm

FABM_CONFIG = "../../fabmos/extern/fabm/testcases/fabm-nersc-ecosmo.yaml"
GOTM_CONFIG = "gotm.yaml"
CLUSTER_FILE = "smoothed_ecoregion_6_iteration.nc"
SPLIT_CLUSTERS = True

POSTFIX = "_split" if SPLIT_CLUSTERS else ""

with netCDF4.Dataset(CLUSTER_FILE) as nc:
    depth = nc["depth"]
    ny, nx = depth.shape
    nz = 50
    masked = np.ma.getmaskarray(depth)
    domain = fabmos.domain.create(
        nx,
        ny,
        nz,
        x=np.arange(nx)[np.newaxis, :],
        y=np.arange(ny)[:, np.newaxis],
        lon=nc["longitude"],
        lat=nc["latitude"],
        H=depth,
        mask=np.where(masked, 0, 1),
        spherical=False,
        glob=True,
        halox=0,
        haloy=0,
    )
    clusters = np.ma.array(nc["ecoregion"], mask=masked)
    if SPLIT_CLUSTERS:
        clusters = fabmos.domain.split_clusters(clusters)
    domain = fabmos.domain.compress_clusters(domain, clusters)

sim = fabmos.transport.gotm.Simulator(
    domain,
    FABM_CONFIG,
    gotm=GOTM_CONFIG,
    vertical_coordinates=fabmos.vertical_coordinates.GVC(
        domain.nz, ddl=0.5, ddu=0.75, Dgamma=40.0
    ),
)

# Meteorology
# fmt: off
METEO_FILE = f"era5{POSTFIX}.nc"
if not os.path.isfile(METEO_FILE):
    ds = pygetm.input.igotm.download_era5(
        domain.T.lon, domain.T.lat, 2005, dims=("y", "x"), logger=domain.logger
    )
    ds.to_netcdf(METEO_FILE)
sim.airsea.u10.set(fabmos.input.from_nc(METEO_FILE, "u10"), on_grid=True, climatology=True)
sim.airsea.v10.set(fabmos.input.from_nc(METEO_FILE, "v10"), on_grid=True, climatology=True)
sim.airsea.t2m.set(fabmos.input.from_nc(METEO_FILE, "t2m"), on_grid=True, climatology=True)
sim.airsea.d2m.set(fabmos.input.from_nc(METEO_FILE, "d2m"), on_grid=True, climatology=True)
sim.airsea.sp.set(fabmos.input.from_nc(METEO_FILE, "sp"), on_grid=True, climatology=True)
sim.airsea.tcc.set(fabmos.input.from_nc(METEO_FILE, "tcc"), on_grid=True, climatology=True)

# Temporary hack to ensure T&S are valid in cells that fall outside active domain,
# but where FABM/ECOSMO are still evaluated.
# This is needed to prevent carbonate chemistry errors.
sim.temp.values.fill(5.0)
sim.salt.values.fill(35.0)

# Initial conditions for temperature, salinity and biogeochemistry
GLODAP_FILE = "glodap_ip.nc"
assert os.path.isfile(GLODAP_FILE), "First run `preprocess.py`"
sim.temp.set(fabmos.input.from_nc(GLODAP_FILE, "ct"), on_grid=True)
sim.salt.set(fabmos.input.from_nc(GLODAP_FILE, "sa"), on_grid=True)
rho = fabmos.input.from_nc(GLODAP_FILE, "density") * 0.001
sim["ECO_no3"].set(fabmos.input.from_nc(GLODAP_FILE, "NO3") * rho * 6.625 * 12.01, on_grid=True)
sim["ECO_pho"].set(fabmos.input.from_nc(GLODAP_FILE, "PO4") * rho * 106.0 * 12.01, on_grid=True)
sim["ECO_sil"].set(fabmos.input.from_nc(GLODAP_FILE, "silicate") * rho * 6.625 * 12.01, on_grid=True)
sim["ECO_oxy"].set(fabmos.input.from_nc(GLODAP_FILE, "oxygen") * rho, on_grid=True)
sim["CO2_alk"].set(fabmos.input.from_nc(GLODAP_FILE, "TAlk") * rho, on_grid=True)
sim["CO2_dic"].set(fabmos.input.from_nc(GLODAP_FILE, "TCO2") * rho, on_grid=True)
# fmt: on

# Light attentuation
sim.radiation.jerlov_type = pygetm.radiation.Jerlov.Type_I

# Atmospheric pCO2
sim.fabm.get_dependency("mole_fraction_of_carbon_dioxide_in_air").set(375.0)

# Configure output
out = sim.output_manager.add_netcdf_file(
    f"gotm-arctic{POSTFIX}.nc", interval=datetime.timedelta(days=1)
)
out.request("temp", "salt", "nuh", "ice", *sim.fabm.state_variables)

# Simulate
sim.start(
    datetime.datetime(2005, 1, 1),
    3600.0,
    report=datetime.timedelta(days=10),
    report_totals=datetime.timedelta(days=365),
)
while sim.time < datetime.datetime(2007, 12, 31):
    sim.advance()
sim.finish()
