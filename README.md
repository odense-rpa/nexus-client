# KMD Nexus Client

This is a client for calling the KMD Nexus API. It allows for interoperability between Python and KMD Nexus using the REST api.

This code is provided as-is with no warranty or guarantee of correctness. Use this at your own risk.

This client is not officially supported or endorsed by KMD. Use this at your own risk.

## Example

You can access Nexus by instantiang a client object. From there you can instantiate sub-clients for the business areas and use these to call specific sections.

The client itself handles all communications and errors. It also provides the api dictionary which contains all basic api calls.


```code
from kmd_nexus_client import NexusClient, OrganizationsClient


def main():
    
    client = NexusClient(instance="your instance", client_id="<id>", client_secret="<secret>")
    
    organizations = OrganizationsClient(client)
    
    
    print(client.api)
    print(organizations.get_organizations())


if __name__ == "__main__":
    main()
```

## License

```
MIT License

Copyright (c) 2025 Odense Kommune

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

