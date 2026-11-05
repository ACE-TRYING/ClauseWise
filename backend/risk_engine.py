import re


RULES = {
    "Auto-Renewal": {
        "keywords": [
            "automatically renew",
            "automatically renewed",
            "auto-renew",
            "auto renew",
            "renew automatically",
            "automatic renewal",
        ],
        "severity": "medium",
        "points": 5,
        "why": "The contract may continue automatically unless you cancel in time.",
        "tip": "Check the renewal date, cancellation deadline, and required notice method.",
    },

    "Indemnification": {
        "keywords": [
            "indemnify",
            "indemnification",
            "hold harmless",
            "defend and hold harmless",
        ],
        "severity": "high",
        "points": 8,
        "why": "You may have to cover certain losses, claims, or legal costs.",
        "tip": "Check which losses are covered and whether the obligation is limited to your actions.",
    },

    "Liability": {
        "keywords": [
            "not responsible",
            "not liable",
            "shall not be liable",
            "shall not be responsible",
            "will not be liable",
            "will not be responsible",
            "no liability",
            "entire liability",
            "liability will be limited",
            "liability shall be limited",
            "liability is limited",
            "limited to the amount actually paid",
            "not be responsible",
            "not be liable",
            "in no event shall",
            "in no event will",
            "in no event is",
        ],
        "severity": "high",
        "points": 6,
        "why": "The contract may limit or exclude responsibility for certain losses.",
        "tip": "Check the liability limits, exceptions, and whether negligence or misconduct is covered.",
    },

    "Penalty": {
        "keywords": [
            "penalty",
            "late fee",
            "late charge",
            "forfeit",
            "forfeiture",
            "liquidated damages",
        ],
        "exclude_keywords": [
            "penalty of perjury",
        ],
        "severity": "high",
        "points": 6,
        "why": "You could face an additional charge or financial consequence.",
        "tip": "Check the amount, the event that triggers it, and whether a grace period applies.",
    },

    "Arbitration": {
        "keywords": [
            "arbitration",
            "arbitrator",
            "binding arbitration",
        ],
        "severity": "medium",
        "points": 4,
        "why": "Some disputes may have to be resolved through private arbitration instead of court.",
        "tip": "Check where arbitration takes place, who pays the costs, and whether it is mandatory.",
    },

    "Termination": {
        "keywords": [
            "terminate",
            "termination",
            "terminate this agreement",
            "termination of this agreement",
            "suspend your account",
            "suspension of your account",
        ],
        "severity": "medium",
        "points": 3,
        "why": "This clause explains when the agreement or account can be ended or suspended.",
        "tip": "Check the notice period, reasons for termination, and whether the same rights apply to both sides.",
    },

    "Payment Terms": {
        "keywords": [
            "must pay",
            "required to pay",
            "shall pay",
            "payment is due",
            "payment shall be made",
            "monthly payment",
            "annual payment",
            "security deposit",
            "refundable deposit",
            "processing fee",
            "service fee",
            "subscription fee",
            "non-refundable fee",
            "charged for",
            "amount due",
            "payment deadline",
            "payment obligation",
            "payment obligations",
            "fees are payable",
            "you agree to pay",
        ],
        "severity": "low",
        "points": 1,
        "why": "This clause describes a payment, fee, or other financial obligation.",
        "tip": "Confirm the amount, payment deadline, additional charges, and refund conditions.",
    },
}


def match_keyword(sentence, keyword):
    pattern = r"\b" + re.escape(keyword) + r"\b"
    return re.search(pattern, sentence, re.IGNORECASE) is not None


def find_clauses(sentences):
    found = []
    seen = set()

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        for name, rule in RULES.items():

            # Skip sentences that explicitly match an exclusion.
            excluded = any(
                match_keyword(sentence, keyword)
                for keyword in rule.get("exclude_keywords", [])
            )

            if excluded:
                continue

            hit = next(
                (
                    keyword
                    for keyword in rule["keywords"]
                    if match_keyword(sentence, keyword)
                ),
                None
            )

            if not hit:
                continue

            # Avoid classifying a late fee or penalty as a normal payment term.
            if name == "Payment Terms":
                penalty_match = any(
                    match_keyword(sentence, keyword)
                    for keyword in RULES["Penalty"]["keywords"]
                )

                if penalty_match:
                    continue

            # A sentence should only be counted once for each category.
            normalized_sentence = re.sub(
                r"\s+",
                " ",
                sentence.lower()
            )

            key = (normalized_sentence, name)

            if key in seen:
                continue

            seen.add(key)

            found.append({
                "type": name,
                "sentence": sentence,
                "matched": hit,
                "severity": rule["severity"],
                "points": rule["points"],
                "why": rule["why"],
                "tip": rule["tip"],
            })

    return found


def score(clauses):
    total = sum(clause["points"] for clause in clauses)

    # Keep the displayed score within a 0–100 range.
    total = min(total, 100)

    if total < 10:
        level = "Low"
    elif total < 25:
        level = "Medium"
    else:
        level = "High"

    return total, level


if __name__ == "__main__":

    test_sentences = [
        "You must pay 5000 every month.",
        "Payment processing is handled by a third party.",
        "You are required to pay a security deposit.",
        "Payment methods include credit cards.",
        "A late fee of 500 applies.",
        "A penalty of 5000 applies for late payment.",
        "The statement is made under penalty of perjury.",
        "The entire liability of the Company shall be limited to the amount actually paid.",
        "In no event shall the Company or its suppliers be liable for special damages.",
        "The Company is not responsible for user content.",
        "Your subscription will automatically renew every year.",
        "You agree to indemnify and hold harmless the Company.",
    ]

    clauses = find_clauses(test_sentences)

    for clause in clauses:
        print(
            clause["type"],
            "->",
            clause["matched"],
            "|",
            clause["severity"]
        )

    total, level = score(clauses)

    print("\nTotal Risk Score:", total)
    print("Risk Level:", level)