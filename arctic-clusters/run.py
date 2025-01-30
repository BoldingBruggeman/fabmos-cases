import datetime
import os.path

import netCDF4
import numpy as np

import fabmos
import fabmos.transport.gotm
import fabmos.input.cluster
import pygetm

DOMAIN_FILE = "smoothed_ecoregion_6_iteration.nc"
SPLIT_CLUSTERS = False  # True


def get_domain(cluster: bool) -> fabmos.domain.Domain:
    # Estimate hydrodynamic bottom roughness from HYCOM's drag
    C_D = 0.003  # drag coefficient
    h_bot = 10.0  # thickness of bottom layer (HYCOM manual section 4.1.2)
    z0b = 0.5 * h_bot / (np.exp(0.4 / np.sqrt(C_D)) - 1.0)

    with netCDF4.Dataset(DOMAIN_FILE) as nc:
        depth = nc["depth"]
        ny, nx = depth.shape
        masked = np.ma.getmaskarray(depth)
        domain = fabmos.domain.Domain(
            nx,
            ny,
            lon=nc["longitude"],
            lat=nc["latitude"],
            H=depth,
            z0=z0b,
            mask=np.where(masked, 0, 1),
            coordinate_type=fabmos.CoordinateType.IJ,
        )
        clusters = np.ma.array(nc["ecoregion"], mask=masked)
    if not cluster:
        return domain
    if SPLIT_CLUSTERS:
        clusters = fabmos.input.cluster.split(clusters)
    return fabmos.domain.compress_clusters(domain, clusters)


if __name__ == "__main__":
    domain = get_domain(cluster=True)

    sim = fabmos.transport.gotm.Simulator(
        domain,
        fabm="fabm.yaml",
        gotm="gotm.yaml",
        ice=pygetm.ice.Prescribed(),
        vertical_coordinates=fabmos.vertical_coordinates.GVC(
            nz=50, ddl=0.5, ddu=0.75, Dgamma=40.0
        ),
        connectivity=fabmos.input.from_nc("connections.nc", "exchange"),
    )

    # Meteorology
    # fmt: off
    METEO_FILE = "era5_????.nc"
    sim.airsea.u10.set(fabmos.input.from_nc(METEO_FILE, "u10"), on_grid=True)
    sim.airsea.v10.set(fabmos.input.from_nc(METEO_FILE, "v10"), on_grid=True)
    sim.airsea.t2m.set(fabmos.input.from_nc(METEO_FILE, "t2m") - 273.15, on_grid=True)
    sim.airsea.d2m.set(fabmos.input.from_nc(METEO_FILE, "d2m") - 273.15, on_grid=True)
    sim.airsea.sp.set(fabmos.input.from_nc(METEO_FILE, "sp"), on_grid=True)
    sim.airsea.tcc.set(fabmos.input.from_nc(METEO_FILE, "tcc"), on_grid=True)
    sim.ice.ice.set(fabmos.input.from_nc(METEO_FILE, "siconc"), on_grid=True)

    # Ensure T&S are valid in cells that fall outside active domain,
    # but where FABM/ECOSMO are still evaluated (e.g. inactive part of last subdomain)
    # This is needed to prevent carbonate chemistry errors.
    sim.temp.values.fill(5.0)
    sim.salt.values.fill(35.0)

    # Initial conditions for temperature, salinity and biogeochemistry
    GLODAP_FILE = "glodap_ip.nc"
    assert os.path.isfile(GLODAP_FILE), "First run `preprocess.py`"
    sim.temp.set(fabmos.input.from_nc(GLODAP_FILE, "ct"), on_grid=True)
    sim.salt.set(fabmos.input.from_nc(GLODAP_FILE, "sa"), on_grid=True)
    rho = fabmos.input.from_nc(GLODAP_FILE, "density") * 0.001  # in kg L-1
    sim["ECO_no3"].set(fabmos.input.from_nc(GLODAP_FILE, "NO3") * rho * 6.625 * 12.01, on_grid=True)
    sim["ECO_pho"].set(fabmos.input.from_nc(GLODAP_FILE, "PO4") * rho * 106.0 * 12.01, on_grid=True)
    sim["ECO_sil"].set(fabmos.input.from_nc(GLODAP_FILE, "silicate") * rho * 6.625 * 12.01, on_grid=True)
    sim["ECO_oxy"].set(fabmos.input.from_nc(GLODAP_FILE, "oxygen") * rho, on_grid=True)
    sim["CO2_TA"].set(fabmos.input.from_nc(GLODAP_FILE, "TAlk") * rho, on_grid=True)
    sim["CO2_c"].set(fabmos.input.from_nc(GLODAP_FILE, "TCO2") * rho, on_grid=True)
    # fmt: on

    # Light attentuation
    sim.radiation.jerlov_type = pygetm.radiation.Jerlov.Type_I

    # Atmospheric pCO2
    sim.fabm.get_dependency("mole_fraction_of_carbon_dioxide_in_air").set(375.0)

    # Configure output
    out = sim.output_manager.add_netcdf_file(
        "gotm-arctic.nc", interval=datetime.timedelta(days=1), sync_interval=None
    )
    out.request("temp", "salt", "nuh", "ice", *sim.fabm.state_variables)

    # Simulate
    sim.start(
        datetime.datetime(2015, 1, 1),
        3600.0,
        report=datetime.timedelta(days=10),
        report_totals=datetime.timedelta(days=365),
    )
    while sim.time < datetime.datetime(2020, 12, 31):
        sim.advance()
    sim.finish()
