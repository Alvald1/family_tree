"""Small route helpers shared by HTTP handlers and API classes."""

from urllib.parse import unquote, urlparse


def parse_api_path(path):
    parsed_path = urlparse(path).path
    return [unquote(part) for part in parsed_path.split("/") if part]
