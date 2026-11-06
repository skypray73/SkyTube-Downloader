"""Preserve SSL data files required by the Python used to build the app."""
from pathlib import Path
import ssl


def ssl_data_files(module=ssl):
    """PyInstaller cannot infer files opened by a customized standard library."""
    source = Path(module.__file__)
    filename = 'codex-rejected-cas.pem'
    resource = source.with_name(filename)
    if resource.is_file():
        return [(str(resource), '.')]
    if source.is_file() and filename in source.read_text(encoding='utf-8'):
        raise RuntimeError('Python SSL runtime data is missing: ' + str(resource))
    return []


def check_ssl_runtime():
    """Construct the same verified TLS context needed before any HTTPS request."""
    import certifi
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cafile=certifi.where())
    if not context.check_hostname or context.verify_mode != ssl.CERT_REQUIRED:
        raise RuntimeError('HTTPS certificate verification must be enabled')
    if not context.get_ca_certs():
        raise RuntimeError('No trusted HTTPS certificates were loaded')
    return context.cert_store_stats()['x509_ca']
