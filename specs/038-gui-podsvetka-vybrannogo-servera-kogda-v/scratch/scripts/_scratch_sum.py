import json

d = json.load(open("/home/m26/probe.json"))
print("window", d["window"])
for p in d["pages"]:
    print("%-9s vp=%s content=%s minHint=%s hbar=%s" % (
        p["page"], p.get("viewport_w"), p.get("content_w"),
        p.get("content_minHint_w"), p.get("hbar_range")))
    for k in p.get("widest_children", [])[:3]:
        print("     ", k)
