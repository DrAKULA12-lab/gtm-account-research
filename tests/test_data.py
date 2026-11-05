from acr.signatures import load_ats, load_tech


def test_tech_entries_are_well_formed():
    names = set()
    for t in load_tech():
        assert t["name"] and t["category"]
        assert t["name"] not in names, f"duplicate tech: {t['name']}"
        names.add(t["name"])
        assert t["signatures"], f"{t['name']} has no signatures"
        for sig in t["signatures"]:
            assert sig == sig.lower(), f"{t['name']}: signature must be lowercase: {sig}"


def test_ats_entries_are_well_formed():
    ats = load_ats()
    assert ats
    for name, sig in ats.items():
        assert sig == sig.lower(), f"{name}: signature must be lowercase"
