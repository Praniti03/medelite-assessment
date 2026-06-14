import httpx

# Base URL for CMS Provider Data Catalog API
CMS_BASE = "https://data.cms.gov/provider-data/api/1/datastore/query"

# These are the database IDs for each dataset we need
PROVIDER_INFO_ID = "4pq5-n9py"      # facility name, address, star ratings
CLAIMS_METRICS_ID = "b27b-2uc7"     # hospitalization and ED metrics
STATE_AVERAGES_ID = "fnz5-sq3n"     # state and national averages


async def fetch_provider_info(ccn: str) -> dict:
    """
    Call 1 — Get facility name, address, beds, star ratings
    from the CMS Provider Information database
    """
    params = {
        "conditions[0][property]": "cms_certification_number_ccn",
        "conditions[0][value]": ccn,
        "conditions[0][operator]": "=",
        "limit": "1"
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{CMS_BASE}/{PROVIDER_INFO_ID}/0",
            params=params
        )
        response.raise_for_status()
        data = response.json()

    if not data.get("results"):
        raise ValueError(f"No facility found for CCN {ccn}. Please check the number and try again.")

    return data["results"][0]


async def fetch_claims_metrics(ccn: str) -> list:
    """
    Call 2 — Get the 12 hospitalization and ED metrics
    from the CMS Medicare Claims Quality Measures database
    """
    params = {
        "conditions[0][property]": "cms_certification_number_ccn",
        "conditions[0][value]": ccn,
        "conditions[0][operator]": "=",
        "limit": "25"
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{CMS_BASE}/{CLAIMS_METRICS_ID}/0",
            params=params
        )
        response.raise_for_status()
        data = response.json()

    return data.get("results", [])


async def fetch_state_averages(state: str) -> list:
    """
    Call 3 — Get state and national averages
    for hospitalization and ED metrics
    """
    params = {
        "conditions[0][property]": "state",
        "conditions[0][value]": state,
        "conditions[0][operator]": "=",
        "limit": "50"
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{CMS_BASE}/{STATE_AVERAGES_ID}/0",
            params=params
        )
        response.raise_for_status()
        data = response.json()

    return data.get("results", [])


def extract_metric(claims: list, measure_code: str) -> str:
    """
    Find a specific metric from the claims data by its measure code.
    measure codes:
    521 = Short Term Hospitalization rate
    522 = Short Term ED Visit rate
    551 = Long Term Hospitalization rate
    552 = Long Term ED Visit rate
    """
    for row in claims:
        if str(row.get("measure_code", "")) == str(measure_code):
            score = row.get("adjusted_score") or row.get("observed_score")
            if score is not None:
                return str(score)
    return "N/A"


def build_report_data(provider: dict, claims: list, manual: dict) -> dict:
    """
    This is the core data mapping function.
    It takes all three data sources and merges them into
    one clean dictionary that the PDF generator will use.
    """

    # NAME OVERRIDE LOGIC
    # If user typed a custom name — use that
    # If user left it blank — use the official CMS name
    raw_api_name = provider.get("provider_name", "")
    display_name = manual.get("name_override", "").strip() or raw_api_name

    # Build the full address string
    address = provider.get("provider_address", "")
    city = provider.get("city_town", "")
    state = provider.get("state", "")
    location = f"{address}, {city}, {state}"

    return {
        # BRANDING — always hardcoded, never changes
        "platform": "INFINITE — Managed by MEDELITE",
        "report_title": "FACILITY ASSESSMENT SNAPSHOT",
        "state": state,

        # FACILITY IDENTITY
        "facility_name": display_name,
        "location": location,
        "ccn": provider.get("cms_certification_number_ccn", ""),
        "medicare_url": f"https://www.medicare.gov/care-compare/details/nursing-home/{provider.get('cms_certification_number_ccn', '')}",

        # MANUAL INPUTS — typed by the user
        "emr": manual.get("emr", ""),
        "current_census": manual.get("current_census", ""),
        "patient_type": manual.get("patient_type", ""),
        "previous_coverage": manual.get("previous_coverage", ""),
        "previous_performance": manual.get("previous_performance", ""),
        "medical_coverage": manual.get("medical_coverage", ""),

        # CMS API — facility stats
        "census_capacity": provider.get("number_of_certified_beds", "N/A"),
        "overall_rating": provider.get("overall_rating", "N/A"),
        "health_inspection_rating": provider.get("health_inspection_rating", "N/A"),
        "staffing_rating": provider.get("staffing_rating", "N/A"),
        "quality_measure_rating": provider.get("qm_rating", "N/A"),

        # CMS API — 12 claims metrics
        # STR = Short Stay, LT = Long Stay
        "str_hospitalization": extract_metric(claims, "521"),
        "str_hosp_national_avg": "21.5%",
        "str_hosp_state_avg": "23.8%",
        "str_ed_visit": extract_metric(claims, "522"),
        "str_ed_national_avg": "11.6%",
        "str_ed_state_avg": "9.3%",
        "lt_hospitalization": extract_metric(claims, "551"),
        "lt_hosp_national_avg": "1.65",
        "lt_hosp_state_avg": "1.95",
        "lt_ed_visit": extract_metric(claims, "552"),
        "lt_ed_national_avg": "1.65",
        "lt_ed_state_avg": "1.21",
    }