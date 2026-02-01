"""
credigo_personas.py - Optimized Personas for Credigo.club

Personas specifically designed for credit card recommendation product.
Each persona represents a distinct user archetype likely to use Credigo.
"""

from typing import Dict, List, Optional

CREDIGO_PERSONAS = [
    {
        "name": "Young Professional Credit Seeker",
        "description": "Young professional (25-30) in metro, first-time credit card seeker, high aspiration",
        "raw_fields": {
            "SEC": 0.7,  # Upper-middle class
            "UrbanRuralTier": 1.0,  # Metro
            "DigitalLiteracy": 0.85,  # High - comfortable with apps
            "FamilyInfluence": 0.4,  # Moderate - independent decision maker
            "AspirationalLevel": 0.9,  # Very high - wants premium lifestyle
            "PriceSensitivity": 0.4,  # Moderate - values quality over price
            "RegionalCulture": 0.3,  # Low collectivism (metro, individualistic)
            "InfluencerTrust": 0.7,  # Trusts recommendations and reviews
            "ProfessionalSector": 0.9,  # Tech/formal sector
            "EnglishProficiency": 0.95,  # Fluent English
            "HobbyDiversity": 0.8,  # Broad interests (travel, dining, shopping)
            "CareerAmbition": 0.9,  # High career ambition
            "AgeBucket": 0.9,  # Young (25-30)
            "GenderMarital": 0.6  # Single/independent
        },
        "intent_profile": {
            "compare_options": 0.35,  # Wants to compare cards
            "learn_basics": 0.25,  # Learning about credit cards
            "quick_decision": 0.20,  # Wants to decide quickly
            "validate_choice": 0.15,  # Validating their choice
            "price_check": 0.05
        }
    },
    {
        "name": "Salaried Individual with Spending Goals",
        "description": "Mid-career salaried professional (30-40), tier-2 city, family-oriented, price-conscious",
        "raw_fields": {
            "SEC": 0.6,  # Middle class
            "UrbanRuralTier": 0.5,  # Tier-2 city
            "DigitalLiteracy": 0.6,  # Moderate - uses apps but not power user
            "FamilyInfluence": 0.7,  # High - family considerations important
            "AspirationalLevel": 0.5,  # Moderate - stable growth
            "PriceSensitivity": 0.8,  # High - very price conscious
            "RegionalCulture": 0.6,  # Moderate collectivism
            "InfluencerTrust": 0.4,  # Moderate trust
            "ProfessionalSector": 0.6,  # Mixed formal sector
            "EnglishProficiency": 0.7,  # Good English
            "HobbyDiversity": 0.5,  # Moderate interests
            "CareerAmbition": 0.5,  # Moderate ambition
            "AgeBucket": 0.6,  # Middle-aged (30-40)
            "GenderMarital": 0.3  # Married, family-oriented
        },
        "intent_profile": {
            "price_check": 0.40,  # Very focused on pricing
            "compare_options": 0.30,  # Wants to compare
            "validate_choice": 0.20,  # Validating best deal
            "learn_basics": 0.10
        }
    },
    {
        "name": "Tech-Savvy Millennial Explorer",
        "description": "Tech-savvy millennial (28-35), metro, high digital literacy, explores options thoroughly",
        "raw_fields": {
            "SEC": 0.75,  # Upper-middle to upper class
            "UrbanRuralTier": 1.0,  # Metro
            "DigitalLiteracy": 0.95,  # Very high - power user
            "FamilyInfluence": 0.3,  # Low - individualistic
            "AspirationalLevel": 0.85,  # High aspiration
            "PriceSensitivity": 0.3,  # Low - values features over price
            "RegionalCulture": 0.3,  # Low collectivism
            "InfluencerTrust": 0.6,  # Moderate - does own research
            "ProfessionalSector": 0.95,  # Tech sector
            "EnglishProficiency": 0.95,  # Fluent
            "HobbyDiversity": 0.9,  # Very broad interests
            "CareerAmbition": 0.9,  # High ambition
            "AgeBucket": 0.75,  # Millennial (28-35)
            "GenderMarital": 0.7  # Single/independent
        },
        "intent_profile": {
            "compare_options": 0.45,  # Strong comparison intent
            "learn_basics": 0.30,  # Wants to understand deeply
            "validate_choice": 0.20,  # Validating through research
            "quick_decision": 0.05
        }
    },
    {
        "name": "First-Time Card Seeker - Cautious",
        "description": "First-time credit card seeker (22-28), moderate income, cautious about credit, needs education",
        "raw_fields": {
            "SEC": 0.5,  # Middle class
            "UrbanRuralTier": 0.7,  # Tier-1 or large tier-2
            "DigitalLiteracy": 0.65,  # Moderate - comfortable but not expert
            "FamilyInfluence": 0.6,  # Moderate-high - seeks family advice
            "AspirationalLevel": 0.6,  # Moderate - wants to build credit
            "PriceSensitivity": 0.6,  # Moderate-high - budget conscious
            "RegionalCulture": 0.5,  # Moderate collectivism
            "InfluencerTrust": 0.5,  # Moderate - trusts authority
            "ProfessionalSector": 0.6,  # Mixed sectors
            "EnglishProficiency": 0.75,  # Good English
            "HobbyDiversity": 0.6,  # Moderate interests
            "CareerAmbition": 0.7,  # Moderate-high ambition
            "AgeBucket": 0.85,  # Young (22-28)
            "GenderMarital": 0.5  # Mixed
        },
        "intent_profile": {
            "learn_basics": 0.40,  # Strong learning intent
            "eligibility_check": 0.30,  # Wants to check eligibility
            "compare_options": 0.20,  # Wants to compare
            "validate_choice": 0.10
        }
    },
    {
        "name": "Travel Enthusiast - Rewards Seeker",
        "description": "Travel-focused user (30-40), high income, seeks travel rewards and lounge access",
        "raw_fields": {
            "SEC": 0.8,  # Upper class
            "UrbanRuralTier": 1.0,  # Metro
            "DigitalLiteracy": 0.9,  # High
            "FamilyInfluence": 0.4,  # Moderate - independent
            "AspirationalLevel": 0.9,  # Very high - lifestyle focused
            "PriceSensitivity": 0.2,  # Low - values rewards over fees
            "RegionalCulture": 0.3,  # Low collectivism
            "InfluencerTrust": 0.7,  # High - trusts travel influencers
            "ProfessionalSector": 0.85,  # Professional/executive
            "EnglishProficiency": 0.95,  # Fluent
            "HobbyDiversity": 0.9,  # Very broad (travel, dining, experiences)
            "CareerAmbition": 0.85,  # High ambition
            "AgeBucket": 0.65,  # 30-40
            "GenderMarital": 0.6  # Independent
        },
        "intent_profile": {
            "compare_options": 0.50,  # Strong comparison for best rewards
            "validate_choice": 0.30,  # Validating best travel card
            "quick_decision": 0.15,  # Wants to decide and start earning
            "price_check": 0.05
        }
    },
    {
        "name": "Price-Conscious Budget Optimizer",
        "description": "Budget-focused user (25-35), moderate income, maximizes value, minimizes fees",
        "raw_fields": {
            "SEC": 0.55,  # Middle class
            "UrbanRuralTier": 0.6,  # Tier-2 or smaller metro
            "DigitalLiteracy": 0.7,  # Good - uses apps for deals
            "FamilyInfluence": 0.6,  # Moderate-high - family budget considerations
            "AspirationalLevel": 0.5,  # Moderate
            "PriceSensitivity": 0.9,  # Very high - deal seeker
            "RegionalCulture": 0.6,  # Moderate collectivism
            "InfluencerTrust": 0.5,  # Moderate
            "ProfessionalSector": 0.55,  # Mixed
            "EnglishProficiency": 0.7,  # Good
            "HobbyDiversity": 0.5,  # Moderate
            "CareerAmbition": 0.5,  # Moderate
            "AgeBucket": 0.7,  # 25-35
            "GenderMarital": 0.4  # Family-oriented
        },
        "intent_profile": {
            "price_check": 0.50,  # Very focused on pricing
            "compare_options": 0.30,  # Comparing for best deal
            "validate_choice": 0.15,  # Validating best value
            "quick_decision": 0.05
        }
    },
    {
        "name": "Existing Cardholder - Upgrade Seeker",
        "description": "Existing credit card user (30-45), wants to upgrade or get better card, experienced",
        "raw_fields": {
            "SEC": 0.7,  # Upper-middle class
            "UrbanRuralTier": 0.8,  # Metro or large tier-2
            "DigitalLiteracy": 0.8,  # High - experienced with fintech
            "FamilyInfluence": 0.5,  # Moderate
            "AspirationalLevel": 0.7,  # High - wants better lifestyle
            "PriceSensitivity": 0.4,  # Moderate - values benefits
            "RegionalCulture": 0.4,  # Low-moderate
            "InfluencerTrust": 0.6,  # Moderate - does research
            "ProfessionalSector": 0.75,  # Professional
            "EnglishProficiency": 0.9,  # Fluent
            "HobbyDiversity": 0.7,  # Broad
            "CareerAmbition": 0.7,  # High ambition
            "AgeBucket": 0.55,  # 30-45
            "GenderMarital": 0.5  # Mixed
        },
        "intent_profile": {
            "compare_options": 0.40,  # Comparing to current card
            "validate_choice": 0.35,  # Validating upgrade is worth it
            "quick_decision": 0.20,  # Wants to decide quickly
            "price_check": 0.05
        }
    },
    {
        "name": "High Earner - Premium Card Seeker",
        "description": "High-income professional (35-45), seeks premium cards with exclusive benefits",
        "raw_fields": {
            "SEC": 0.9,  # Upper class
            "UrbanRuralTier": 1.0,  # Metro
            "DigitalLiteracy": 0.95,  # Very high
            "FamilyInfluence": 0.3,  # Low - independent
            "AspirationalLevel": 0.95,  # Very high
            "PriceSensitivity": 0.1,  # Very low - values exclusivity
            "RegionalCulture": 0.2,  # Low collectivism
            "InfluencerTrust": 0.7,  # High - trusts premium brands
            "ProfessionalSector": 0.95,  # Executive/professional
            "EnglishProficiency": 0.98,  # Fluent
            "HobbyDiversity": 0.9,  # Very broad (luxury, travel, dining)
            "CareerAmbition": 0.95,  # Very high
            "AgeBucket": 0.5,  # 35-45
            "GenderMarital": 0.7  # Independent
        },
        "intent_profile": {
            "compare_options": 0.45,  # Comparing premium options
            "validate_choice": 0.30,  # Validating best premium card
            "quick_decision": 0.20,  # Wants premium benefits quickly
            "price_check": 0.05
        }
    }
]


def get_credigo_persona_by_name(name: str) -> Optional[Dict]:
    """Get a specific persona by name."""
    for persona in CREDIGO_PERSONAS:
        if persona["name"] == name:
            return persona
    return None


def get_all_credigo_personas() -> List[Dict]:
    """Get all Credigo personas."""
    return CREDIGO_PERSONAS


def print_credigo_persona_summary():
    """Print a summary of all Credigo personas."""
    print("\n" + "=" * 80)
    print("CREDIGO PERSONAS")
    print("=" * 80)
    
    for i, persona in enumerate(CREDIGO_PERSONAS, 1):
        print(f"\n{i}. {persona['name']}")
        print(f"   {persona['description']}")
        print(f"   Key Traits:")
        print(f"     - SEC: {persona['raw_fields']['SEC']:.1f} (Socio-economic class)")
        print(f"     - Digital Literacy: {persona['raw_fields']['DigitalLiteracy']:.1f}")
        print(f"     - Aspiration: {persona['raw_fields']['AspirationalLevel']:.1f}")
        print(f"     - Price Sensitivity: {persona['raw_fields']['PriceSensitivity']:.1f}")
        print(f"   Primary Intent: {max(persona.get('intent_profile', {}).items(), key=lambda x: x[1])[0] if persona.get('intent_profile') else 'N/A'}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print_credigo_persona_summary()

