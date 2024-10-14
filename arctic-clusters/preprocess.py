import os.path

import numpy as np
import netCDF4

import fabmos

GLODAP_FILE = "glodap.nc"

assert os.path.isfile(
    GLODAP_FILE
), f"First download GLODAP with `python -m pygetm.input.glodap {GLODAP_FILE}`"

with netCDF4.Dataset("smoothed_ecoregion_6_iteration.nc") as nc:
    lon = nc["longitude"][:, :]
    lat = nc["latitude"][:, :]


def get_initial_conditions(lon: np.ndarray, lat: np.ndarray):
    with netCDF4.Dataset(GLODAP_FILE) as nc:
        target_variables = [n for n, v in nc.variables.items() if v.ndim == 3]
    lat_glodap = np.minimum(lat, 87.5)
    with netCDF4.Dataset("glodap_ip.nc", "w") as ncbath:
        for name in target_variables:
            values = fabmos.input.from_nc(GLODAP_FILE, name)
            values = fabmos.input.limit_region(
                values, -180.0, 180.0, -80.0, 89.5, periodic_lon=True
            )
            if not ncbath.variables:
                ncbath.createDimension("x", lon.shape[1])
                ncbath.createDimension("y", lon.shape[0])
                ncbath.createVariable("lon", float, ("y", "x"))[:, :] = lon
                ncbath.createVariable("lat", float, ("y", "x"))[:, :] = lat
                glodap_depth = values.coords["Depth"]
                ncbath.createDimension("depth", len(glodap_depth))
                ncdepth = ncbath.createVariable("depth", float, ("depth",))
                ncdepth[:] = glodap_depth
                ncdepth.positive = glodap_depth.attrs["positive"]
            values_ip = fabmos.input.horizontal_interpolation(values, lon, lat_glodap)
            values_ip = np.asarray(values_ip)
            ncvar = ncbath.createVariable(
                name, float, ("depth", "y", "x"), fill_value=-1
            )
            ncvar.long_name = values.long_name
            ncvar.units = values.units
            ncvar[:, :, :] = values_ip


if __name__ == "__main__":
    get_initial_conditions(lon, lat)
