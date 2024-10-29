# Proxy servers management

This project is a simple proxy servers management system. It allows to add, remove and list
proxy servers. It also allows to check if a proxy server is working or not.

## Supported cloud providers

- DigitalOcean
- Hetzner

## Required environment variables

- `PROXY_LOGIN` - login for the proxy server
- `PROXY_PASSWORD` - password for the proxy server
- `DO_TOKEN` - DigitalOcean API token
- `DO_PROJECT_ID` - DigitalOcean project ID
- `HETZNER_TOKEN` - Hetzner API token

## Usage

Authentication using Bearer token.

```
POST - create a new proxy server
/api/proxies/proxies/
{
  "provider": "digitalocean"
}

GET - list all proxies
/api/proxies/proxies/

GET - list proxies for a client (create a client if it does not exist)
/api/proxies/client/{client}/

PUT - put the proxy server to client's blacklist
/api/proxies/client/{client}/
{
  "proxy_id: "proxy_id"
}
```
