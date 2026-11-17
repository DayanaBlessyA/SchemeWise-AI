import os
from dotenv import load_dotenv

load_dotenv()


def explain_schemes(user_data, results):
    if not results:
        return (
            "No potential matches were found using the details provided. "
            "You can try reviewing your details or checking official "
            "government portals for additional schemes."
        )

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return fallback_explanation(user_data, results)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-2.0-flash")

        scheme_details = []

        for scheme in results[:5]:
            scheme_details.append(
                f"Scheme: {scheme['scheme_name']}\n"
                f"Benefits: {scheme['benefits']}\n"
                f"Eligibility: {scheme['eligibility']}\n"
            )

        prompt = f"""
You are SchemeWise AI, a government scheme information assistant.

Explain these potential government scheme matches in simple English.

User details:
Age: {user_data['age']}
Gender: {user_data['gender']}
State: {user_data['state']}
Community: {user_data['caste']}
Annual income: {user_data['annual_income']}
Purpose: {user_data['purpose']}

Potential matching schemes:
{chr(10).join(scheme_details)}

Instructions:
1. Briefly explain why these schemes may be relevant.
2. Use simple language.
3. Do not claim the user is definitely eligible.
4. Do not invent benefits or eligibility conditions.
5. Tell the user to verify details on official websites.
"""

        response = model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()

        return fallback_explanation(user_data, results)

    except Exception:
        return fallback_explanation(user_data, results)


def fallback_explanation(user_data, results):
    return (
        f"We found {len(results)} potential scheme matches based on your "
        f"profile and selected purpose, {user_data['purpose']}. "
        "The schemes are ranked using the available eligibility information "
        "and relevance to your selected purpose. Please read each scheme's "
        "eligibility conditions and verify the latest information on its "
        "official government website before applying."
    )
