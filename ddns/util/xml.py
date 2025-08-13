# -*- coding:utf-8 -*-
def _to_xml(obj, tag):
    # type: (object, str) -> str
    """Convert object to XML element"""
    if isinstance(obj, dict):
        if not obj:
            return "<{0}></{0}>".format(tag)
        content = "".join(_to_xml(v, k) for k, v in obj.items())
        return "<{0}>{1}</{0}>".format(tag, content)
    elif isinstance(obj, (list, tuple)):
        return "".join(_to_xml(item, tag) for item in obj)
    else:
        return "<{0}>{1}</{0}>".format(tag, obj)


def dict_to_xml(data, root, namespace=None, encoding="UTF-16", version="1.0", root_version=None):
    # type: (dict, str, str | None, str, str, str | None) -> str
    """
    Convert dictionary to XML document

    Args:
        data (dict): Dictionary to convert
        root(str): Root element tag name (optional)
        namespace (str): XML namespace (optional)
        encoding (str): XML encoding (default: UTF-16)
        version (str): XML version (default: 1.0)
        root_version (str): Version attribute for root element (optional)

    Returns:
        str: XML document as string
    """

    # Build XML declaration and content
    xml_header = '<?xml version="{0}" encoding="{1}"?>'.format(version, encoding)
    # Handle different root scenarios
    # Explicit root tag with optional namespace and version
    ns_attr = ' xmlns="{0}"'.format(namespace) if namespace else ""
    version_attr = ' version="{0}"'.format(root_version) if root_version else ""
    content = "".join(_to_xml(v, k) for k, v in data.items())
    xml_body = "<{0}{1}{2}>{3}</{0}>".format(root, ns_attr, version_attr, content)

    return xml_header + xml_body
