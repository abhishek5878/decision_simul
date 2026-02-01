"""
derive_features.py - Feature Derivation for Credigo.club Audience Simulation

This module derives behavioral and psychographic features from the 28 raw persona fields.
These derived features power the step-by-step journey simulation predictions.

Key Derived Features (with 0-10 scoring where applicable):
1. Urban/Rural Proxy - Metro/Urban/Semi-Urban/Rural classification
2. Regional Cultural Cluster - North/South/East/West/Northeast/Central
3. Primary Language + English Proficiency (0-10 scale)
4. Aspirational Intensity (0-10 scale) - Growth/wealth vs. stability
5. Digital Literacy Proxy (0-10 scale) - Age + education + occupation
6. Trust/Risk Orientation (0-10 scale) - Conservative vs. open
7. Status Quo Sufficiency (0-10 scale) - Satisfaction with current state
8. Openness/Hobby Breadth (0-10 scale) - Diversity of interests
9. Generation Bucket - Gen Z, Millennial, Gen X, Boomer
10. Credit Card Relevance Score (0-10 composite)
11. Privacy Sensitivity (0-10) - How much privacy claims matter
12. Debt Aversion (0-10) - Fear of credit/debt

All rules calibrated for 2025 India FinTech context.
"""

import pandas as pd
import re
from typing import Dict, List, Optional, Tuple
import warnings


# ============================================================================
# GEOGRAPHIC CLASSIFICATIONS (2025 India)
# ============================================================================

# Regional zone mapping based on dataset's zone field
REGIONAL_CLUSTERS = {
    'North': ['NORTHERN', 'CENTRAL', 'NORTH'],
    'South': ['SOUTHERN', 'SOUTH'],
    'East': ['EASTERN', 'EAST'],
    'West': ['WESTERN', 'WEST'],
    'Northeast': ['NORTH EASTERN', 'NORTH-EASTERN', 'NORTHEAST', 'NE']
}

# States by regional cluster (comprehensive mapping)
STATE_TO_REGION = {
    # North
    'Delhi': 'North', 'Haryana': 'North', 'Punjab': 'North', 
    'Uttar Pradesh': 'North', 'Uttarakhand': 'North', 'Himachal Pradesh': 'North',
    'Jammu and Kashmir': 'North', 'Ladakh': 'North', 'Chandigarh': 'North',
    'Rajasthan': 'North', 'Madhya Pradesh': 'Central',
    # South
    'Tamil Nadu': 'South', 'Kerala': 'South', 'Karnataka': 'South',
    'Andhra Pradesh': 'South', 'Telangana': 'South', 'Puducherry': 'South',
    'Lakshadweep': 'South',
    # East
    'West Bengal': 'East', 'Odisha': 'East', 'Bihar': 'East', 
    'Jharkhand': 'East', 'Chhattisgarh': 'East',
    # West
    'Maharashtra': 'West', 'Gujarat': 'West', 'Goa': 'West',
    'Dadra and Nagar Haveli': 'West', 'Daman and Diu': 'West',
    # Northeast
    'Assam': 'Northeast', 'Meghalaya': 'Northeast', 'Manipur': 'Northeast',
    'Mizoram': 'Northeast', 'Tripura': 'Northeast', 'Nagaland': 'Northeast',
    'Arunachal Pradesh': 'Northeast', 'Sikkim': 'Northeast',
    # Island territories
    'Andaman and Nicobar Islands': 'South'
}

# Tier-1 cities and their districts (metro/urban indicators)
TIER1_METRO_DISTRICTS = [
    'Mumbai', 'Delhi', 'Bengaluru', 'Bangalore', 'Hyderabad', 'Chennai', 
    'Kolkata', 'Pune', 'Ahmedabad', 'Surat', 'Lucknow', 'Jaipur',
    'North Delhi', 'South Delhi', 'East Delhi', 'West Delhi', 'Central Delhi',
    'New Delhi', 'Gurugram', 'Gurgaon', 'Noida', 'Ghaziabad', 'Faridabad',
    'Thane', 'Mumbai Suburban', 'Navi Mumbai'
]

# Tier-2 cities (semi-urban/aspirational)
TIER2_URBAN_DISTRICTS = [
    'Chandigarh', 'Coimbatore', 'Indore', 'Nagpur', 'Bhopal', 'Visakhapatnam',
    'Patna', 'Vadodara', 'Ludhiana', 'Agra', 'Nashik', 'Rajkot', 'Varanasi',
    'Thiruvananthapuram', 'Kochi', 'Madurai', 'Mysuru', 'Mysore', 'Mangalore',
    'Bhubaneswar', 'Ranchi', 'Raipur', 'Vijayawada', 'Jodhpur', 'Amritsar',
    'Dehradun', 'Udaipur', 'Guwahati', 'Kanpur', 'Meerut', 'Allahabad',
    'Prayagraj', 'Jabalpur', 'Gwalior', 'Aurangabad', 'Hubli', 'Belgaum',
    'Tiruchirappalli', 'Salem', 'Tirupati', 'Warangal', 'Guntur'
]


# ============================================================================
# OCCUPATION & EDUCATION PATTERNS
# ============================================================================

# High digital literacy occupations (IT, professional services, modern sector)
DIGITAL_NATIVE_OCCUPATIONS = [
    'software', 'engineer', 'developer', 'programmer', 'it ', 'tech', 
    'computer', 'data', 'analyst', 'digital', 'web', 'mobile', 'app',
    'consultant', 'manager', 'executive', 'marketing', 'advertising',
    'finance', 'banking', 'investment', 'startup', 'entrepreneur',
    'designer', 'architect', 'product', 'business', 'sales', 'corporate',
    'professional', 'associate', 'specialist', 'coordinator', 'lead'
]

# Traditional/stability-oriented occupations
TRADITIONAL_OCCUPATIONS = [
    'farmer', 'agricultural', 'cultivation', 'farming', 'fisherman',
    'teacher', 'professor', 'lecturer', 'government', 'govt', 'psu',
    'clerk', 'officer', 'inspector', 'police', 'military', 'army',
    'railway', 'postal', 'bank clerk', 'accountant', 'cashier',
    'shopkeeper', 'trader', 'merchant', 'vendor', 'artisan', 'craftsman',
    'carpenter', 'blacksmith', 'weaver', 'tailor', 'electrician', 'plumber',
    'driver', 'labourer', 'worker', 'helper', 'peon', 'attendant'
]

# Aspirational/entrepreneurial occupations
ASPIRATIONAL_OCCUPATIONS = [
    'ceo', 'founder', 'director', 'entrepreneur', 'startup',
    'business owner', 'investor', 'venture', 'consultant', 'freelance',
    'influencer', 'content creator', 'youtuber', 'artist', 'musician',
    'actor', 'filmmaker', 'photographer', 'fashion', 'model'
]

# Education levels indicating higher digital literacy
HIGH_EDUCATION_LEVELS = [
    'graduate', 'post-graduate', 'postgraduate', 'master', 'mba', 'mtech',
    'phd', 'doctorate', 'professional', 'engineering', 'medical', 'law',
    'bachelor', 'degree', 'diploma'
]


# ============================================================================
# CAREER GOALS & AMBITIONS PATTERNS (for 0-10 scoring)
# ============================================================================

# High aspirational intensity keywords (+1 each, max contributions)
HIGH_ASPIRATION_KEYWORDS = [
    'wealth', 'rich', 'millionaire', 'success', 'successful', 'growth',
    'promotion', 'leadership', 'ceo', 'director', 'own business', 'startup',
    'entrepreneur', 'venture', 'invest', 'property', 'real estate', 'abroad',
    'international', 'global', 'innovation', 'impact', 'transform', 'scale',
    'achieve', 'ambition', 'dream', 'aspire', 'excel', 'top', 'best',
    'premium', 'luxury', 'upgrade', 'career growth', 'climb', 'advance',
    'travel', 'explore', 'experience', 'lifestyle', 'freedom'
]

# Stability/conservative orientation keywords (-0.5 each from aspirational)
STABILITY_KEYWORDS = [
    'stable', 'stability', 'secure', 'security', 'pension', 'retirement',
    'government', 'govt job', 'permanent', 'settled', 'family', 'support',
    'maintain', 'preserve', 'traditional', 'routine', 'regular', 'safe',
    'risk-free', 'guaranteed', 'fixed', 'steady', 'reliable', 'dependable',
    'simple', 'peaceful', 'content', 'satisfy', 'enough', 'sufficient'
]

# Debt aversion keywords (for debt_aversion_score)
DEBT_AVERSION_KEYWORDS = [
    'debt', 'loan', 'emi', 'borrow', 'credit', 'interest', 'repay',
    'savings', 'save', 'frugal', 'budget', 'careful', 'cautious',
    'risk-free', 'no risk', 'safe', 'secure'
]

# Privacy sensitivity keywords
PRIVACY_SENSITIVE_KEYWORDS = [
    'private', 'privacy', 'data', 'information', 'secure', 'security',
    'trust', 'confidential', 'personal', 'identity', 'spam', 'calls'
]


# ============================================================================
# FEATURE DERIVATION FUNCTIONS (Enhanced with 0-10 scales)
# ============================================================================

def derive_urban_rural(row: pd.Series) -> Tuple[str, int]:
    """
    Derive urban/rural classification from district and state.
    
    Returns: (category, urbanization_score 0-10)
        Metro = 10, Urban = 7, Semi-Urban = 4, Rural = 1
    """
    district = str(row.get('district', '')).lower()
    state = str(row.get('state', '')).lower()
    
    # Check for Tier-1 metro cities
    for city in TIER1_METRO_DISTRICTS:
        if city.lower() in district or city.lower() in state:
            return ('Metro', 10)
    
    # Check for Tier-2 cities
    for city in TIER2_URBAN_DISTRICTS:
        if city.lower() in district:
            return ('Urban', 7)
    
    # State capitals and major district HQs
    capital_indicators = ['capital', 'municipal', 'corporation', 'metro', 'urban', 'city']
    if any(ind in district for ind in capital_indicators):
        return ('Urban', 7)
    
    # Check for semi-urban indicators
    semi_urban_indicators = ['town', 'nagar', 'pur', 'pura', 'puram', 'bad', 'abad']
    if any(ind in district for ind in semi_urban_indicators):
        return ('Semi-Urban', 4)
    
    # Default to Rural
    return ('Rural', 1)


def derive_regional_cluster(row: pd.Series) -> str:
    """
    Derive regional cultural cluster from zone and state.
    
    Returns: 'North', 'South', 'East', 'West', 'Northeast', 'Central'
    """
    zone = str(row.get('zone', '')).upper()
    state = str(row.get('state', ''))
    
    # First try state mapping (more reliable)
    for state_name, region in STATE_TO_REGION.items():
        if state_name.lower() in state.lower():
            return region
    
    # Fallback to zone field
    for region, zone_keywords in REGIONAL_CLUSTERS.items():
        if any(kw in zone for kw in zone_keywords):
            return region
    
    return 'Central'  # Default for ambiguous cases


def derive_english_proficiency(row: pd.Series) -> Tuple[str, int]:
    """
    Derive English proficiency level from language fields + education.
    
    Returns: (category, proficiency_score 0-10)
        Native = 10, Fluent = 8, Moderate = 5, Basic = 3, None = 0
    """
    first_lang = str(row.get('first_language', '')).lower()
    second_lang = str(row.get('second_language', '')).lower()
    third_lang = str(row.get('third_language', '')).lower()
    education = str(row.get('education_level', '')).lower()
    
    # Check English position
    if 'english' in first_lang:
        return ('Native', 10)
    elif 'english' in second_lang:
        # If graduate+ with English as 2nd language = Fluent
        if any(level in education for level in HIGH_EDUCATION_LEVELS):
            return ('Fluent', 8)
        return ('Moderate', 5)
    elif 'english' in third_lang:
        return ('Basic', 3)
    
    # Education level as proxy (no explicit English)
    if any(level in education for level in ['professional', 'post-graduate', 'graduate']):
        return ('Basic', 3)
    elif 'higher secondary' in education or '12th' in education:
        return ('Minimal', 2)
    
    return ('None', 0)


def derive_primary_language(row: pd.Series) -> str:
    """Extract primary language from first_language field."""
    first_lang = str(row.get('first_language', ''))
    return first_lang if first_lang and first_lang.lower() != 'nan' else 'Hindi'


def derive_aspirational_intensity(row: pd.Series) -> Tuple[str, int]:
    """
    Derive aspirational intensity (0-10 scale) from career goals, ambitions, persona.
    
    High aspiration: growth, wealth, entrepreneurship, travel, lifestyle
    Low aspiration: stability, government job, security, routine
    
    Returns: (category, score 0-10)
    """
    goals = str(row.get('career_goals_and_ambitions', '')).lower()
    persona = str(row.get('persona', '')).lower()
    professional = str(row.get('professional_persona', '')).lower()
    occupation = str(row.get('occupation', '')).lower()
    
    combined_text = f"{goals} {persona} {professional} {occupation}"
    
    # Count high aspiration signals
    high_count = sum(1 for kw in HIGH_ASPIRATION_KEYWORDS if kw in combined_text)
    
    # Count stability signals (reduces aspirational score)
    stability_count = sum(1 for kw in STABILITY_KEYWORDS if kw in combined_text)
    
    # Aspirational occupations boost
    aspiration_boost = 2 if any(occ in occupation for occ in ASPIRATIONAL_OCCUPATIONS) else 0
    
    # Calculate raw score
    raw_score = min(10, high_count) - (stability_count * 0.5) + aspiration_boost
    
    # Normalize to 0-10
    score = max(0, min(10, int(raw_score * 1.2)))
    
    # Categorize
    if score >= 7:
        return ('High', score)
    elif score >= 4:
        return ('Medium', score)
    else:
        return ('Low', score)


def derive_digital_literacy(row: pd.Series) -> Tuple[str, int]:
    """
    Derive digital literacy proxy (0-10 scale).
    
    Formula: Age factor + Education factor + Occupation factor + Urban factor
    
    Returns: (category, score 0-10)
    """
    age = int(row.get('age', 40))
    education = str(row.get('education_level', '')).lower()
    occupation = str(row.get('occupation', '')).lower()
    urban_rural, urban_score = derive_urban_rural(row)
    
    score = 0
    
    # Age factor (0-3 points) - younger = more digital native
    if age < 25:
        score += 3
    elif age < 35:
        score += 2.5
    elif age < 45:
        score += 1.5
    elif age < 55:
        score += 0.5
    # 55+ gets 0
    
    # Education factor (0-3 points)
    if any(level in education for level in ['professional', 'post-graduate', 'engineering']):
        score += 3
    elif any(level in education for level in ['graduate', 'bachelor', 'diploma']):
        score += 2
    elif 'higher secondary' in education or '12th' in education:
        score += 1
    elif 'secondary' in education or '10th' in education:
        score += 0.5
    
    # Occupation factor (0-3 points)
    if any(occ in occupation for occ in DIGITAL_NATIVE_OCCUPATIONS):
        score += 3
    elif any(occ in occupation for occ in ASPIRATIONAL_OCCUPATIONS):
        score += 2
    elif 'student' in occupation.lower():
        score += 2.5  # Students are generally digital
    elif any(occ in occupation for occ in TRADITIONAL_OCCUPATIONS):
        score += 0.5
    
    # Urban factor (0-1 point)
    score += urban_score / 10  # Normalized urban contribution
    
    # Normalize to 0-10
    final_score = max(0, min(10, int(score)))
    
    if final_score >= 7:
        return ('High', final_score)
    elif final_score >= 4:
        return ('Medium', final_score)
    else:
        return ('Low', final_score)


def derive_trust_risk_orientation(row: pd.Series) -> Tuple[str, int]:
    """
    Derive trust/risk orientation (0-10 scale, where 10 = very conservative/risk-averse).
    
    Conservative: High trust threshold, risk averse, traditional
    Open: Lower trust threshold, risk tolerant, entrepreneurial
    
    Returns: (category, conservatism_score 0-10)
    """
    goals = str(row.get('career_goals_and_ambitions', '')).lower()
    cultural = str(row.get('cultural_background', '')).lower()
    occupation = str(row.get('occupation', '')).lower()
    age = int(row.get('age', 40))
    marital = str(row.get('marital_status', '')).lower()
    
    combined = f"{goals} {cultural} {occupation}"
    
    # Start with neutral
    conservatism = 5
    
    # Stability keywords increase conservatism
    stability_count = sum(1 for kw in STABILITY_KEYWORDS if kw in combined)
    conservatism += min(3, stability_count * 0.5)
    
    # Age factor (older = more conservative)
    if age > 55:
        conservatism += 2
    elif age > 45:
        conservatism += 1
    elif age < 30:
        conservatism -= 1.5
    elif age < 25:
        conservatism -= 2
    
    # Married with family = more conservative
    if 'married' in marital:
        conservatism += 0.5
    
    # Traditional occupations = more conservative
    if any(occ in occupation for occ in TRADITIONAL_OCCUPATIONS):
        conservatism += 1
    
    # Aspirational/entrepreneurial = less conservative
    if any(occ in occupation for occ in ASPIRATIONAL_OCCUPATIONS):
        conservatism -= 2
    
    # High aspiration keywords reduce conservatism
    aspiration_count = sum(1 for kw in HIGH_ASPIRATION_KEYWORDS if kw in combined)
    conservatism -= min(2, aspiration_count * 0.3)
    
    score = max(0, min(10, int(conservatism)))
    
    if score >= 7:
        return ('Conservative', score)
    elif score <= 3:
        return ('Open', score)
    else:
        return ('Moderate', score)


def derive_status_quo_sufficiency(row: pd.Series) -> Tuple[str, int]:
    """
    Derive status quo sufficiency (0-10 scale).
    
    High: "My current solutions work fine, why change?"
    Low: "I'm actively looking for better options"
    
    Returns: (category, score 0-10)
    """
    goals = str(row.get('career_goals_and_ambitions', '')).lower()
    cultural = str(row.get('cultural_background', '')).lower()
    age = int(row.get('age', 40))
    marital = str(row.get('marital_status', '')).lower()
    urban_rural, urban_score = derive_urban_rural(row)
    
    # Base score
    score = 5
    
    # Stability keywords indicate high status quo sufficiency
    stability_count = sum(1 for kw in STABILITY_KEYWORDS if kw in goals)
    score += min(3, stability_count * 0.5)
    
    # Growth keywords indicate low status quo sufficiency
    growth_count = sum(1 for kw in HIGH_ASPIRATION_KEYWORDS if kw in goals)
    score -= min(3, growth_count * 0.4)
    
    # Age factor (older = more status quo satisfied)
    if age > 60:
        score += 2.5
    elif age > 50:
        score += 1.5
    elif age > 40:
        score += 0.5
    elif age < 30:
        score -= 1.5
    elif age < 25:
        score -= 2
    
    # Married = more status quo
    if 'married' in marital:
        score += 0.5
    
    # Rural = more status quo (UPI habit established, local ecosystem)
    if urban_rural == 'Rural':
        score += 1.5
    elif urban_rural == 'Metro':
        score -= 1
    
    final_score = max(0, min(10, int(score)))
    
    if final_score >= 7:
        return ('High', final_score)
    elif final_score <= 3:
        return ('Low', final_score)
    else:
        return ('Medium', final_score)


def derive_openness_hobby_breadth(row: pd.Series) -> Tuple[str, int]:
    """
    Derive openness/hobby breadth (0-10 scale).
    
    Counts diversity across sports, arts, travel, culinary personas.
    More diverse = more open to new experiences (including apps).
    
    Returns: (category, score 0-10)
    """
    hobbies = str(row.get('hobbies_and_interests', ''))
    sports = str(row.get('sports_persona', ''))
    arts = str(row.get('arts_persona', ''))
    travel = str(row.get('travel_persona', ''))
    culinary = str(row.get('culinary_persona', ''))
    
    score = 0
    
    # Count substantial content in each persona area (min 50 chars = engaged)
    if len(sports) > 50:
        score += 2
    if len(arts) > 50:
        score += 2
    if len(travel) > 50:
        score += 2
    if len(culinary) > 50:
        score += 2
    
    # Count hobby keywords for extra points
    combined = f"{hobbies}".lower()
    hobby_keywords = ['reading', 'music', 'sports', 'travel', 'cooking', 'gaming',
                     'photography', 'art', 'dance', 'yoga', 'fitness', 'movies',
                     'writing', 'gardening', 'crafts', 'collection', 'hiking',
                     'adventure', 'social', 'community', 'volunteer']
    hobby_matches = sum(1 for kw in hobby_keywords if kw in combined)
    score += min(2, hobby_matches * 0.3)
    
    final_score = max(0, min(10, int(score)))
    
    if final_score >= 7:
        return ('Broad', final_score)
    elif final_score >= 4:
        return ('Moderate', final_score)
    else:
        return ('Narrow', final_score)


def derive_generation_bucket(row: pd.Series) -> Tuple[str, str]:
    """
    Derive generational bucket from age.
    
    Based on 2025 context:
    - Gen Z: 18-24 (born 2001-2007)
    - Young Millennial: 25-32 (born 1993-2000)
    - Core Millennial: 33-40 (born 1985-1992)
    - Gen X: 41-56 (born 1969-1984)
    - Boomer: 57+ (born before 1969)
    
    Returns: (bucket_name, bucket_code)
    """
    age = int(row.get('age', 40))
    
    if age <= 24:
        return ('Gen Z', 'GEN_Z')
    elif age <= 32:
        return ('Young Millennial', 'YOUNG_MILL')
    elif age <= 40:
        return ('Core Millennial', 'CORE_MILL')
    elif age <= 56:
        return ('Gen X', 'GEN_X')
    else:
        return ('Boomer', 'BOOMER')


def derive_debt_aversion(row: pd.Series) -> Tuple[str, int]:
    """
    Derive debt aversion score (0-10 scale).
    
    High: Strong fear of credit/debt, prefers cash/debit
    Low: Comfortable with credit as financial tool
    
    Returns: (category, score 0-10)
    """
    goals = str(row.get('career_goals_and_ambitions', '')).lower()
    cultural = str(row.get('cultural_background', '')).lower()
    occupation = str(row.get('occupation', '')).lower()
    age = int(row.get('age', 40))
    
    combined = f"{goals} {cultural}"
    
    # Base score (moderate)
    score = 5
    
    # Debt-related keywords increase aversion
    debt_mentions = sum(1 for kw in DEBT_AVERSION_KEYWORDS if kw in combined)
    score += min(3, debt_mentions * 0.5)
    
    # Age factor (middle-aged most debt-averse due to family responsibilities)
    if 40 <= age <= 55:
        score += 1.5
    elif age > 55:
        score += 1  # Conservative but less actively averse
    elif age < 25:
        score += 0.5  # Gen Z surprisingly debt-averse (seen EMI horror stories)
    
    # Traditional occupations = more debt averse
    if any(occ in occupation for occ in TRADITIONAL_OCCUPATIONS):
        score += 1
    
    # Aspirational occupations = less debt averse (see credit as tool)
    if any(occ in occupation for occ in ASPIRATIONAL_OCCUPATIONS):
        score -= 2
    
    # Stability keywords increase aversion
    stability_count = sum(1 for kw in STABILITY_KEYWORDS if kw in combined)
    score += min(2, stability_count * 0.3)
    
    final_score = max(0, min(10, int(score)))
    
    if final_score >= 7:
        return ('High', final_score)
    elif final_score <= 3:
        return ('Low', final_score)
    else:
        return ('Medium', final_score)


def derive_privacy_sensitivity(row: pd.Series) -> Tuple[str, int]:
    """
    Derive privacy sensitivity (0-10 scale).
    
    High: Very concerned about data privacy, spam calls, etc.
    Low: Less concerned, willing to share data for convenience
    
    Returns: (category, score 0-10)
    """
    age = int(row.get('age', 40))
    education = str(row.get('education_level', '')).lower()
    occupation = str(row.get('occupation', '')).lower()
    digital_cat, digital_score = derive_digital_literacy(row)
    trust_cat, trust_score = derive_trust_risk_orientation(row)
    
    # Base score influenced by digital literacy (more aware = more concerned)
    score = 3 + (digital_score * 0.3)
    
    # Conservative people care about privacy
    score += trust_score * 0.2
    
    # Educated professionals very privacy-aware
    if any(level in education for level in ['professional', 'post-graduate', 'engineering']):
        score += 1
    
    # IT/Tech people highly privacy aware
    if any(occ in occupation for occ in ['software', 'engineer', 'developer', 'data', 'security']):
        score += 1.5
    
    # Middle-aged parents extra cautious
    if 35 <= age <= 50:
        score += 0.5
    
    final_score = max(0, min(10, int(score)))
    
    if final_score >= 7:
        return ('High', final_score)
    elif final_score <= 3:
        return ('Low', final_score)
    else:
        return ('Medium', final_score)


def derive_cc_relevance_score(row: pd.Series, derived: Dict) -> Tuple[str, int]:
    """
    Derive overall credit card product relevance score (0-10).
    
    Combines multiple factors for Credigo.club specific targeting.
    
    Returns: (category, score 0-10)
    """
    score = 0
    
    # Urban/Metro boost (credit card adoption is urban-centric)
    urban_rural = derived.get('urban_rural', 'Rural')
    urban_score = derived.get('urban_score', 1)
    score += urban_score * 0.2  # Max 2 points
    
    # Digital literacy boost
    digital_score = derived.get('digital_literacy_score', 3)
    score += digital_score * 0.2  # Max 2 points
    
    # Aspirational intensity boost
    aspiration_score = derived.get('aspirational_score', 3)
    score += aspiration_score * 0.15  # Max 1.5 points
    
    # Age factor (young professionals = prime CC audience)
    gen_bucket = derived.get('generation_bucket', 'Gen X')
    if gen_bucket in ['Young Millennial', 'Core Millennial']:
        score += 2
    elif gen_bucket == 'Gen Z':
        score += 1.5
    elif gen_bucket == 'Gen X':
        score += 0.5
    
    # Low status quo = more open to new products
    status_quo_score = derived.get('status_quo_score', 5)
    score += (10 - status_quo_score) * 0.1  # Max 1 point
    
    # Low debt aversion helps
    debt_score = derived.get('debt_aversion_score', 5)
    score += (10 - debt_score) * 0.1  # Max 1 point
    
    # English proficiency (product is in English)
    english_score = derived.get('english_score', 0)
    score += english_score * 0.1  # Max 1 point
    
    final_score = max(0, min(10, int(score)))
    
    if final_score >= 7:
        return ('High', final_score)
    elif final_score >= 4:
        return ('Medium', final_score)
    else:
        return ('Low', final_score)


# ============================================================================
# MAIN DERIVATION PIPELINE
# ============================================================================

def derive_all_features(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Main entry point: Derive all simulation features for the dataset.
    
    Takes raw persona DataFrame and adds derived feature columns with 0-10 scores.
    
    Args:
        df: DataFrame with raw persona data (28 columns)
        verbose: Print progress information
    
    Returns:
        DataFrame with additional derived feature columns
    """
    if verbose:
        print("🔧 Deriving simulation features...")
        print(f"   Processing {len(df):,} personas")
    
    # Create copy to avoid modifying original
    result_df = df.copy()
    
    # Derive each feature
    derived_data = []
    
    for idx, row in df.iterrows():
        derived = {}
        
        # Geographic features
        urban_cat, urban_score = derive_urban_rural(row)
        derived['urban_rural'] = urban_cat
        derived['urban_score'] = urban_score
        derived['regional_cluster'] = derive_regional_cluster(row)
        
        # Language features
        derived['primary_language'] = derive_primary_language(row)
        english_cat, english_score = derive_english_proficiency(row)
        derived['english_proficiency'] = english_cat
        derived['english_score'] = english_score
        
        # Psychographic features (all 0-10 scales)
        asp_cat, asp_score = derive_aspirational_intensity(row)
        derived['aspirational_intensity'] = asp_cat
        derived['aspirational_score'] = asp_score
        
        dig_cat, dig_score = derive_digital_literacy(row)
        derived['digital_literacy'] = dig_cat
        derived['digital_literacy_score'] = dig_score
        
        trust_cat, trust_score = derive_trust_risk_orientation(row)
        derived['trust_orientation'] = trust_cat
        derived['trust_score'] = trust_score
        
        sq_cat, sq_score = derive_status_quo_sufficiency(row)
        derived['status_quo_sufficiency'] = sq_cat
        derived['status_quo_score'] = sq_score
        
        open_cat, open_score = derive_openness_hobby_breadth(row)
        derived['openness_hobby_breadth'] = open_cat
        derived['openness_score'] = open_score
        
        debt_cat, debt_score = derive_debt_aversion(row)
        derived['debt_aversion'] = debt_cat
        derived['debt_aversion_score'] = debt_score
        
        privacy_cat, privacy_score = derive_privacy_sensitivity(row)
        derived['privacy_sensitivity'] = privacy_cat
        derived['privacy_score'] = privacy_score
        
        # Generation bucket
        gen_bucket, gen_code = derive_generation_bucket(row)
        derived['generation_bucket'] = gen_bucket
        derived['generation_code'] = gen_code
        
        # Credit card relevance (composite)
        cc_cat, cc_score = derive_cc_relevance_score(row, derived)
        derived['cc_relevance'] = cc_cat
        derived['cc_relevance_score'] = cc_score
        
        derived_data.append(derived)
        
        if verbose and (idx + 1) % 200 == 0:
            print(f"   Processed {idx + 1:,}/{len(df):,} personas")
    
    # Convert to DataFrame and join
    derived_df = pd.DataFrame(derived_data)
    result_df = pd.concat([result_df.reset_index(drop=True), derived_df], axis=1)
    
    if verbose:
        print(f"✅ Derived {len(derived_df.columns)} new features (with 0-10 scores)")
        print(f"   Total columns: {len(result_df.columns)}")
        
        # Quick distribution summary
        print("\n📊 Derived Feature Distributions:")
        print(f"   Urban/Rural: {dict(result_df['urban_rural'].value_counts())}")
        print(f"   Generation: {dict(result_df['generation_bucket'].value_counts())}")
        print(f"   Digital Literacy: {dict(result_df['digital_literacy'].value_counts())}")
        print(f"   Aspirational: {dict(result_df['aspirational_intensity'].value_counts())}")
        print(f"   CC Relevance: {dict(result_df['cc_relevance'].value_counts())}")
        
        # Score distributions
        print(f"\n   Score Means (0-10 scale):")
        score_cols = ['digital_literacy_score', 'aspirational_score', 'trust_score', 
                      'status_quo_score', 'debt_aversion_score', 'cc_relevance_score']
        for col in score_cols:
            if col in result_df.columns:
                print(f"     {col}: {result_df[col].mean():.1f}")
    
    return result_df


def get_derived_feature_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate summary statistics for derived features.
    """
    derived_cols = [
        'urban_rural', 'regional_cluster', 'english_proficiency',
        'aspirational_intensity', 'digital_literacy', 'trust_orientation',
        'status_quo_sufficiency', 'openness_hobby_breadth', 'debt_aversion',
        'privacy_sensitivity', 'generation_bucket', 'cc_relevance'
    ]
    
    summary_data = []
    for col in derived_cols:
        if col in df.columns:
            value_counts = df[col].value_counts()
            summary_data.append({
                "Feature": col,
                "Values": ", ".join([f"{k}: {v}" for k, v in value_counts.head(5).items()]),
                "Unique": df[col].nunique()
            })
    
    return pd.DataFrame(summary_data)


# ============================================================================
# MAIN EXECUTION (for standalone testing)
# ============================================================================

if __name__ == "__main__":
    """
    Test feature derivation when run directly.
    """
    print("\n🧪 Running derive_features.py test...\n")
    
    try:
        # Import load_dataset
        from load_dataset import load_and_sample
        
        # Load a small sample for testing
        sample_df, metadata = load_and_sample(n=100, seed=42, verbose=True)
        
        print("\n" + "=" * 60)
        print("Testing Feature Derivation (Enhanced 0-10 Scales)")
        print("=" * 60)
        
        # Derive features
        enriched_df = derive_all_features(sample_df, verbose=True)
        
        print("\n📋 Sample Enriched Persona:")
        print("-" * 60)
        sample = enriched_df.iloc[0]
        show_cols = [
            'age', 'sex', 'state', 'occupation',
            'urban_rural', 'urban_score', 'regional_cluster', 'generation_bucket',
            'digital_literacy', 'digital_literacy_score',
            'aspirational_intensity', 'aspirational_score',
            'trust_orientation', 'trust_score',
            'debt_aversion', 'debt_aversion_score',
            'cc_relevance', 'cc_relevance_score'
        ]
        for col in show_cols:
            if col in sample.index:
                print(f"  {col}: {sample[col]}")
        
        print("\n✅ Test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
