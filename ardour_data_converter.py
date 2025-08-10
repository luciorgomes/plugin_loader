#!/usr/bin/env python3
"""
Ardour Plugin XML to JSON Converter
Parses Ardour plugin scan log XML and extracts Author/Factory and Category/Type information
"""
import os
import xml.etree.ElementTree as ET
import json
from urllib.parse import urlparse

ARDOUR_SCAN_LOG_FILE = '/.config/ardour8/plugin_metadata/scan_log'

def parse_lv2_plugin(scan_log):
    """Parse LV2 plugin information from scan log."""

    scan_log_list = scan_log.split('\n')

    plugin_info = {
        'type': 'LV2',
        'author': None,
        'category': None,
        'name': None,
        'uri': None
    }

    for line in scan_log_list:
        line = line.strip()
        # print(line)
        if line.startswith('URI:'):
            plugin_info['uri'] = line.replace('URI: ', '')
            # Extract author from URI domain
            parsed = urlparse(plugin_info['uri'])
            if parsed.netloc:
                plugin_info['author'] = parsed.netloc
        elif "LV2 Category" in line:
            category = line.replace("LV2 Category: '", "").replace("'", "")
            plugin_info['category'] = category
    # print(plugin_info)
    return plugin_info


def parse_vst3_plugin(scan_log):
    """Parse VST3 plugin information from scan log."""
    scan_log = scan_log.replace('[Info]: ','')
    scan_log_list = scan_log.split('\n')
    plugin_info = {
        'type': 'VST3',
        'author': None,
        'category': None,
        'name': None,
        'vendor': None
    }

    # Look for FactoryInfo line
    for line in scan_log_list:
        line = line.strip()
        if line.startswith("Found Plugin: "):
            plugin_info['name'] = line.replace("Found Plugin: ", "")
        elif '<VST3Info' in line:
            # print(line)
            plugin_info['category'] = line.split('category="')[1].split('"')[0]
            plugin_info['vendor'] = line.split('vendor="')[1].split('"')[0]

    return plugin_info


def parse_vst2_plugin(scan_log, plugin_type):
    """Parse VST2/LXVST plugin information from scan log."""
    scan_log = scan_log.replace('[Info]: ', '')
    scan_log_list = scan_log.split('\n')
    plugin_info = {
        'type': plugin_type,
        'author': None,
        'category': None,
        'name': None,
        'creator': None
    }

    # Look for plugin name in Found Plugin line
    for line in scan_log_list:
        line = line.strip()
        if '<VST2Info' in line:
            plugin_info['name'] = line.split('name="')[1].split('"')[0]
            plugin_info['category'] = line.split('category="')[1].split('"')[0]
            plugin_info['creator'] = line.split('creator="')[1].split('"')[0]

    return plugin_info


def parse_ardour_plugin_xml(xml_content):
    """Parse Ardour plugin scan XML and extract plugin information."""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        # Try to wrap in root element if it's fragment
        try:
            root = ET.fromstring(f"<root>{xml_content}</root>")
        except ET.ParseError:
            raise ValueError(f"Invalid XML content: {e}")

    plugins = []

    # Find all PluginScanLogEntry elements
    entries = root.findall('.//PluginScanLogEntry')
    if not entries:
        # Try direct children if wrapped in root
        entries = root.findall('PluginScanLogEntry')

    for entry in entries:
        plugin_type = entry.get('type')
        scan_log = entry.get('scan-log', '')
        path = entry.get('path', '')
        scan_result = entry.get('scan-result', '0')

        # Skip failed scans (non-zero scan-result usually indicates issues)
        if scan_result != '0':
            continue

        plugin_info = None

        if plugin_type == 'LV2':
            plugin_info = parse_lv2_plugin(scan_log)
        elif plugin_type == 'VST3':
            plugin_info = parse_vst3_plugin(scan_log)
        elif plugin_type in ['VST2', 'LXVST']:
            plugin_info = parse_vst2_plugin(scan_log, plugin_type)

        if plugin_info:
            plugin_info['path'] = path
            plugin_info['scan_result'] = scan_result

            # Clean up empty values
            for key, value in plugin_info.items():
                if value == '':
                    plugin_info[key] = None

            plugins.append(plugin_info)

    return plugins


def convert_xml_to_json(xml_content, output_file=None, pretty_print=True):
    """Convert Ardour plugin XML to JSON format."""
    plugins = parse_ardour_plugin_xml(xml_content)

    # Create structured output
    result = {
        'plugins': plugins,
        'summary': {
            'total_plugins': len(plugins),
            'by_type': {}
        }
    }

    # Count by type
    for plugin in plugins:
        plugin_type = plugin['type']
        if plugin_type not in result['summary']['by_type']:
            result['summary']['by_type'][plugin_type] = 0
        result['summary']['by_type'][plugin_type] += 1

    # Convert to JSON
    json_output = json.dumps(result, indent=2 if pretty_print else None, ensure_ascii=False)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_output)
        print(f"JSON output saved to: {output_file}")

    return json_output

def main():
    home_directory = os.path.expanduser("~")
    # print(home_directory)
    path_ardour_scan_log = home_directory + ARDOUR_SCAN_LOG_FILE
    if os.path.exists(path_ardour_scan_log):
        with open(path_ardour_scan_log, 'r') as f:
            xml_content = f.read()
        json_output = convert_xml_to_json(xml_content, 'plugins_ardour.json')


# Example usage and test with the provided data
if __name__ == "__main__":
    main()
