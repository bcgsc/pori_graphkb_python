import io
import json
import tarfile

import requests

# Define the package name and version
registry_url = "https://registry.npmjs.org"
package_scope = "@bcgsc-pori/"
package_name = "graphkb-parser"
package_version = "2.0.0"

# Package's metadata
metadata_url = f"{registry_url}/{package_scope}{package_name}/{package_version}"
metadata_req = requests.get(metadata_url)

# Package tarball
metadata = metadata_req.content.decode("utf-8")
tarfile_url = json.loads(metadata)['dist']['tarball']
tarfile_req = requests.get(tarfile_url)

# Extract tarball into memory
with tarfile.open(fileobj=io.BytesIO(tarfile_req.content), mode="r:gz") as tar:
    for i in tar.getmembers():
        print(i)
    # main_file = tar.extractfile(f"{package_name}-{package_version}/graphkb-parser.js")
    # contents = main_file.read()
    # print(contents)
