#!/usr/bin/env python3
"""
SeisComP XML Station Filter
---------------------------
A tool to filter stations from SeisComP XML files by including or excluding specific stations/networks.

Author: Mustafa COMOGLU
GitHub: https://github.com/comoglu
"""

import xml.etree.ElementTree as ET
import argparse
import sys
from typing import List, Set, Dict, Optional
import logging

class SeisComPStationFilter:
    """Filter stations from SeisComP XML files while preserving structure"""
    
    def __init__(self, mode='exclude'):
        self.stations = set()  # Set of tuples (network, station)
        self.networks = set()  # Set of network codes
        self.mode = mode  # 'exclude' or 'include'
        self.logger = self._setup_logger()
        
        # Define supported schema versions
        self.namespaces = {
            '0.13': 'http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.13',
            '0.12': 'http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.12',
            '0.11': 'http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.11',
            '0.10': 'http://geofon.gfz-potsdam.de/ns/seiscomp3-schema/0.10'
        }
        self.namespace = None  # Will be set when XML is loaded

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SeisComPStationFilter')
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def detect_namespace(self, root: ET.Element) -> Optional[str]:
        """Detect the SeisComP XML namespace from root element"""
        for version, uri in self.namespaces.items():
            if root.tag.startswith('{' + uri + '}'):
                self.namespace = uri
                ET.register_namespace('', uri)  # Register the detected namespace
                self.logger.info(f"Detected SeisComP schema version {version}")
                return uri
        return None

    def load_station_file(self, filename: str):
        """Load station/network patterns from file"""
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '.' in line:
                        network, station = line.split('.')
                        self.stations.add((network.strip(), station.strip()))
                    else:
                        self.networks.add(line.strip())
            
            mode_str = "include" if self.mode == 'include' else "exclude"
            self.logger.info(f"Loaded {mode_str} patterns: {len(self.stations)} stations, "
                           f"{len(self.networks)} networks")
            self.logger.debug(f"Networks to {mode_str}: {self.networks}")
            self.logger.debug(f"Stations to {mode_str}: {self.stations}")
        except Exception as e:
            self.logger.error(f"Error loading station file: {str(e)}")
            sys.exit(1)

    def should_remove(self, network: str, station: str) -> bool:
        """Determine if a station should be removed based on mode"""
        if self.mode == 'exclude':
            # In exclude mode, remove if matches exclusion patterns
            should_remove = (network in self.networks or 
                           (network, station) in self.stations)
        else:  # include mode
            # In include mode, remove if doesn't match inclusion patterns
            should_remove = not (network in self.networks or 
                               (network, station) in self.stations)
            
        if should_remove:
            self.logger.debug(f"Marking for removal: Network={network}, Station={station}")
        return should_remove

    def find_element_parent(self, root: ET.Element, element: ET.Element) -> Optional[ET.Element]:
        """Recursively find an element's parent"""
        for parent in root.iter():
            for child in list(parent):
                if child == element:
                    return parent
        return None

    def remove_element(self, root: ET.Element, element: ET.Element) -> bool:
        """Remove an element from its parent"""
        parent = self.find_element_parent(root, element)
        if parent is not None:
            parent.remove(element)
            return True
        return False

    def make_xpath(self, element_type: str) -> str:
        """Create proper xpath with namespace if available"""
        return f".//{{{self.namespace}}}{element_type}" if self.namespace else f".//{element_type}"

    def filter_xml(self, input_file: str, output_file: str):
        try:
            self.logger.debug(f"Parsing input file: {input_file}")
            tree = ET.parse(input_file)
            root = tree.getroot()
            
            # Detect and set namespace
            if not self.detect_namespace(root):
                self.logger.warning("No SeisComP namespace detected, proceeding without namespace")
            
            stats = {'removed': 0, 'kept': 0}
            elements_to_remove = []
            
            # Find all elements that might contain station information
            element_types = ['pick', 'amplitude', 'stationMagnitude', 'stationMagnitudeContribution']
            
            for elem_type in element_types:
                xpath = self.make_xpath(elem_type)
                for element in root.findall(xpath):
                    waveform_id = element.find(self.make_xpath('waveformID'))
                    if waveform_id is not None:
                        network = waveform_id.get('networkCode', '')
                        station = waveform_id.get('stationCode', '')
                        
                        self.logger.debug(f"Processing {elem_type}: Network={network}, Station={station}")
                        
                        if self.should_remove(network, station):
                            elements_to_remove.append((element, elem_type))
                            stats['removed'] += 1
                        else:
                            stats['kept'] += 1

            # Remove elements and their related references
            for element, elem_type in elements_to_remove:
                try:
                    # If it's a pick, remove arrival references to it
                    if elem_type == 'pick':
                        pick_id = element.get('publicID')
                        if pick_id:
                            # Find and remove arrivals that reference this pick
                            arrival_xpath = self.make_xpath('arrival')
                            pickid_xpath = self.make_xpath('pickID')
                            for arrival in root.findall(arrival_xpath):
                                pick_ref = arrival.find(pickid_xpath)
                                if pick_ref is not None and pick_ref.text == pick_id:
                                    self.remove_element(root, arrival)
                    
                    # If it's a stationMagnitude, remove its contributions
                    elif elem_type == 'stationMagnitude':
                        mag_id = element.get('publicID')
                        if mag_id:
                            contrib_xpath = self.make_xpath('stationMagnitudeContribution')
                            magid_xpath = self.make_xpath('stationMagnitudeID')
                            for contrib in root.findall(contrib_xpath):
                                mag_ref = contrib.find(magid_xpath)
                                if mag_ref is not None and mag_ref.text == mag_id:
                                    self.remove_element(root, contrib)
                    
                    # Remove the element itself
                    self.remove_element(root, element)
                    
                except Exception as e:
                    self.logger.warning(f"Error removing {elem_type}: {str(e)}")
                    continue

            # Write the filtered XML
            self.logger.debug(f"Writing output to: {output_file}")
            tree.write(output_file, 
                      encoding='UTF-8', 
                      xml_declaration=True,
                      method='xml')
            
            mode_str = "included" if self.mode == 'include' else "excluded"
            self.logger.info(f"Processing complete: {stats['removed']} {mode_str}, "
                           f"{stats['kept']} kept")
            
        except Exception as e:
            self.logger.error(f"Error processing XML file: {str(e)}")
            import traceback
            self.logger.debug(traceback.format_exc())
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Filter stations from SeisComP XML files')
    
    # Create mutually exclusive group for include/exclude
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--exclude', help='File containing stations/networks to exclude')
    group.add_argument('--include', help='File containing stations/networks to include (excludes all others)')
    
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('input', help='Input SeisComP XML file')
    parser.add_argument('output', help='Output filtered XML file')
    
    args = parser.parse_args()
    
    # Determine mode and filename based on which argument was provided
    mode = 'include' if args.include else 'exclude'
    filename = args.include if args.include else args.exclude
    
    filter = SeisComPStationFilter(mode=mode)
    
    if args.debug:
        filter.logger.setLevel(logging.DEBUG)
    
    filter.load_station_file(filename)
    filter.filter_xml(args.input, args.output)

if __name__ == '__main__':
    main()
