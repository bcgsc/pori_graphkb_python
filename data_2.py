"""_summary_
    matches:
        Array of variant (diplayName and type) that MUST be matching, but not restricted to
    does_not_matches:
        Array of variant (diplayName and type) that MUST NOT be matching, but not restricted to
"""

KBDEV_1024 = {
    "TSC2:c.3365G>C": {
        "matches": {
            "displayName": [""],
            "type": [""],
        },
        "does_not_matches": {
            "displayName": [""],
            "type": [""],
        },
    },
}

KBDEV_1044 = {
    "TSC2:c.4700G>A": {
        "matches": {
            "displayName": [
                "ENST00000219476:c.4700G>A",
                "ENST00000219476:r.4810G>A",
                "TSC2 mutation",
                "TSC2:p.G1567D",
                "chr16:g.2086230G>A",
            ],
            "type": [
                "missense mutation",
                "mutation",
                "substitution",
            ],
        },
        "does_not_matches": {
            "displayName": [
                "TSC2 nonsense",
            ],
            "type": [
                "nonsense",
            ],
        },
    },
}



OTHERS = {
    "KRAS:p.G12D": {
        "matches": {
            "displayName": [
                "ENST00000256078:r.225_226delinsAC",
                "ENST00000311936.7:c.35G>A",
                "KRAS mutation",
                "KRAS:c.35G>A",
                "KRAS:p.(G12_G13)mut",
                "KRAS:p.?12mut",
                "KRAS:p.G12",
                "KRAS:p.G12D",
                "KRAS:p.G12X",
                "KRAS:p.G12mut",
            ],
            "type": [
                "indel",
                "missense",
                "missense mutation",
                "mutation",
                "substitution",
            ],
        },
        "does_not_matches": {
            "displayName": [
                "chr12:g.25245349_25245351delinsGCT",
                "cosm516",
                "ensp00000452512:p.G12V",
            ],
            "type": [
                "nonsense",
            ],
        },
    },
}

GERO_299 = {
    "TP53:p.M237I": {
        "matches": {
            "displayName": [
                "ENST00000269305:r.901G>T",
                "TP53 missense",
                "TP53 mutation",
                "TP53:p.M237I",
                "TP53:p.M237X",
                "chr17:g.7577570C>T",
            ],
            "type": [
                "missense",
                "missense mutation",
                "mutation",
                "substitution",
            ],
        },
        "does_not_matches": {
            "displayName": [
                "TP53 nonsense",
            ],
            "type": [
                "nonsense",
            ],
        },
    },
}


# Testing combinations
x = dict(
    **KBDEV_1024,
    **KBDEV_1044,
)

########################
## KBDEV-1038
########################
# "FGFR4:p.N535K",
# "EGFR:p.D942N",
########################
## KBDEV-1052
########################
# "EGFR:c.28246G>A",
# "chr7:g.55198839G>A",
# "EGFR:p.D942N",
# '(PCM1,JAK2):fusion(r.6280,r.1821)',  # dummy test for Infers edges
########################
## KBDEV-1054
########################
# "ERBB2:p.R814C",
########################
## KBDEV-1056
########################
"FGFR3:c.1212dupC",
"FGFR3:c.1212dupACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGT",
"FGFR3:c.1212_1213insC",
"FGFR3:c.1212C>A",
"chr1:g.33344590_33344592del",
"FGFR3:g.5000_5001del",
"FGFR3:g.5000_5100del",
"FGFR3:c.9002_9050delinsTTT",
"FGFR3:c.9002_9051delinsTTT",
########################
## GERO-299
########################
# "chr17:g.7674252C>T",
# "ENST00000269305:c.711G>A",
# "TP53:p.M237I",
########################
## KBDEV-1024
########################
# "TSC2:c.3365G>C",
# "NM_000548.5:c.3365G>A",
# "NM_000548.5:p.Arg1122His",
# "TSC2: p.R112H",
########################
## KBDEV-1044
########################
# "TSC2:c.4700G>A",
########################
## OTHER Ex.
########################
# "ENST00000219476:c.4700_4701delinsAT",
# "NM_000548.5:c.3365G>A",
# "TSC2:p.R112H",
# "TSC2:p.G1567D",
# "KRAS:p.G12D",
