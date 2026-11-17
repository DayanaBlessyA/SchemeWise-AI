
const form = document.getElementById("schemeForm");
const button = document.getElementById("submitBtn");

const fields = [
    document.getElementById("age"),
    document.getElementById("gender"),
    document.getElementById("state"),
    document.getElementById("caste"),
    document.getElementById("income"),
    document.getElementById("purpose")
];

const resultsSection = document.getElementById("results");
const resultCount = document.getElementById("resultCount");
const schemeList = document.getElementById("schemeList");
const aiExplanation = document.getElementById("aiExplanation");
const disclaimer = document.getElementById("disclaimer");


function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}


function safeURL(value) {
    try {
        const url = new URL(value);

        if (url.protocol === "https:" || url.protocol === "http:") {
            return url.href;
        }
    } catch (error) {
        return "";
    }

    return "";
}


function setSearching(searching) {
    fields.forEach(field => {
        field.disabled = searching;
    });

    button.disabled = searching;
    button.textContent = searching
        ? "Finding your schemes..."
        : "Find My Schemes";
}


function showMessage(message) {
    schemeList.innerHTML = `
        <div class="no-results">
            ${escapeHTML(message)}
        </div>
    `;
}


function displaySchemes(data) {
    const results = Array.isArray(data.results) ? data.results : [];

    resultCount.textContent =
        `${data.total_matches ?? results.length} potential matches found`;

    if (results.length === 0) {
        showMessage(
            "No potential matches were found. Try reviewing your details or selecting another purpose."
        );
        return;
    }

    schemeList.innerHTML = results.map((scheme, index) => {
        const checks = Array.isArray(scheme.verification_required)
            ? scheme.verification_required
            : [];

        const actionURL = safeURL(scheme.action_url);
        const actionLabel = "Visit Official Website";

        return `
            <article class="scheme-card">
                <div class="scheme-number">Scheme ${index + 1}</div>

                <h3>${escapeHTML(scheme.scheme_name || "Unnamed Scheme")}</h3>

                <p>${escapeHTML(scheme.description || "Description not available.")}</p>

                <h4>Benefits</h4>
                <p>${escapeHTML(scheme.benefits || "Check the official website for details.")}</p>

                <h4>Eligibility</h4>
                <p>${escapeHTML(scheme.eligibility || "Check the official website for eligibility conditions.")}</p>

                ${scheme.ministry ? `
                    <p><strong>Ministry:</strong> ${escapeHTML(scheme.ministry)}</p>
                ` : ""}

                ${scheme.category ? `
                    <p><strong>Category:</strong> ${escapeHTML(scheme.category)}</p>
                ` : ""}

                ${scheme.application_process ? `
                    <h4>How to apply</h4>
                    <p>${escapeHTML(scheme.application_process)}</p>
                ` : ""}

                ${checks.length ? `
                    <div class="scheme-notice">
                        <strong>Before applying:</strong>
                        <ul>
                            ${checks.map(check => `<li>${escapeHTML(check)}</li>`).join("")}
                        </ul>
                    </div>
                ` : ""}

                <div class="scheme-links">
                    ${actionURL ? `
                        <a href="${escapeHTML(actionURL)}"
                           target="_blank"
                           rel="noopener noreferrer">
                            ${escapeHTML(actionLabel)}
                        </a>
                    ` : `
                        <span>Official link unavailable</span>
                    `}
                </div>
            </article>
        `;
    }).join("");
}


form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const missingField = fields.find(field => !field.value.trim());

    if (missingField) {
        alert("Please fill in all six fields before finding schemes.");
        missingField.focus();
        return;
    }

    const age = Number(document.getElementById("age").value);
    const income = Number(document.getElementById("income").value);

    if (!Number.isInteger(age) || age < 0 || age > 120) {
        alert("Please enter a valid age between 0 and 120.");
        return;
    }

    if (!Number.isFinite(income) || income < 0) {
        alert("Please enter a valid annual income.");
        return;
    }

    const profile = {
        age: age,
        gender: document.getElementById("gender").value,
        state: document.getElementById("state").value,
        caste: document.getElementById("caste").value,
        annual_income: income,
        purpose: document.getElementById("purpose").value
    };

    setSearching(true);

    resultsSection.hidden = false;
    resultCount.textContent = "Searching...";
    schemeList.innerHTML = "";
    aiExplanation.textContent = "Finding schemes that may match your profile...";
    disclaimer.textContent = "";

    try {
        const response = await fetch("/schemes/explain", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(profile)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Something went wrong.");
        }

        displaySchemes(data);

        aiExplanation.textContent =
            data.ai_explanation || "No explanation is available.";

        disclaimer.textContent =
            data.disclaimer || "These are potential matches. Verify eligibility and application dates on official websites.";

    } catch (error) {
        resultCount.textContent = "Search unsuccessful";
        showMessage(error.message || "Unable to find schemes. Please try again.");
        aiExplanation.textContent = "";
        disclaimer.textContent = "";
    } finally {
        setSearching(false);
    }
});
