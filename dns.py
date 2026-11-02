#!/usr/bin/env python3
"""Point roninsoft.io at GitHub Pages and set up support@ forwarding through the Namecheap API.

Credentials (never in the repo) from ~/.forge/plugins/namecheap/namecheap.toml when it exists, else
~/.config/Claude/namecheap/namecheap.env or $NAMECHEAP_ENV_FILE:
  NAMECHEAP_API_USER=<namecheap username>
  NAMECHEAP_API_KEY=<api key from Profile > Tools > Namecheap API Access>
  NAMECHEAP_USERNAME=<same username unless you use a sub-account>
  NAMECHEAP_CLIENT_IP=<optional; defaults to this machine's public IP, which must be whitelisted in that same page>
  FORWARD_TO=<the mailbox support@ should land in>

  python3 dns.py            # show current records
  python3 dns.py --apply    # replace the parking records with GitHub Pages, keep any TXT/MX, set support@ forwarding
"""
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DOMAIN = ("roninsoft", "io")
API = "https://api.namecheap.com/xml.response"
NS = {"nc": "http://api.namecheap.com/xml.response"}
PAGES_A = ["185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153"]
WANT = [{"HostName": "@", "RecordType": "A", "Address": ip, "TTL": "1800"} for ip in PAGES_A] + [
    {"HostName": "www", "RecordType": "CNAME", "Address": "ronin11.github.io.", "TTL": "1800"}]


TOML = os.path.expanduser("~/.forge/plugins/namecheap/namecheap.toml")  # the forge plugin's config, if present


def load_env():
    path = os.environ.get("NAMECHEAP_ENV_FILE") or os.path.expanduser("~/.config/Claude/namecheap/namecheap.env")
    env = {}
    if os.path.isfile(TOML):
        import tomllib
        t = tomllib.load(open(TOML, "rb"))
        nc = t.get("namecheap", {})
        env = {"NAMECHEAP_API_USER": nc.get("api_user", ""), "NAMECHEAP_API_KEY": nc.get("api_key", ""),
               "NAMECHEAP_USERNAME": nc.get("username", ""), "FORWARD_TO": t.get("registrant", {}).get("email", "")}
        path = TOML
    if os.path.isfile(path) and path != TOML:
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("NAMECHEAP_API_USER", "NAMECHEAP_API_KEY", "NAMECHEAP_USERNAME", "NAMECHEAP_CLIENT_IP", "FORWARD_TO"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    missing = [k for k in ("NAMECHEAP_API_USER", "NAMECHEAP_API_KEY") if not env.get(k)]
    if missing:
        sys.exit(f"missing {missing} (looked in {path})")
    env.setdefault("NAMECHEAP_USERNAME", env["NAMECHEAP_API_USER"])
    if not env.get("NAMECHEAP_CLIENT_IP"):
        env["NAMECHEAP_CLIENT_IP"] = urllib.request.urlopen("https://api.ipify.org", timeout=10).read().decode().strip()
    return env


def call(env, command, **params):
    q = {"ApiUser": env["NAMECHEAP_API_USER"], "ApiKey": env["NAMECHEAP_API_KEY"], "UserName": env["NAMECHEAP_USERNAME"],
         "ClientIp": env["NAMECHEAP_CLIENT_IP"], "Command": command, "SLD": DOMAIN[0], "TLD": DOMAIN[1], **params}
    data = urllib.parse.urlencode(q).encode()
    root = ET.fromstring(urllib.request.urlopen(urllib.request.Request(API, data=data), timeout=30).read())
    if root.get("Status") != "OK":
        errs = "; ".join(e.text or "" for e in root.iter("{%s}Error" % NS["nc"]))
        sys.exit(f"{command} failed: {errs}")
    return root


def get_hosts(env):
    root = call(env, "namecheap.domains.dns.getHosts")
    return [dict(h.attrib) for h in root.iter("{%s}host" % NS["nc"])]


def main():
    apply = "--apply" in sys.argv
    env = load_env()
    hosts = get_hosts(env)
    print("current records:")
    for h in hosts:
        print(f"  {h['Type']:6} {h['Name']:8} {h['Address']}  ttl {h.get('TTL')}" + (f"  mx {h.get('MXPref')}" if h["Type"] == "MX" else ""))
    # keep everything that isn't the parking A/CNAME/URL records at @ and www
    keep = [h for h in hosts if not (h["Name"] in ("@", "www") and h["Type"] in ("A", "CNAME", "URL", "URL301", "FRAME", "AAAA"))]
    new = [{"HostName": h["Name"], "RecordType": h["Type"], "Address": h["Address"], "TTL": h.get("TTL", "1800"),
            **({"MXPref": h["MXPref"]} if h["Type"] == "MX" else {})} for h in keep] + WANT
    print("\nafter:")
    for h in new:
        print(f"  {h['RecordType']:6} {h['HostName']:8} {h['Address']}")
    if not apply:
        print("\n(dry run; pass --apply to write)")
        return
    params = {}
    mx_mode = any(h["Type"] == "MX" for h in keep)
    for i, h in enumerate(new, 1):
        for k, v in h.items():
            params[f"{k}{i}"] = v
    if not mx_mode and env.get("FORWARD_TO"):
        params["EmailType"] = "FWD"  # Namecheap's own forwarding MX records
    call(env, "namecheap.domains.dns.setHosts", **params)
    print("\nDNS written.")
    if env.get("FORWARD_TO"):
        call(env, "namecheap.domains.dns.setEmailForwarding",  # this command wants the whole domain name
             **{"DomainName": ".".join(DOMAIN), "MailBox1": "support", "ForwardTo1": env["FORWARD_TO"]})
        print(f"support@{DOMAIN[0]}.{DOMAIN[1]} forwards to the FORWARD_TO mailbox.")


if __name__ == "__main__":
    main()
