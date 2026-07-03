def winner_team(by_id: dict, fid: str) -> str | None:
    f = by_id.get(fid)
    if not f or f.get("status") != "finished":
        return None
    w = f.get("winner")
    if w == "home": return f.get("home")
    if w == "away": return f.get("away")
    return None

def resolve(fixtures: list[dict]) -> list[str]:
    by_id = {f["fixture_id"]: f for f in fixtures}
    changed: list[str] = []
    for _ in range(10):
        progressed = False
        for f in fixtures:
            links = f.get("links")
            if not links or not f.get("tbd"):
                continue
            hw = winner_team(by_id, links["home_from"])
            aw = winner_team(by_id, links["away_from"])
            if hw and aw and (f.get("home") != hw or f.get("away") != aw):
                f["home"], f["away"], f["tbd"] = hw, aw, False
                changed.append(f["fixture_id"]); progressed = True
        if not progressed:
            break
    return changed
