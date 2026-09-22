# dashboard/utils/country_names.py
#
# Small hardcoded ISO3-to-country-name lookup, scoped to the codes that
# actually appear in this dataset. Kept local (not pulled from dbt seeds)
# so the dashboard stays fully self-contained.

COUNTRY_NAMES = {
    "AFG": "Afghanistan", "AGO": "Angola", "ALB": "Albania", "ARE": "United Arab Emirates",
    "ARM": "Armenia", "AUS": "Australia", "AUT": "Austria", "AZE": "Azerbaijan",
    "BEL": "Belgium", "BEN": "Benin", "BGD": "Bangladesh", "BGR": "Bulgaria",
    "BHR": "Bahrain", "BIH": "Bosnia and Herzegovina", "BLR": "Belarus", "BOL": "Bolivia",
    "BRA": "Brazil", "BWA": "Botswana", "CAN": "Canada", "CHE": "Switzerland",
    "CHL": "Chile", "CHN": "China", "CIV": "C\u00f4te d'Ivoire", "CMR": "Cameroon",
    "COD": "DR Congo", "COL": "Colombia", "COM": "Comoros", "CPV": "Cabo Verde",
    "CRI": "Costa Rica", "CUB": "Cuba", "CZE": "Czechia", "DEU": "Germany",
    "DOM": "Dominican Republic", "DZA": "Algeria", "ECU": "Ecuador", "EGY": "Egypt",
    "ERI": "Eritrea", "ESP": "Spain", "EST": "Estonia", "ETH": "Ethiopia",
    "FJI": "Fiji", "FRA": "France", "GBR": "United Kingdom", "GEO": "Georgia",
    "GHA": "Ghana", "GMB": "Gambia", "GTM": "Guatemala", "GUY": "Guyana",
    "HND": "Honduras", "HRV": "Croatia", "HTI": "Haiti", "HUN": "Hungary",
    "IDN": "Indonesia", "IND": "India", "ISR": "Israel", "ITA": "Italy",
    "JAM": "Jamaica", "JOR": "Jordan", "JPN": "Japan", "KAZ": "Kazakhstan",
    "KEN": "Kenya", "KGZ": "Kyrgyzstan", "KHM": "Cambodia", "KOR": "South Korea",
    "KWT": "Kuwait", "LAO": "Laos", "LBN": "Lebanon", "LBR": "Liberia",
    "LKA": "Sri Lanka", "LSO": "Lesotho", "LTU": "Lithuania", "LVA": "Latvia",
    "MAR": "Morocco", "MDA": "Moldova", "MDG": "Madagascar", "MEX": "Mexico",
    "MKD": "North Macedonia", "MLI": "Mali", "MMR": "Myanmar", "MOZ": "Mozambique",
    "MWI": "Malawi", "MYS": "Malaysia", "NAM": "Namibia", "NGA": "Nigeria",
    "NIC": "Nicaragua", "NLD": "Netherlands", "NOR": "Norway", "NPL": "Nepal",
    "NZL": "New Zealand", "OMN": "Oman", "PAK": "Pakistan", "PAN": "Panama",
    "PER": "Peru", "PHL": "Philippines", "POL": "Poland", "PRT": "Portugal",
    "PRY": "Paraguay", "PSE": "Palestine", "QAT": "Qatar", "ROU": "Romania",
    "RUS": "Russia", "RWA": "Rwanda", "SAU": "Saudi Arabia", "SDN": "Sudan",
    "SEN": "Senegal", "SGP": "Singapore", "SLE": "Sierra Leone", "SLV": "El Salvador",
    "SOM": "Somalia", "SRB": "Serbia", "SSD": "South Sudan", "SUR": "Suriname",
    "SWE": "Sweden", "SWZ": "Eswatini", "SYR": "Syria", "TGO": "Togo",
    "THA": "Thailand", "TJK": "Tajikistan", "TON": "Tonga", "TUN": "Tunisia",
    "TUR": "Turkey", "TZA": "Tanzania", "UGA": "Uganda", "UKR": "Ukraine",
    "USA": "United States", "UZB": "Uzbekistan", "VNM": "Vietnam", "VUT": "Vanuatu",
    "WSM": "Samoa", "XKX": "Kosovo", "YEM": "Yemen", "ZAF": "South Africa",
    "ZMB": "Zambia", "ZWE": "Zimbabwe",
}


def country_name(iso3_code: str) -> str:
    return COUNTRY_NAMES.get(iso3_code, iso3_code)


def corridor_label(sending_code: str, receiving_code: str) -> str:
    return f"{country_name(sending_code)} \u2192 {country_name(receiving_code)}"
