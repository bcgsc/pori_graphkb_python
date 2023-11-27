"""_summary_
    matches:
        Array of variants (diplayName and type) that MUST be matching, but not restricted to
    does_not_matches:
        Array of variants (diplayName and type) that MUST NOT be matching, but not restricted to
"""


# Screening structural variant to rule out small events [KBDEV_1056]
structuralVariants = {
    # Unambiguous structural variations
    "(FGFR3,BRCA2):fusion(g.1234567,g.1234567)": {
        "matches": {
            "displayName": [
                "FGFR3 fusion",
                "FGFR3 rearrangement",
            ],
            "type": [
                "fusion",
                "rearrangement",
            ],
        },
    },
    # ambiguous structural variations -> structural
    "FGFR3:c.1200_1300dup": {
        "matches": {
            "displayName": [
                "FGFR3 mutation",
                "FGFR3 rearrangement",
            ],
            "type": [
                "mutation",
                "rearrangement",
            ],
        },
    },
    "FGFR3:c.1200_1201insACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT": {
        "matches": {
            "displayName": [
                "FGFR3 mutation",
                "FGFR3 rearrangement",
            ],
            "type": [
                "mutation",
                "rearrangement",
            ],
        },
    },
    "FGFR3:g.5000_5100del": {
        "matches": {
            "displayName": [
                "FGFR3 mutation",
                "FGFR3 rearrangement",
            ],
            "type": [
                "mutation",
                "rearrangement",
            ],
        },
    },
    "FGFR3:c.1200_1300delinsA": {
        "matches": {
            "displayName": [
                "FGFR3 mutation",
                "FGFR3 rearrangement",
            ],
            "type": [
                "mutation",
                "rearrangement",
            ],
        },
    },
    "FGFR3:c.1200delinsACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT": {
        "matches": {
            "displayName": [
                "FGFR3 mutation",
                "FGFR3 rearrangement",
            ],
            "type": [
                "mutation",
                "rearrangement",
            ],
        },
    },
    # ambiguous structural variations -> non-structural
    "FGFR3:c.1200dup": {
        "matches": {
            "displayName": [
                "FGFR3 mutation",
            ],
            "type": [
                "mutation",
            ],
        },
        "does_not_matches": {
            "displayName": [
                "FGFR3 rearrangement",
            ],
            "type": [
                "rearrangement",
            ],
        },
    },
    "FGFR3:c.1200_1201insA": {
        "matches": {
            "displayName": [
                "FGFR3 mutation",
            ],
            "type": [
                "mutation",
            ],
        },
        "does_not_matches": {
            "displayName": [
                "FGFR3 rearrangement",
            ],
            "type": [
                "rearrangement",
            ],
        },
    },
    "FGFR3:g.5000del": {
        "matches": {
            "displayName": [
                "FGFR3 mutation",
            ],
            "type": [
                "mutation",
            ],
        },
        "does_not_matches": {
            "displayName": [
                "FGFR3 rearrangement",
            ],
            "type": [
                "rearrangement",
            ],
        },
    },
    "FGFR3:c.1200delinsA": {
        "matches": {
            "displayName": [
                "FGFR3 mutation",
            ],
            "type": [
                "mutation",
            ],
        },
        "does_not_matches": {
            "displayName": [
                "FGFR3 rearrangement",
            ],
            "type": [
                "rearrangement",
            ],
        },
    },
    "FANCM:e.2del": {
        "matches": {
            "displayName": [
                "FANCM mutation",
            ],
            "type": [
                "mutation",
            ],
        },
        "does_not_matches": {
            "displayName": [
                "FANCM structural variant",
            ],
            "type": [
                "structural variant",
            ],
        },
    },
    # non-structural variations
    "FGFR3:c.1200C>A": {
        "matches": {
            "displayName": [
                "FGFR3 mutation",
            ],
            "type": [
                "mutation",
            ],
        },
        "does_not_matches": {
            "displayName": [
                "FGFR3 rearrangement",
            ],
            "type": [
                "rearrangement",
            ],
        },
    },
}

# 
smallMutations = {
    "...": {
        "matches": {
            "displayName": [
                "...",
            ],
            "type": [
                "...",
            ],
        },
        "does_not_matches": {
            "displayName": [
                "...",
            ],
            "type": [
                "...",
            ],
        },
    },
}

# Make sure delins (indel) events are treated appart [KBDEV-1133]
# delins match deletion/insertion, and deletion/insertion match delins
delins = {
    "...": {
        "matches": {
            "displayName": [
                "...",
            ],
            "type": [
                "...",
            ],
        },
        "does_not_matches": {
            "displayName": [
                "...",
            ],
            "type": [
                "...",
            ],
        },
    },
}

# ...
other = {
    "VHL:p.T133Lfs*26": {
        "matches": {
            "displayName": [
                "VHL:p.T133fs",
                "VHL:c.397delA",
                "VHL deletion",
                "VHL frameshift mutation",
                "VHL mutation",
                "VHL truncating",
            ],
            "type": [
                "...",
            ],
        },
        "does_not_matches": {
            "displayName": [
                "...",
            ],
            "type": [
                "...",
            ],
        },
    },
}