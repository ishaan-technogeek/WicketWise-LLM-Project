import json, re, sys, urllib.request, urllib.error, concurrent.futures as cf

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}

GREENHOUSE = """postman hasura chargebee browserstack razorpay groww meesho zomato swiggy dream11
sharechat slice navi zepto atlan sprinklr mindtickle whatfix innovaccer darwinbox leadsquared
coinbase dropbox figma notion reddit discord stripe airbnb twilio gitlab mongodbinc elastic
cloudflare databricks confluent nutanix rubrik druva harness postmanlabs zscaler
hackerrank chargebeeinc smallcase setu juspay phonepe uber lyft doordash instacart robinhood
plaid brex ramp rippling asana samsara affirm chime gusto""".split()

LEVER = """swiggy jupiter khatabook dunzo urbancompany practo gupshup exotel netcore
spinny cars24 zolostays rentomojo bijnis moengage clevertap plivo hasura
figma notion attentive mistral perplexityai scale openai anthropic""".split()

SMARTREC = """Freshworks ThoughtWorks Visa Bosch Siemens SAP Publicis Ubisoft""".split()


def get(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def greenhouse(slug):
    d = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=false")
    if not isinstance(d, dict):
        return []
    out = []
    for j in d.get("jobs", []):
        out.append({
            "co": slug, "src": "greenhouse",
            "title": j.get("title", ""),
            "loc": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
        })
    return out


def lever(slug):
    d = get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    if not isinstance(d, list):
        return []
    out = []
    for j in d:
        c = j.get("categories") or {}
        out.append({
            "co": slug, "src": "lever",
            "title": j.get("text", ""),
            "loc": c.get("location", "") or "",
            "url": j.get("hostedUrl", ""),
        })
    return out


def smartrec(slug):
    d = get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100")
    if not isinstance(d, dict):
        return []
    out = []
    for j in d.get("content", []):
        loc = j.get("location") or {}
        out.append({
            "co": slug, "src": "smartrecruiters",
            "title": j.get("name", ""),
            "loc": f"{loc.get('city','')}, {loc.get('country','')}".strip(", "),
            "url": f"https://jobs.smartrecruiters.com/{slug}/{j.get('id','')}",
        })
    return out


tasks = [(greenhouse, s) for s in GREENHOUSE] + [(lever, s) for s in LEVER] + [(smartrec, s) for s in SMARTREC]
rows, hits = [], {}
with cf.ThreadPoolExecutor(max_workers=16) as ex:
    futs = {ex.submit(f, s): (f.__name__, s) for f, s in tasks}
    for fu in cf.as_completed(futs):
        fn, s = futs[fu]
        try:
            r = fu.result()
        except Exception:
            r = []
        if r:
            hits[f"{fn}:{s}"] = len(r)
            rows.extend(r)

json.dump(rows, open("/tmp/jobdata/all_postings.json", "w"))
print("boards that answered:", len(hits), "| total postings:", len(rows))
print(json.dumps(dict(sorted(hits.items(), key=lambda kv: -kv[1])), indent=0))
