"""Proxy rules in front of the frontend: AED service paths go to the service, the portal API (incl. /aed-aggregated)
goes to the portal. Both nginx `location /x` and dev-proxy keys are prefix matches, so `/api/aed` would also swallow
`/api/aed-aggregated` (bug seen on aed.heckyeah.pl: the national AED list page got 404).
Run: python3 -m unittest tests.test_proxy_routes"""
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NGINX = ["docker/nginx.conf.template", "backend/aed-domain/web.conf.template"]
DEV_PROXIES = ["frontend/proxy.aed.conf.json", "frontend/proxy.aed-local.conf.json"]

SERVICE_PATH = "/api/aed/statystyki"
PORTAL_PATHS = ["/api/aed-aggregated", "/api/aed-aggregated/resource", "/api/datasets"]


def nginx_rules(path):
    """(prefix, target) of plain prefix `location` blocks, in file order."""
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        text = f.read()
    # A block ends at a line holding only `}` (`${VAR}` inside proxy_pass also has braces).
    blocks = re.findall(r"location\s+(/\S*)\s*\{(.*?)\n\s*\}", text, re.S)
    return [(prefix, (re.search(r"proxy_pass\s+([^;]+);", body) or [None, None])[1]) for prefix, body in blocks]


def nginx_target(rules, url):
    """nginx picks the longest matching prefix location."""
    matches = [(prefix, target) for prefix, target in rules if url.startswith(prefix)]
    return max(matches, key=lambda rule: len(rule[0]))[1] if matches else None


def dev_proxy_target(path, url):
    """Angular dev server (http-proxy-middleware): first key whose prefix matches; `/**` means the prefix itself."""
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        rules = json.load(f)
    for key, rule in rules.items():
        if url.startswith(key.replace("/**", "/")):
            return rule["target"] if isinstance(rule["target"], str) else rule["target"]["host"]
    return None


class ProxyRoutesTest(unittest.TestCase):
    def test_nginx_sends_aed_service_paths_to_the_service_and_aed_aggregated_to_the_portal(self):
        for path in NGINX:
            rules = nginx_rules(path)
            with self.subTest(config=path):
                self.assertEqual(nginx_target(rules, SERVICE_PATH), "${AED_SERVICE_URL}")
                for url in PORTAL_PATHS:
                    self.assertNotEqual(nginx_target(rules, url), "${AED_SERVICE_URL}", url)

    def test_dev_proxies_send_aed_service_paths_to_the_service_and_aed_aggregated_to_the_portal(self):
        for path in DEV_PROXIES:
            with self.subTest(config=path):
                self.assertEqual(dev_proxy_target(path, SERVICE_PATH), "http://localhost:8085")
                for url in PORTAL_PATHS:
                    self.assertNotEqual(dev_proxy_target(path, url), "http://localhost:8085", url)


if __name__ == "__main__":
    unittest.main()
