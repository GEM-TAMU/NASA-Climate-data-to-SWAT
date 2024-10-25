# Climate Data Downloader and SWAT Converter

This project provides a Python-based tool to download climate data from NASA Earth Exchange (NEX), process it, and convert it into a format suitable for use with the Soil and Water Assessment Tool (SWAT). The tool is implemented as a class that enables users to specify download parameters, fetch data in NetCDF format from specified models and scenarios, and save it in text format for SWAT compatibility.

## Features

- **Download climate data** from NASA Earth Exchange based on specified variables, models, and SSP scenarios.
- **Process NetCDF files** to extract variable-specific data over time.
- **Convert data into SWAT-compatible format** for seamless integration with SWAT models.

## Project Structure

```plaintext
ClimateDataDownloader/
│
├── NASA_earth_exchange.py         # Main script containing the ClimateDataDownloader class
├── environment.yml       # Conda environment file with dependencies
├── README.md             # Project overview and usage instructions
└── data/                 # Directory for storing downloaded data (user-defined)
```

## Setup and Installation

### Prerequisites
- [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) for environment management.

### Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/GEM-TAMU/NASA-Climate-data-to-SWAT.git
   cd NASA-Climate-data-to-SWAT
   ```

2. Create the Conda environment using `environment.yml`:
   ```bash
   conda env create -f environment.yml
   conda activate NASA_earth_exchange
   ```

### Environment Details
The `environment.yml` file specifies the following dependencies:
   ```yaml
   name: NASA_earth_exchange
   channels:
     - conda-forge
   dependencies:
     - python=3.8
     - geopandas
     - numpy
     - pandas
     - netCDF4
     - wget
   ```

## Usage

### Step 1: Define Download Parameters
In `downloader.py`, define the parameters for your download:

- `working_dir`: Directory for storing downloaded and processed data.
- `dataset_name`: Dataset name (e.g., `"GDDP-CMIP6"`).
- `model_name`: Climate model to use (e.g., `"ACCESS-CM2"`).
- `ssp_of_interest`: Scenarios of interest, such as `["historical", "ssp126", "ssp245", "ssp370", "ssp585"]`.
- `meta_data_format`: Metadata format, e.g., `"r1i1p1f1"`.
- `variables_of_interest`: Climate variables to download, such as `["hurs", "huss", "pr", "rlds", "rsds", "sfcWind", "tas", "tasmax", "tasmin"]`.
- `versions_avail`: Available data versions, e.g., `["", "_v1.1", "_v1.2"]`.

### Step 2: Instantiate the Downloader Class
Import and initialize the `ClimateDataDownloader` class with your defined parameters:
   ```python
   from downloader import ClimateDataDownloader

   working_dir = "/path/to/working_directory"
   dataset_name = "GDDP-CMIP6"
   model_name = "ACCESS-CM2"
   ssp_of_interest = ["historical", "ssp126", "ssp245", "ssp370", "ssp585"]
   meta_data_format = "r1i1p1f1"
   variables_of_interest = ["hurs", "huss", "pr", "rlds", "rsds", "sfcWind", "tas", "tasmax", "tasmin"]
   versions_avail = ["", "_v1.1", "_v1.2"]

   downloader = ClimateDataDownloader(
       working_dir,
       dataset_name,
       model_name,
       ssp_of_interest,
       meta_data_format,
       variables_of_interest,
       versions_avail
   )
   ```

### Step 3: Download NetCDF Files
To download all specified NetCDF files, call the `download_all()` method. This method retries downloads up to three times in case of errors, using the most recent data version available.
   ```python
   downloader.download_all()
   ```

### Step 4: Process and Convert Data to SWAT Format
To process the downloaded NetCDF files and convert them into a SWAT-compatible format, call `convert_to_swat()`. This method processes each climate variable, fills missing dates, and converts temperature units to Celsius.
   ```python
   downloader.convert_to_swat()
   ```

### Example
   ```python
   # Example usage
   if __name__ == "__main__":
       working_dir = "/home/arvinder/Downloads/HTT_L07"
       dataset_name = "GDDP-CMIP6"
       model_name = "ACCESS-CM2"
       ssp_of_interest = ["historical", "ssp126", "ssp245", "ssp370", "ssp585"]
       meta_data_format = "r1i1p1f1"
       variables_of_interest = ["hurs", "huss", "pr", "rlds", "rsds", "sfcWind", "tas", "tasmax", "tasmin"]
       versions_avail = ["", "_v1.1", "_v1.2"]

       downloader = ClimateDataDownloader(
           working_dir,
           dataset_name,
           model_name,
           ssp_of_interest,
           meta_data_format,
           variables_of_interest,
           versions_avail
       )

       # Download netCDF files
       downloader.download_all()

       # Process netCDF files and convert to SWAT format
       downloader.convert_to_swat()
   ```

## Notes

- **Data Source**: The climate data is sourced from NASA Earth Exchange (NEX), and the downloaded files are in NetCDF format.
- **Error Handling**: The script includes basic error handling, with retries and alternative versions in case of HTTP errors.
- **SWAT Compatibility**: The script converts NetCDF data into daily temperature and radiation values compatible with SWAT, adjusting units where necessary.

## Troubleshooting

- **HTTP Errors**: If repeated 504 Gateway Timeout errors occur, ensure your internet connection is stable, or check for potential issues with the data server.
- **Dependencies**: If `geopandas` or `netCDF4` raise errors, confirm they are correctly installed using Conda, as these libraries may have dependencies on system libraries.
