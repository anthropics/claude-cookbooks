"""Settlement quotes: the manual (policy_manual.md with Section 9 and the Appendix A catalogue put in) and the grader. Standard library only."""

from pathlib import Path

CAT = [  # no, name, area, list price, book hours, labor type, wear category
    ("4101", "Front bumper cover", "front", 385, 2.5, "body", None),
    ("4102", "Hood panel", "front", 520, 2.0, "body", None),
    ("4103", "Fender LH", "front", 340, 2.5, "body", None),
    ("4104", "Fender RH", "front", 340, 2.5, "body", None),
    ("4105", "Headlamp assembly LH", "front", 410, 1.0, "body", None),
    ("4106", "Headlamp assembly RH", "front", 410, 1.0, "body", None),
    ("4107", "Grille", "front", 165, 0.5, "body", None),
    ("4108", "Radiator support", "front", 290, 3.0, "body", None),
    ("4109", "A/C condenser", "front", 310, 1.5, "mechanical", None),
    ("4110", "Front crossmember", "front", 460, 4.0, "frame", None),
    ("4111", "Radiator", "front", 355, 1.5, "mechanical", None),
    ("4112", "Front impact bar", "front", 245, 2.0, "body", None),
    ("4201", "Rear bumper cover", "rear", 360, 2.0, "body", None),
    ("4202", "Trunk lid", "rear", 480, 2.0, "body", None),
    ("4203", "Tail lamp assembly LH", "rear", 220, 1.0, "body", None),
    ("4204", "Tail lamp assembly RH", "rear", 220, 1.0, "body", None),
    ("4205", "Quarter panel LH", "rear", 690, 6.5, "body", None),
    ("4206", "Rear body panel", "rear", 540, 4.5, "body", None),
    ("4207", "Trunk floor pan", "rear", 415, 5.0, "frame", None),
    ("4208", "Rear impact bar", "rear", 230, 1.5, "body", None),
    ("4209", "Rear frame rail section", "rear", 520, 5.5, "frame", None),
    ("4210", "Quarter panel RH", "rear", 690, 6.5, "body", None),
    ("4211", "Backup sensor harness", "rear", 175, 1.0, "mechanical", None),
    ("4301", "Front door shell LH", "left side", 640, 3.5, "body", None),
    ("4302", "Rear door shell LH", "left side", 610, 3.5, "body", None),
    ("4303", "B-pillar reinforcement LH", "left side", 450, 6.0, "frame", None),
    ("4304", "Rocker panel LH", "left side", 380, 5.0, "frame", None),
    ("4305", "Side mirror assembly LH", "left side", 265, 0.5, "body", None),
    ("4306", "Door wiring harness LH", "left side", 190, 1.5, "mechanical", None),
    ("4307", "Door glass LH", "left side", 210, 1.0, "body", None),
    ("4311", "Front door shell RH", "right side", 640, 3.5, "body", None),
    ("4312", "Rear door shell RH", "right side", 610, 3.5, "body", None),
    ("4314", "Rocker panel RH", "right side", 380, 5.0, "frame", None),
    ("4315", "Side mirror assembly RH", "right side", 265, 0.5, "body", None),
    ("4401", "Roof panel", "roof", 720, 8.0, "body", None),
    ("4402", "Paintless dent repair block", "roof", 0, 6.0, "body", None),
    ("4403", "Roof rail molding set", "roof", 145, 1.0, "body", None),
    ("4404", "Cowl panel", "roof", 210, 1.5, "body", None),
    ("4405", "Sunroof frame", "roof", 330, 2.5, "body", None),
    ("4406", "Roof bow set", "roof", 185, 2.0, "frame", None),
    ("4501", "Airbag module, driver", "interior", 780, 1.5, "mechanical", None),
    ("4502", "Airbag module, curtain LH", "interior", 820, 1.5, "mechanical", None),
    ("4503", "Seat-belt pretensioner", "interior", 240, 1.0, "mechanical", None),
    ("4507", "Driver seat upholstery", "interior", 400, 1.5, "body", "upholstery"),
    ("4508", "Rear seat upholstery", "interior", 350, 1.5, "body", "upholstery"),
    ("4601", "Battery", "front", 200, 0.5, "mechanical", "battery"),
    ("4604", "Front strut pair", "front", 450, 2.0, "mechanical", "suspension"),
    ("4605", "Lower control arm LH", "front", 250, 1.5, "mechanical", "suspension"),
    ("4602", "Exhaust pipe section", "rear", 300, 1.0, "mechanical", "exhaust"),
    ("4603", "Muffler assembly", "rear", 350, 1.0, "mechanical", "exhaust"),
    ("4606", "Rear shock pair", "rear", 300, 1.5, "mechanical", "suspension"),
    ("4113", "Hood hinge set", "front", 95, 1.0, "body", None),
    ("4114", "Fog lamp LH", "front", 140, 0.5, "body", None),
    ("4115", "Fog lamp RH", "front", 140, 0.5, "body", None),
    ("4116", "Front bumper absorber", "front", 120, 0.5, "body", None),
    ("4117", "Washer reservoir", "front", 85, 0.5, "mechanical", None),
    ("4118", "Fan shroud assembly", "front", 260, 1.0, "mechanical", None),
    ("4119", "Hood latch", "front", 70, 0.5, "body", None),
    ("4120", "Inner fender liner LH", "front", 90, 0.5, "body", None),
    ("4121", "Inner fender liner RH", "front", 90, 0.5, "body", None),
    ("4212", "Rear bumper absorber", "rear", 110, 0.5, "body", None),
    ("4213", "License lamp harness", "rear", 60, 0.5, "mechanical", None),
    ("4214", "Trunk latch", "rear", 80, 0.5, "body", None),
    ("4215", "Rear valance", "rear", 150, 1.0, "body", None),
    ("4216", "Spare wheel well", "rear", 280, 3.0, "frame", None),
    ("4308", "Front door trim panel LH", "left side", 180, 0.5, "body", None),
    ("4309", "Rear door glass LH", "left side", 195, 1.0, "body", None),
    ("4310", "Door handle set LH", "left side", 75, 0.5, "body", None),
    ("4313", "B-pillar reinforcement RH", "right side", 450, 6.0, "frame", None),
    ("4316", "Door wiring harness RH", "right side", 190, 1.5, "mechanical", None),
    ("4317", "Door glass RH", "right side", 210, 1.0, "body", None),
    ("4407", "Headliner", "roof", 310, 2.0, "body", None),
    ("4408", "Antenna base", "roof", 65, 0.5, "body", None),
    ("4701", "Oil pump", "engine", 280, 1.5, "mechanical", None),
    ("4702", "Brake line set", "engine", 190, 2.0, "mechanical", None),
    ("4703", "Timing chain kit", "engine", 420, 4.0, "mechanical", None),
    ("4704", "Rear main seal", "engine", 95, 3.5, "mechanical", None),
]
CAT.sort(key=lambda r: r[0])
INCL = {
    "4108": ["4109", "4111"],
    "4110": ["4112"],
    "4206": ["4201", "4208"],
    "4205": ["4203"],
    "4210": ["4204"],
    "4301": ["4305", "4307"],
    "4401": ["4403", "4406"],
    "4101": ["4116"],
    "4201": ["4212"],
    "4103": ["4120"],
    "4104": ["4121"],
    "4302": ["4309"],
}  # included operations: labor overlap
PANEL = {
    "4101",
    "4102",
    "4103",
    "4104",
    "4201",
    "4202",
    "4205",
    "4206",
    "4210",
    "4301",
    "4302",
    "4304",
    "4311",
    "4312",
    "4314",
    "4401",
    "4404",
}  # exterior panels that need refinishing


def catalogue_md():
    o = [
        "| Cat. no. | Part | Area | List price | Book hours | Labor type | Wear category (3.3) | Refinish panel | Book hours include the labor for |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for n, nm, ar, lp, bh, lt, w in CAT:
        o.append(
            f"| {n} | {nm} | {ar} | ${lp} | {bh} | {lt} | {({'battery': 'Batteries', 'exhaust': 'Exhaust systems', 'upholstery': 'Convertible tops / upholstery', 'suspension': 'Suspension wear components'}[w]) if w else 'none'} | {'yes' if n in PANEL else 'no'} | {', '.join(INCL[n]) if n in INCL else 'none'} |"
        )
    return "\n".join(o)


HERE = Path(__file__).parent
TOLERANCE = 0.50  # dollars; forgives cent rounding only


def manual():
    """The cost cookbook's policy manual, unchanged, with Section 9 and Appendix A inserted before the end marker."""
    head, tail = (
        (HERE / "policy_manual.md").read_text(encoding="utf-8").split("---\n\n*End of Manual")
    )
    s9 = (
        (HERE / "section9_desk_settlement.md")
        .read_text(encoding="utf-8")
        .replace("CATALOGUE_TABLE", catalogue_md())
    )
    return head.rstrip() + "\n" + s9 + "\n---\n\n*End of Manual" + tail


def _system(ask):
    return (
        "You are the settlement desk assistant for Acme Insurance auto claims. An adjuster is on a live call with a customer and sends you the claim file. "
        "Apply the Desk Settlement Procedure (Section 9 of the manual below) and return the verdict and the amount.\n\n<manual>\n"
        + manual()
        + "\n</manual>\n\n"
        + ask
    )


SYSTEM = _system(
    "Return the verdict (APPROVE, SUPERVISOR, FRAUD or DENY) and the amount in dollars and cents (0 for FRAUD and DENY)."
)


def grade(item, parsed):
    """True when the verdict matches and the amount is within TOLERANCE. parsed is the decoded JSON reply; extra fields such as working are ignored."""
    try:
        return (
            str(parsed["verdict"]).upper() == item["key"]["verdict"]
            and abs(float(parsed["amount"]) - item["key"]["amount"]) <= TOLERANCE
        )
    except (KeyError, TypeError, ValueError):
        return False
