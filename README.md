# Seafile Docker Container

There are many Seafile Docker images, there is even official one from the Seafile team. Non of them I liked, even though I'm running official one, version 7.1.4. And it has a couple of drawbacks, it packs nginx inside the container, wants to take over ports 80 and 443, and changing environment variables between container restart does nothing, since they only matter during container creation. Maybe it's changed over time, I didn't check new versions in a long time.

This image mostly me trying to pack non-container native application into Docker container.

Since my use case involves only me using Seafile, this image runs only with SQLite and without memcache.

## Seafile components

Seafile actually consists if multiple components.

- Seafile - The service it's self, that manages files. It's has it's own network port.
- Seahub - Web interface of Seafile. That talks to the Seafile service via it's network port. It's has it's own network port.
- Seafdav - Webdav service. It's has it's own network port.

## ENV

There this variables you can set:

- `TZ` - Timezone. Default `Etc/UTC`.
- `SEAFILE_ADMIN_EMAIL` - admin use login in form of email. Default `me@example.com`.
- `SEAFILE_ADMIN_PASSWORD` - admin password. Default `asecret`.
  - SEAFILE_ADMIN_EMAIL and SEAFILE_ADMIN_PASSWORD are used one time during container creation and used to create admin user in DB. After that you can delete this variables and manage users in web interface.
- `ENABLE_WEBDAV` - Enable/Disable WEBDav. Default `False`.
- `SEAFILE_URL` - URL format is `scheme://hostname_or_IP:seahub_port:seafile_port`. Seafile needs to know it's url to set media and file links. Default `127.0.0.1:8000:8082`. You can run it without web server, just using ports. With default values Seahub will be available at `localhost:8000`. When using web server with reverse proxy set URL to, for example `https://seafile.example.com`. You need to configure paths for `/`, `/seafhttp` and `/seafdav`, if using WebDav. See `nginx.conf` for how to do it in nginx.
