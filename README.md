***Note: I am no longer maintaining this repository, as I've moved on from using a dynamic DNS and port forwarding to expose my server to the cloud. Ultimately, I feel that using Cloudflare tunnels is a much easier, safer and more sustainable option for my use case, so I no longer have a need to keep my dynv6.net records up to date. Anyone who wants to is free to fork this repository and take over the project.***

# DynV6 API v2 Updater

Uses the REST API supplied by DynV6 to update zone records. Forked from [teunito/dynv6_apiv2_updater](https://github.com/teunito/dynv6_apiv2_updater), which is now 2 years without updates and buggy.

## Usage
`python3 dynv6-client.py --token "your_token" --interface "your_interface" record.zone.dynv6.net`

## Thanks
@[teunito](https://github.com/teunito) for the original code that was the basis and inspiration for this fork. (Please hit me up if you want me to merge this into your project via a pull request.)
