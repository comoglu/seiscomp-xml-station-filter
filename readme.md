# SeisComP XML Station Filter

A Python tool to filter stations from SeisComP XML files by including or excluding specific stations and networks.

## Features

- Filter SeisComP XML files by excluding specific stations/networks
- Filter SeisComP XML files by including only specific stations/networks
- Support for multiple SeisComP schema versions (0.10 - 0.13)
- Automatic schema version detection
- Handles related element cleanup (arrivals, station magnitudes, etc.)
- Preserves XML structure and namespaces

## Installation

1. Clone the repository:
```bash
git clone https://github.com/comoglu/seiscomp-xml-station-filter.git
cd seiscomp-xml-station-filter
```

2. Ensure you have Python 3.7 or newer installed.

## Usage

The script can be used in two modes: exclude mode (remove specific stations) or include mode (keep only specific stations).

### Basic Usage

```bash
# Exclude mode - remove specified stations
python3 station-filter.py --exclude stations.txt input.xml output.xml

# Include mode - keep only specified stations
python3 station-filter.py --include stations.txt input.xml output.xml

# Enable debug output
python3 station-filter.py --debug --exclude stations.txt input.xml output.xml
```

### Station List File Format

The station list file (for both include and exclude modes) uses a simple format:

```text
# Comments start with #
# Network codes to include/exclude
GE
IU

# Specific stations to include/exclude (network.station format)
AU.ARMA
IU.MBWA
```

- Lines starting with # are treated as comments
- Network codes alone will include/exclude all stations from that network
- Network.Station format will include/exclude specific stations

### Examples

1. Exclude all stations from the IU network:
```text
# exclude.txt
IU
```
```bash
python3 station-filter.py --exclude exclude.txt input.xml output.xml
```

2. Keep only specific stations:
```text
# include.txt
AU.ARMA
AU.EIDS
GE.BFO
```
```bash
python3 station-filter.py --include include.txt input.xml output.xml
```

## Features in Detail

The tool will:
- Remove specified stations from:
  - Picks
  - Amplitudes
  - Station Magnitudes
  - Station Magnitude Contributions
- Clean up related elements:
  - Remove arrivals that reference excluded picks
  - Remove station magnitude contributions for excluded stations
- Preserve XML structure and namespaces
- Support multiple SeisComP schema versions

## Debugging

Use the --debug flag for detailed output:
```bash
python3 station-filter.py --debug --exclude stations.txt input.xml output.xml
```

This will show:
- Schema version detection
- Station processing details
- Element removal operations
- Final statistics

## Schema Support

The tool supports the following SeisComP schema versions:
- 0.13 (latest)
- 0.12
- 0.11
- 0.10

Schema version is automatically detected from the input file.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Mustafa COMOGLU  
GitHub: [@comoglu](https://github.com/comoglu)
