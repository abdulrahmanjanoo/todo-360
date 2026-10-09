"""Revenue lens: which to-dos (and meetings) carry a money opportunity.

Derived, never written to the vault. A to-do earns the `#revenue` tag when its text and
project tag score at least MIN_SCORE: strong commercial terms (a price, a proposal, an
invoice, a contract) count 2, deal-stage words (pilot, prospect, opportunity) and sales tags
count 1. Abdul can overrule any verdict from the app; that override lives in decisions.json.
"""
import re

MIN_SCORE = 2

STRONG = [
    (r"\bproposals?\b", "proposal"),
    (r"\bpric(e|es|ed|ing)\b", "price"),
    (r"\bquot(e|es|ed|ation)\b", "quote"),
    (r"\binvoic(e|es|ed|ing)\b", "invoice"),
    (r"\bpay(ment|ments|ing|able)?\b|\bpaid\b", "payment"),
    (r"\bcontracts?\b|\bagreements?\b", "contract"),
    (r"\bsow\b|statement of work", "SOW"),
    (r"\bpurchase order\b|\bpo\b", "purchase order"),
    (r"\brenew(al|als|ed|ing)?\b", "renewal"),
    (r"\bupsell|cross[- ]sell|\bexpansion\b", "upsell"),
    (r"\bbudgets?\b", "budget"),
    (r"\brevenue\b|\barr\b|\bmrr\b", "revenue"),
    (r"\bretainer\b", "retainer"),
    (r"\bfees?\b|\bfee basis\b", "fee"),
    (r"\brate card\b|\bper (call|vehicle|user|seat|month|minute|document|device)\b", "unit price"),
    (r"\d\s*(lakh|lakhs|crore|cr)\b|\b(lakh|lakhs|crore)s?\b", "amount"),
    (r"₹|\$|\binr\b|\busd\b|\brs\.?\s?\d", "currency"),
    (r"\bcommercials?\b|commercial terms", "commercials"),
    (r"\bmsa\b", "MSA"),
    (r"\bdiscount(s|ed)?\b", "discount"),
    (r"\bnegotiat(e|ed|ion|ing)\b", "negotiation"),
    (r"\btender|\brfp\b|\brfq\b|\brfi\b|\bbid\b", "tender"),
    (r"\bbilling\b|\bbill(ed)?\b", "billing"),
    (r"\bmargins?\b", "margin"),
    (r"\bcost(ing)? sheet\b|\bcost estimate\b|\bcosting\b|\bestimate\b", "costing"),
    (r"\blicen[cs]e fee|\bsubscription\b", "subscription"),
    (r"\bclose the deal\b|\bdeal (value|size)\b|\bwin (the|one|a|this) (customer|deal|account|contract)\b", "close"),
    (r"\bsign(ing|ed)? (the |off (on )?)?(contract|agreement|msa|sow|nda|proposal)\b", "signature"),
    (r"\b(send|share|put|give|present)\b.{0,60}\bcosts?\b|\bcosts? (to|for) [A-Z]", "cost to client"),
]
# money that leaves Tericsoft, or people costs: a hire, a salary, a vendor bill. Not revenue.
NEGATIVE = [
    (r"\bhr\b|\bhir(e|ing)\b|\brecruit|\bcandidate|\bintern(s|ship)?\b|\bsalary|\bpayroll|\bemployment|\bappraisal|\bjoining\b", "people cost"),
    (r"\bcancel|\bunsubscribe|\bour (cloud|aws|azure|gcp|server) (bill|cost)|\bvendor (bill|invoice|payment)|\brenew our\b", "our own cost"),
]
MEDIUM = [
    (r"\bpilots?\b", "pilot"),
    (r"\bpoc\b|proof of concept", "POC"),
    (r"\bprospects?\b", "prospect"),
    (r"\bopportunit(y|ies)\b", "opportunity"),
    (r"\bdeals?\b", "deal"),
    (r"\bleads?\b", "lead"),
    (r"\bpipeline\b", "pipeline"),
    (r"\bscope\b|\bscoping\b", "scope"),
    (r"\bpartnership\b|\bpartner\b", "partnership"),
    (r"\bdemo\b", "demo"),
    (r"\bnda\b", "NDA"),
    (r"\bclient\b|\bcustomer\b", "customer"),
]
TAG_SIGNALS = [
    (r"^p/Lead/", "lead project"),
    (r"^Area/Sales/", "sales area"),
    (r"^p/Partner/", "partner project"),
]


def _hits(patterns, text, weight):
    out = []
    for pat, label in patterns:
        if re.search(pat, text, re.I):
            out.append((label, weight))
    return out


def classify(text, tag=""):
    """-> {"money": bool, "score": int, "reasons": [labels]} for one to-do."""
    text = text or ""
    strong = _hits(STRONG, text, 2)
    hits = strong + _hits(MEDIUM, text, 1)
    anchored = bool(strong)
    for pat, label in TAG_SIGNALS:
        if re.search(pat, tag or ""):
            hits.append((label, 1))
            anchored = True
    score = sum(w for _, w in hits)
    neg = _hits(NEGATIVE, text, 3)
    score -= sum(w for _, w in neg)
    # two deal-stage words alone (demo + customer) are not a money signal; something has to anchor it
    return {"money": anchored and score >= MIN_SCORE, "score": score,
            "reasons": [l for l, _ in hits][:6] if score >= MIN_SCORE else [l for l, _ in neg]}


def effective(todo, override=None):
    """Abdul's override (yes / no) beats the heuristic."""
    if override == "yes":
        return True
    if override == "no":
        return False
    return bool(todo.get("money"))
