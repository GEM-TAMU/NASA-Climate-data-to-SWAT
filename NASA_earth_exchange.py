from urllib.error import HTTPError
import time
import geopandas as gpd
import os
import numpy as np
import wget
import pandas as pd
import netCDF4 as nc

class ClimateDataDownloader:
    def __init__(self, working_dir, dataset_name, model_name, ssp_of_interest,
                 meta_data_format, variables_of_interest, versions_avail):
        self.working_dir = working_dir
        self.dataset_name = dataset_name
        self.model_name = model_name
        self.ssp_of_interest = ssp_of_interest
        self.meta_data_format = meta_data_format
        self.variables_of_interest = variables_of_interest
        self.versions_avail = versions_avail
        self.west, self.south, self.east, self.north = self._get_bounds()
        self.dates_historical = np.arange(1950, 2015)
        self.dates_projected = np.arange(2015, 2101)
        self.max_retries = 3
        self.timeout = 10

    def _get_bounds(self):
        for file in os.listdir(self.working_dir):
            if file.endswith(".shp"):
                shp_file_path = os.path.join(working_dir, file)
                gdf = gpd.read_file(shp_file_path)
                return gdf.total_bounds

    def download_nc_file(self, vers, var, ssp, date, save_folder):
        filename = f"{var}_day_{self.model_name}_{ssp}_{self.meta_data_format}_gn_{str(date)}{vers}.nc"
        save_path = os.path.join(save_folder, filename)

        if not os.path.exists(save_path):
            wget_string = (
                f"https://ds.nccs.nasa.gov/thredds/ncss/grid/AMES/NEX/{self.dataset_name}/{self.model_name}/{ssp}/"
                f"{self.meta_data_format}/{var}/{filename}?var={var}&north={self.north}&west={self.west}&east={self.east}&south={self.south}"
                f"&horizStride=1&time_start={date}-01-01T12:00:00Z"
                f"&time_end={date}-12-31T12:00:00Z&&&accept=netcdf3&addLatLon=true"
            )
            wget.download(wget_string, save_path)

    def download_all(self):
        for ssp in self.ssp_of_interest:
            dates = self.dates_historical if ssp == "historical" else self.dates_projected

            for var in self.variables_of_interest:
                save_folder = f'{self.working_dir}/{self.dataset_name}/{self.model_name}/{ssp}/{self.meta_data_format}/{var}'
                os.makedirs(save_folder, exist_ok=True)

                for date in dates:
                    vers = self.versions_avail[-1]  # Start with the last version
                    for attempt in range(self.max_retries):
                        try:
                            self.download_nc_file(vers, var, ssp, date, save_folder)
                            print(f"Download Successful for Dataset: {self.dataset_name}, Model: {self.model_name}, "
                                  f"ssp: {ssp}, Variable: {var}, Version: {vers}, Date:{date}")
                            break
                        except HTTPError as e:
                            if e.code == 504 and attempt < self.max_retries - 1:
                                print(
                                    f"Gateway Timeout (504) on attempt {attempt + 1} for version {vers}. Retrying in {self.timeout} seconds...")
                                time.sleep(self.timeout)
                            else:
                                # Try the next version
                                if vers == self.versions_avail[2]:
                                    vers = self.versions_avail[1]
                                elif vers == self.versions_avail[1]:
                                    vers = self.versions_avail[0]
                                else:
                                    print(f"All versions failed to download for {var} on {date}.")
                                    break

    def process_netcdf(self):
        data_dir = os.path.join(self.working_dir, "GDDP-CMIP6/ACCESS-CM2")
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)
        data_dict_hist = {}
        data_dict_ssp = {}
        for ssp in sorted(os.listdir(data_dir)):
            metadata_pth = os.path.join(data_dir, ssp)
            data_dict_proj = {}
            for metadata_info in sorted(os.listdir(metadata_pth)):
                var_path = os.path.join(metadata_pth, metadata_info)

                for var in sorted(os.listdir(var_path)):
                    climate_info_path = os.path.join(var_path, var)
                    df = pd.DataFrame()
                    first_time = True
                    for data_file_nm in sorted(os.listdir(climate_info_path)):

                        data_file_pth = os.path.join(climate_info_path, data_file_nm)
                        data_file = nc.Dataset(data_file_pth, mode='r')

                        num_days = data_file[var].shape[0]
                        var_data = data_file[var][:].reshape(num_days, -1)

                        latitudes = data_file.variables['lat'][:]
                        longitudes = data_file.variables['lon'][:]
                        time_data = data_file.variables['time'][:]
                        time_units = data_file.variables['time'].units

                        time_dates = nc.num2date(time_data, units=time_units)

                        # Create a list of lat-lon pair names for the columns
                        lat_lon_str = []
                        lat_lon_pairs = []
                        for lat in latitudes:
                            for lon in longitudes:
                                lat_lon_str.append(f"{int(lat * 1000)}_{int(lon * 1000)}")
                                lat_lon_pairs.append([lat, lon])
                        if first_time:
                            df = pd.DataFrame(var_data, columns=lat_lon_str)
                            df['time'] = time_dates
                            df.set_index('time', inplace=True)
                            first_time = False
                        else:
                            temp_df = pd.DataFrame(var_data, columns=lat_lon_str)
                            temp_df['time'] = time_dates
                            temp_df.set_index('time', inplace=True)
                            df = pd.concat([df, temp_df])

                    if ssp == "historical":
                        data_dict_hist[var] = df
                    else:
                        data_dict_proj[var] = df

            if not ssp == "historical":
                data_dict_ssp[ssp] = data_dict_proj
        return data_dict_ssp, data_dict_hist, lat_lon_pairs

    def convert_to_swat(self):
        data_dict_ssp, data_dict_hist, lat_lon_pairs = self.process_netcdf()
        for ssp, dicts in data_dict_ssp.items():
            save_folder = f'{self.working_dir}/SWAT_files'
            os.makedirs(save_folder, exist_ok=True)

            projected_dict = dicts
            tasmax_df = pd.DataFrame()
            tasmin_df = pd.DataFrame()
            for var, hist_df in data_dict_hist.items():
                names = hist_df.columns.tolist()

                names_temp = ["temp_max_min" + "_" + item for item in names]
                names = [var + "_" + item for item in names]
                if var == "tasmin" or var == "tasmax":
                    names = names_temp

                ids = list(range(1, len(names) + 1))
                elevation = [100] * len(names)
                df_info = pd.DataFrame({
                    'ID': ids,
                    'NAME': names,
                    'LAT': [lat for lat, lon in lat_lon_pairs],
                    'LONG': [lon for lat, lon in lat_lon_pairs],
                    'ELEVATION': elevation
                })

                if var == "tasmin" or var == "tasmax":
                    save_path = os.path.join(save_folder, "temp_max_min" + ".txt")
                else:
                    save_path = os.path.join(save_folder, var + ".txt")

                df_info.to_csv(save_path, index=False)

                projected_df = projected_dict[var]
                df_data = pd.concat([hist_df, projected_df])
                df_data.index = pd.to_datetime(df_data.index.astype(str))
                full_date_range = pd.date_range(start=df_data.index.min(), end=df_data.index.max(), freq='D')
                missing_dates = full_date_range.difference(df_data.index)
                for date in missing_dates:
                    print(f"Missing dates for ssp: {ssp}, variable: {var}: {date.date()}")

                df_data = df_data.reindex(full_date_range, fill_value=-99.0)
                if var in ["tas", "tasmax", "tasmin"]:
                    df_data = df_data - 273.15  # convert to degrees celsius

                df_data = df_data.round(3)
                data_save_pth = os.path.join(save_folder, ssp)
                os.makedirs(data_save_pth, exist_ok=True)
                date_string = df_data.index.min().strftime("%Y%m%d")

                if var == "tasmax":
                    tasmax_df = df_data
                elif var == "tasmin":
                    tasmin_df = df_data
                else:
                    if var in ["rlds", "rsds"]:
                        df_data = df_data * 0.0036  # Convert to MJ/m^2
                    for i, column in enumerate(df_data.columns):
                        file_path = f'{data_save_pth}/{names[i]}.txt'
                        with open(file_path, 'w') as f:
                            f.write(date_string + '\n')  # Write the date as the first line
                            df_data[column].to_csv(f, index=False,
                                                   header=False)  # Write the DataFrame column to the file

            for i, column in enumerate(tasmax_df.columns):
                # Create a combined DataFrame for each corresponding pair of columns
                combined_df = pd.DataFrame({
                    'tmax': tasmax_df[column],
                    'tmin': tasmin_df[column]
                })

                file_path = f'{data_save_pth}/{names[i]}.txt'
                with open(file_path, 'w') as f:
                    f.write(date_string + '\n')  # Write the date as the first line
                    combined_df.to_csv(f, index=False, header=False)  # Write the DataFrame column to the file

# Example usage
if __name__ == "__main__":
    working_dir = "D:\\Projects\\Watersheds\\Ghana\\Analysis\\climate_scenarios"
    dataset_name = "GDDP-CMIP6"
    model_name = "ACCESS-CM2"
    ssp_of_interest = ["historical", "ssp126", "ssp245", "ssp370", "ssp585"]
    meta_data_format = "r1i1p1f1"
    variables_of_interest = ["hurs", "huss", "pr", "rlds", "rsds", "sfcWind", "tas", "tasmax", "tasmin"]
    versions_avail = ["", "_v1.1", "_v1.2"]

    # Instantiate the object
    downloader = ClimateDataDownloader(working_dir, dataset_name, model_name,
                                        ssp_of_interest, meta_data_format,
                                        variables_of_interest, versions_avail)
    # Download netcdf files
    downloader.download_all()

    # Process netcdf and convert to SWAT format
    downloader.convert_to_swat()