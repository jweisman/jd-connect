from google.cloud import storage
from urllib.parse import urlparse

def upload_blob_from_memory(bucket_name, contents, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(contents)

    print(f"{destination_blob_name} uploaded to {bucket_name}.")

def find_link(iterable, rel):
  link = next((link for link in iterable if link['rel'] == rel), None)
  return link['uri'] if link else None

def add_qs_params(url, params):
    import urllib.parse

    url_parts = urllib.parse.urlparse(url)
    query = dict(urllib.parse.parse_qsl(url_parts.query))
    query.update(params)

    return url_parts._replace(query=urllib.parse.urlencode(query)).geturl()

def get_client_redirect_uri(request):
  o = urlparse(request.base_url)
  port = "" if o.port in [80,443] else f":{o.port}"
  return f"{o.scheme}://{o.hostname}{port}/callback"