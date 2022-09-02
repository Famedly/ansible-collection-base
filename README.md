# `famedly.base` ansible collection

![Matrix](https://img.shields.io/matrix/ansible-famedly:matrix.org)

## Scope

This ansible collection contains a variety of basic/barebone functionality
needed for bootstrapping larger, complex infrastructure. This includes
roles for databases (like redis, ldap, postgres) as they are often a foundation
to build services on.

## Roles

- [`roles/dns`](roles/dns/README.md) for setting DNS records with ansible, currently only cloudflare as a backend is supported
- [`roles/dropbear_luks_unlock`](roles/dropbear_luks_unlock/README.md) for setting up dropbear to unlock LUKS volumes using a SSH connection at boot
- [`roles/hostname`](roles/hostname/README.md) for setting `/etc/hostname` and `/etc/hosts`
- [`roles/ldap`](roles/ldap/README.md) to deploy openldap in a docker container
- [`roles/redis`](roles/redis/README.md) to deploy redis in a docker container
- [`roles/ssh`](roles/ssh/README.md) for SSH hardening
- [`roles/user`](roles/user/README.md) for creating user accounts with SSH keys deployed

## License

[AGPL-3.0-only](LICENSE.md)

## Authors

- Jadyn Emma Jäger <jadyn@jadyn.dev>
- Jan Christian Grünhage <jan.christian@gruenhage.xyz>
- Johanna Dorothea Reichmann <transcaffeine@finallycoffee.eu>
- Vincent Wilke <v.wilke@famedly.com>
