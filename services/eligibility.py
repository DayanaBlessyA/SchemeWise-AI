
import csv
import html
import re
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "Schemes.csv"


def clean(value):
    value = html.unescape(str(value or ""))
    value = re.sub(r"<[^>]*>", " ", value)
    value = value.replace("\\n", " ")
    return re.sub(r"\s+", " ", value).strip()


def short_text(value, limit=250):
    text = clean(value)
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(".,;:") + "..."


def norm(value):
    return clean(value).lower()


def number(value):
    try:
        return float(clean(value).replace(",", "").replace("₹", ""))
    except (ValueError, TypeError):
        return None


def load_schemes():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {CSV_PATH}")

    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def is_pdf_url(url):
    if not clean(url):
        return False

    path = urlparse(clean(url)).path.lower()
    return path.endswith(".pdf")


def is_individual_scheme(scheme):
    """
    Exclude schemes specifically intended for NGOs or
    voluntary organisations, rather than individual applicants.
    """
    name = norm(scheme.get("name"))
    beneficiary = norm(scheme.get("beneficiary_type"))
    category = norm(scheme.get("category"))
    description = norm(scheme.get("description"))
    eligibility = norm(scheme.get("eligibility_text"))

    organisation_terms = (
        "non-governmental organization",
        "non-governmental organisation",
        "non governmental organization",
        "non governmental organisation",
        "voluntary organization",
        "voluntary organisation",
        "voluntary organizations",
        "voluntary organisations",
    )

    if any(term in beneficiary for term in organisation_terms):
        return False

    if any(term in name for term in organisation_terms):
        return False

    if "ngo" in beneficiary:
        return False

    if re.search(r"\bfor ngos?\b", name):
        return False

    if "ngo" in category and not any(
        word in category for word in ("individual", "student", "person")
    ):
        return False

    organisation_only_phrases = (
        "assistance to voluntary organizations",
        "assistance to voluntary organisations",
        "grants to voluntary organizations",
        "grants to voluntary organisations",
        "financial assistance to ngos",
        "financial assistance to voluntary organizations",
        "financial assistance to voluntary organisations",
    )

    combined = " ".join((name, description, eligibility))

    if any(phrase in combined for phrase in organisation_only_phrases):
        return False

    return True


def location_matches(scheme, user_state):
    state = norm(scheme.get("state"))
    eligible_state = norm(scheme.get("eligibility_state"))
    combined = state + " " + eligible_state
    user_state = norm(user_state)

    if not state and not eligible_state:
        return True

    if "tamil nadu" in user_state or "tamilnadu" in user_state:
        return (
            "tamil nadu" in combined
            or "tamilnadu" in combined
            or "central" in combined
            or "india" in combined
            or not eligible_state
        )

    return (
        user_state in combined
        or "central" in combined
        or "india" in combined
        or not eligible_state
    )


def gender_matches(scheme, gender):
    required = norm(scheme.get("eligibility_gender"))
    gender = norm(gender)

    if not required or required in ("all", "any", "both"):
        return True

    if gender in ("transgender person", "transgender", "other"):
        return not any(
            word in required
            for word in ("female only", "male only", "women only", "men only")
        )

    if gender in required:
        return True

    if "female" in required or "women" in required:
        return gender in ("female", "woman")

    if "male" in required or "men" in required:
        return gender in ("male", "man")

    return True


def caste_matches(scheme, caste):
    required = norm(scheme.get("eligibility_caste"))
    caste = norm(caste)

    if not required or required in ("all", "any"):
        return True

    aliases = {
        "sc": ("sc", "scheduled caste", "adi dravidar"),
        "st": ("st", "scheduled tribe"),
        "bc": ("bc", "backward class"),
        "mbc": ("mbc", "most backward class"),
        "obc": ("obc", "other backward class"),
        "general": ("general", "unreserved", "open category")
    }

    terms = aliases.get(caste, (caste,))
    return any(term in required for term in terms)


def basic_eligibility(scheme, user):
    age_min = number(scheme.get("eligibility_age_min"))
    age_max = number(scheme.get("eligibility_age_max"))
    income_max = number(scheme.get("eligibility_income_max"))

    if age_min is not None and user["age"] < age_min:
        return False

    if age_max is not None and user["age"] > age_max:
        return False

    if income_max is not None and user["annual_income"] > income_max:
        return False

    if not gender_matches(scheme, user["gender"]):
        return False

    if not caste_matches(scheme, user["caste"]):
        return False

    if not location_matches(scheme, user["state"]):
        return False

    return True


def scheme_text(scheme):
    return " ".join(
        norm(scheme.get(field))
        for field in (
            "name", "description", "category", "benefits",
            "eligibility_text", "beneficiary_type"
        )
    )


def purpose_category(purpose):
    purpose = norm(purpose)

    if purpose in ("education", "scholarship", "financial assistance"):
        return "education"

    if "business" in purpose:
        return "business"

    if "employment" in purpose:
        return "employment"

    if "housing" in purpose:
        return "housing"

    if "health" in purpose:
        return "health"

    if "agriculture" in purpose:
        return "agriculture"

    if "women" in purpose:
        return "women"

    if "skill" in purpose:
        return "skill"

    return "other"


def purpose_score(scheme, category):
    text = scheme_text(scheme)

    keywords = {
        "education": [
            "scholarship", "student", "education", "school",
            "college", "university", "tuition", "fellowship",
            "academic", "educational assistance"
        ],
        "business": [
            "entrepreneur", "startup", "business", "enterprise",
            "business loan", "venture capital"
        ],
        "employment": [
            "employment", "job", "worker", "livelihood",
            "self employment", "vocational training"
        ],
        "housing": ["housing", "house construction", "home"],
        "health": ["health", "medical", "hospital", "treatment"],
        "agriculture": ["agriculture", "farmer", "farming", "crop"],
        "women": ["women", "woman", "girl", "maternity", "widow"],
        "skill": ["skill development", "vocational training", "training"]
    }

    return sum(2 for word in keywords.get(category, []) if word in text)


def unsuitable_for_undergraduate_scholarship(scheme):
    text = scheme_text(scheme)

    advanced_research = [
        "m.phil", "ph.d", "phd", "net-jrf", "net jrf",
        "research fellowship"
    ]

    special_employment = [
        "coffee plantation", "licensed coffee curing",
        "children of labourers", "children of laborers"
    ]

    return (
        any(word in text for word in advanced_research)
        or any(word in text for word in special_employment)
    )



def build_result(scheme, score, reasons, warnings):
    official_url = clean(scheme.get("official_url")) or clean(scheme.get("apply_url"))

    return {
        "scheme_name": clean(scheme.get("name")) or "Unnamed Scheme",
        "description": short_text(scheme.get("description"), 220),
        "ministry": short_text(scheme.get("ministry"), 80),
        "category": short_text(scheme.get("category"), 100),
        "benefits": short_text(scheme.get("benefits"), 250),
        "eligibility": short_text(scheme.get("eligibility_text"), 300),
        "eligibility_text": short_text(scheme.get("eligibility_text"), 300),
        "application_process": short_text(scheme.get("application_process"), 250),
        "documents_required": short_text(scheme.get("documents_required"), 180),
        "apply_url": "",
        "official_url": official_url,
        "action_url": official_url,
        "action_label": "Visit Official Website" if official_url else "Official Link Unavailable",
        "match_score": score,
        "match_reasons": reasons,
        "verification_required": warnings,
        "match_status": "Potential Match"
    }


def find_eligible_schemes(user_data):
    schemes = load_schemes()

    user = {
        "age": int(user_data["age"]),
        "gender": user_data["gender"],
        "state": user_data["state"],
        "caste": user_data["caste"],
        "annual_income": float(user_data["annual_income"])
    }

    category = purpose_category(user_data.get("purpose", "Other"))
    matches = []

    for scheme in schemes:
        # Only show schemes intended for individual applicants.
        if not is_individual_scheme(scheme):
            continue

        if not basic_eligibility(scheme, user):
            continue

        text = scheme_text(scheme)
        relevance = purpose_score(scheme, category)

        if category == "education":
            business_only = (
                "business & entrepreneurship" in norm(scheme.get("category"))
                and not any(word in text for word in (
                    "scholarship", "student", "education", "school", "college"
                ))
            )

            if business_only:
                continue

            if unsuitable_for_undergraduate_scholarship(scheme):
                continue

            if relevance == 0:
                continue

        elif relevance == 0 and category != "other":
            continue

        reasons = [
            "No conflicting age limit was found in the available dataset.",
            "No conflicting community restriction was found in the available dataset."
        ]

        if number(scheme.get("eligibility_income_max")) is not None:
            reasons.append("Your income is within the listed income limit.")
        else:
            reasons.append("The dataset does not specify an income limit.")

        reasons.append("The scheme information matches your selected purpose.")

        warnings = [
            "This is a potential match, not confirmed eligibility.",
            "Check the official website for complete conditions and application dates."
        ]

        if not clean(scheme.get("eligibility_text")):
            warnings.append("Detailed eligibility information is missing from the dataset.")

        if not clean(scheme.get("official_url")) and not clean(scheme.get("apply_url")):
            warnings.append("No official link was available in the dataset.")

        score = min(50 + relevance * 3, 95)

        matches.append(
            build_result(scheme, score, reasons, warnings)
        )

    matches.sort(key=lambda item: item["match_score"], reverse=True)
    return matches[:10]
