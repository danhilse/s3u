"""
Output formatters for different output types (JSON, XML, HTML, CSV).
"""

import json
import xml.dom.minidom
from datetime import datetime

def format_output(urls, objects, output_format):
    """
    Format URLs and object metadata according to the specified format.
    
    Args:
        urls (list): List of URLs
        objects (list): List of objects with metadata
        output_format (str): Format for output: 'array', 'json', 'xml', 'html', or 'csv'
        
    Returns:
        str: Formatted output string
    """
    format_functions = {
        'array': format_array,
        'json': format_json,
        'xml': format_xml,
        'html': format_html,
        'csv': format_csv
    }
    
    # Use the appropriate formatter or default to array
    formatter = format_functions.get(output_format, format_array)
    return formatter(urls, objects)

def format_array(urls, objects):
    """
    Format URLs as a JSON array.
    
    Args:
        urls (list): List of URLs
        objects (list): List of objects with metadata (not used)
        
    Returns:
        str: JSON array of URLs
    """
    return "[" + ", ".join([f'"{url}"' for url in urls]) + "]"

def format_json(urls, objects):
    """
    Format objects as a JSON object with metadata.
    
    Args:
        urls (list): List of URLs (not used)
        objects (list): List of objects with metadata
        
    Returns:
        str: JSON formatted metadata
    """
    return json.dumps({
        "folder": objects[0]['s3_path'].split('/')[0] if objects else "",
        "count": len(objects),
        "timestamp": datetime.now().isoformat(),
        "files": objects
    }, indent=2)

def format_xml(urls, objects):
    """
    Format objects as an XML document.
    
    Args:
        urls (list): List of URLs (not used)
        objects (list): List of objects with metadata
        
    Returns:
        str: XML formatted metadata
    """
    doc = xml.dom.minidom.getDOMImplementation().createDocument(None, "files", None)
    root = doc.documentElement
    
    # Add metadata
    folder_elem = doc.createElement("folder")
    folder_elem.appendChild(doc.createTextNode(objects[0]['s3_path'].split('/')[0] if objects else ""))
    root.appendChild(folder_elem)
    
    count_elem = doc.createElement("count")
    count_elem.appendChild(doc.createTextNode(str(len(objects))))
    root.appendChild(count_elem)
    
    timestamp_elem = doc.createElement("timestamp")
    timestamp_elem.appendChild(doc.createTextNode(datetime.now().isoformat()))
    root.appendChild(timestamp_elem)
    
    # Add files
    files_elem = doc.createElement("items")
    root.appendChild(files_elem)
    
    for obj in objects:
        file_elem = doc.createElement("file")
        
        for key, value in obj.items():
            elem = doc.createElement(key)
            elem.appendChild(doc.createTextNode(str(value)))
            file_elem.appendChild(elem)
        
        files_elem.appendChild(file_elem)
    
    return doc.toprettyxml(indent="  ")

def format_html(urls, objects):
    """
    Format objects as an HTML document with links.
    
    Args:
        urls (list): List of URLs (not used)
        objects (list): List of objects with metadata
        
    Returns:
        str: HTML document with links
    """
    html = "<html>\n<head>\n  <title>File Links</title>\n</head>\n<body>\n"
    html += f"  <h1>Files in {objects[0]['s3_path'].split('/')[0] if objects else ''}</h1>\n"
    html += "  <p>Generated on " + datetime.now().isoformat() + "</p>\n"
    html += "  <ul>\n"
    
    for obj in objects:
        html += f'    <li><a href="{obj["url"]}" target="_blank">{obj["filename"]}</a> ({obj["size"]} bytes)</li>\n'
    
    html += "  </ul>\n</body>\n</html>"
    return html

def format_csv(urls, objects):
    """
    Format objects as a CSV document.
    
    Args:
        urls (list): List of URLs (not used)
        objects (list): List of objects with metadata
        
    Returns:
        str: CSV formatted metadata
    """
    csv = "url,filename,s3_path,size,last_modified,type\n"
    
    for obj in objects:
        csv += f"{obj['url']},{obj['filename']},{obj['s3_path']},{obj['size']},{obj['last_modified']},{obj['type']}\n"
    
    return csv