import streamlit as st
import asyncio
import aiohttp
import os
from dotenv import load_dotenv
import re
import json

# Load environment variables from the .env file
load_dotenv()

# Get the API key from environment variables
api_key = os.getenv("OPENWEBUI_API_KEY")
API_URL = "http://localhost:3000/api/chat/completions"

class GoogleAdsPolicyChecker:
    def __init__(self):
        self.prohibited_keywords = {
            "counterfeit_goods": [
                "fake", "replica", "knockoff", "imitation", "copy", "counterfeit", 
                "lookalike", "clone", "reproduction", "duplicate"
            ],
            "dangerous_products": [
                "weapons", "weapon", "drugs", "explosives", "tobacco", "firearms", "gun", 
                "toxic chemicals", "steroids", "ammunition", "controlled substance"
            ],
            "adult_content": [
                "nudity", "sexually suggestive", "explicit", "nude", "sex", "adult content",
                "adult services", "escort", "dating services", "mature content"
            ],
            "prohibited_practices": [
                "phishing", "malware", "hacking", "spyware", "keyloggers", 
                "unapproved pharmaceuticals", "ddos attack", "hack", "crack", 
                "pirate", "illegal download", "unauthorized access"
            ],
            "restricted_content": [
                "alcohol", "gambling", "adult", "political", "financial services",
                "prescription", "pharmacy", "medicine", "supplements"
            ],
            "personal_attributes": [
                "race", "ethnicity", "religion", "age", "sexual orientation", 
                "gender identity", "disability", "income level", "financial status"
            ],
            "misinformation": [
                "false", "fake news", "misleading", "gossip", "conspiracy",
                "unverified", "unproven", "disputed", "propaganda"
            ],
            "profanity": [
                "curse", "swear", "expletive","taboo", "obscenity", "cuss", 
                "vulgarism", "epithet", "profane", "offensive language"
            ],
            "sensitive_content": [
                "dark comedy", "dark humor","Clear Skin", "black comedy", "black humor",
                "taboo", "controversial","Acne Treatment","Gentle Solution for Acne", "offensive", "sensitive topics",
                "sensitive subjects","Brighter Complexion", "disturbing", "twisted humor", "morbid",
                "inappropriate", "politically incorrect","Effective Skincare", "shock value",
                "edgy humor", "crude humor","Achieve Confidence ", "insensitive", "triggering",
                "uncomfortable topics","Radiant Skin","Innovative Cream", "controversial subjects",
                "sensitive issues", "moral issues","Consistent Use Benefits", "ethical issues",
                "social commentary", "cultural sensitivity", "racial topics",
                "religious topics", "political satire", "dark subjects",
                "mature themes", "adult themes", "sensitive material",
                "controversial content", "provocative content",
                "sensitive matters", "delicate subjects", "contentious topics",
                "offensive material", "questionable content"
            ],
            "financial_services": [
                "high-interest payday loans", "cryptocurrency investment", "crypto investment",
                "no credit check financing", "guaranteed cash advance", 
                "instant loan approval", "high APR personal loans",
                "invest", "investment", "investing", "investor",
                "stock trading", "forex trading", "day trading",
                "cryptocurrency", "crypto", "bitcoin", "ethereum",
                "binary options", "CFDs", "futures trading","finpath",
                "guaranteed returns", "guaranteed profit", "guaranteed investment",
                "risk-free investment", "quick profits", "fast returns",
                "double your money", "triple your investment",
                "trade signals", "trading bot", "automated trading",
                "margin trading", "leveraged trading", "forex signals",
                "get rich quick", "become wealthy", "financial freedom",
                "passive income", "earn from home", "make money online",
                "investment advice", "financial advisor", "wealth management",
                "portfolio management", "asset management", "fund management",
                "banking", "loans", "credit", "mortgage", "refinance",
                "debt consolidation", "debt relief", "credit repair"
            ],
            "gambling_and_games": [
                "unlicensed gambling", "online betting", "casino", "betting",
                "gambling", "lottery", "poker", "slots", "sports betting",
                "wagering", "bookmaker", "bookie", "odds", "jackpot",
                "roulette", "blackjack", "bingo", "raffle", "sweepstakes"
            ]
        }
        
        self.misrepresentation_replacements = {
            "Absolute Claims": {
                "Guaranteed results": "Potential benefits",
                "100% success rate": "Proven effectiveness",
                "Always effective": "Helpful solution",
                "Instant cure": "Supportive treatment",
                "No risk involved": "Carefully designed",
                "Perfect solution": "Effective solution",
                "Never fails": "Reliable performance",
                "Zero problems": "Minimized issues",
                "Ultimate answer": "Practical solution"
            },
            "Exaggerated Superlatives": {
                "Best in the world": "Reliable choice",
                "Number 1": "Trusted option",
                "Top-rated": "Well-regarded",
                "Most effective": "Proven performer",
                "Highest quality": "Premium quality",
                "Unbeatable": "Competitive",
                "Superior to all": "High-quality",
                "World-class": "Professional",
                "Revolutionary": "Innovative"
                
                
            },
            "False Authority": {
                "FDA approved": "Quality tested",
                "Doctor recommended": "Professional insight",
                "Official partner": "Collaborative solution",
                "Government endorsed": "Industry standard",
                "Scientifically proven": "Research-based",
                "Expert guaranteed": "Professional grade",
                "Officially certified": "Thoroughly tested"
            },
            "False Pricing": {
                "Lowest price guaranteed": "Competitive pricing",
                "50% off today only": "Special offer available",
                "No hidden fees": "Transparent pricing",
                "Limited-time offer": "Current promotion",
                "Biggest discount ever": "Special savings",
                "Exclusive deal": "Featured offer",
                "One-time price": "Special rate"
            },
            "Unsupported Claims": {
                "Lose 10 pounds in a week": "Support healthy lifestyle",
                "Cures all diseases": "Supports wellness",
                "Clinically proven": "Research-backed",
                "Miracle solution": "Innovative approach",
                "Magical results": "Positive outcomes",
                "Life-changing effects": "Beneficial results",
                "Instant transformation": "Gradual improvement"
            }
        }
        
        self.cleanup_patterns = {
            "symbols": (r'[!?₹@#$%^&*()_+<>{}[\]|~`=]', ""),
            "repeated_periods": (r'\.{2,}', "."),
            "oxford_comma": (r',\s*(and|or)\s', " and "),
            
            "generic_phrases": {
                r'\bBuy products here\b': "Explore our selection",
                r'\bClick to learn more\b': "Discover details",
                r'\bShop now\b': "Browse selection",
                r'\bLimited time only\b': "While available",
                r'\bAct fast\b': "Consider today",
                r'\bDon\'t wait\b': "Start today",
                r'\bClick here\b': "Learn more",
                r'\bBuy now\b': "Shop today",
                r'\bOrder now\b': "Start order",
                r'\bDon\'t miss out\b': "Available now",
                r'\bExclusive offer\b': "Featured item",
                r'\bSpecial promotion\b': "Current offer"
            },
            
            "gimmicky": {
                r'\bFREE\b': "included",
                r'\bf-r-e-e\b': "included",
                r'\bF₹€€\b': "included",
                r'\bB-U-Y\b': "shop",
                r'\bSALE!!!\b': "reduced price",
                r'\b100% OFF\b': "special price",
                r'\bHUGE SAVINGS\b': "great value",
                r'\bINCREDIBLE DEAL\b': "featured price",
                r'\bAMAZING OFFER\b': "special value",
                r'\bUNBELIEVABLE PRICE\b': "competitive price",
                r'\bFANTASTIC DEAL\b': "current offer"
            }
        }

    async def initial_policy_check(self, session: aiohttp.ClientSession, text: str) -> dict:
        """
        Modified first-line validation to distinguish between prohibited and misrepresentation content
        """
        prompt = f"""
        You are a strict Google Ads policy enforcer. Analyze this text and categorize any issues found:

        Text: {text}

        Strictly Prohibited content (must block ad):
        - Weapons, ammunition, explosives
        - Drugs, pharmaceuticals, controlled substances
        - Gambling, betting, casino content
        - Adult content, dating services
        - Counterfeit goods
        - Hacking, cracking tools
        - Dangerous products or services
        - Financial services (cryptocurrency, trading, investments)

        Misrepresentation content (can be fixed):
        - Superlative claims (best, perfect, ultimate)
        - Unrealistic guarantees
        - Unverifiable claims
        - Exaggerated promises
        - False urgency or scarcity claims

        Return JSON with these exact keys:
        - has_prohibited: boolean (true if ANY strictly prohibited content is found)
        - has_misrepresentation: boolean (true if ANY misrepresentation content is found)
        - prohibited_violations: list of {{"category": string, "found_term": string, "explanation": string}}
        - misrepresentation_items: list of {{"type": string, "found_term": string, "suggested_replacement": string}}
        - confidence_score: number between 0 and 1

        Be extremely strict with prohibited content, but flag misrepresentation separately.
        """

        try:
            async with session.post(
                API_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4o-mini-2024-07-18",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a policy enforcement AI that distinguishes between prohibited content and fixable issues."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                    "max_tokens": 500,
                },
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    policy_check = json.loads(result['choices'][0]['message']['content'])
                    return policy_check
                else:
                    error_content = await response.text()
                    return {
                        "has_prohibited": True,
                        "has_misrepresentation": False,
                        "prohibited_violations": [{
                            "category": "API Error",
                            "found_term": "Error checking policy",
                            "explanation": f"Failed to verify policy compliance: {error_content}"
                        }],
                        "misrepresentation_items": [],
                        "confidence_score": 1.0
                    }
        except Exception as e:
            return {
                "has_prohibited": True,
                "has_misrepresentation": False,
                "prohibited_violations": [{
                    "category": "System Error",
                    "found_term": "Error checking policy",
                    "explanation": f"System error during policy check: {str(e)}"
                }],
                "misrepresentation_items": [],
                "confidence_score": 1.0
            }

    async def clean_and_generate_ad(self, session: aiohttp.ClientSession, product_name: str, product_description: str, misrepresentation_items: list) -> tuple[dict, list]:
        """
        Clean text and generate ad based on policy check results
        """
        # First apply the misrepresentation replacements from OpenAI's suggestions
        cleaned_name = product_name
        cleaned_description = product_description
        all_replacements = []

        # Apply OpenAI's suggested replacements first
        for item in misrepresentation_items:
            found_term = item['found_term']
            replacement = item['suggested_replacement']
            
            # Clean product name
            if found_term.lower() in cleaned_name.lower():
                cleaned_name = re.sub(
                    re.escape(found_term),
                    replacement,
                    cleaned_name,
                    flags=re.IGNORECASE
                )
                all_replacements.append({
                    "type": "Misrepresentation",
                    "category": item['type'],
                    "original": found_term,
                    "replacement": replacement
                })
            
            # Clean product description
            if found_term.lower() in cleaned_description.lower():
                cleaned_description = re.sub(
                    re.escape(found_term),
                    replacement,
                    cleaned_description,
                    flags=re.IGNORECASE
                )
                if {"type": "Misrepresentation", "category": item['type'], "original": found_term, "replacement": replacement} not in all_replacements:
                    all_replacements.append({
                        "type": "Misrepresentation",
                        "category": item['type'],
                        "original": found_term,
                        "replacement": replacement
                    })

        # Then apply standard cleaning
        cleaned_name, name_replacements = self.clean_text(cleaned_name)
        cleaned_description, desc_replacements = self.clean_text(cleaned_description)
        
        all_replacements.extend(name_replacements)
        all_replacements.extend(desc_replacements)

        # Generate ad with cleaned text
        ad_result = await self.generate_compliant_ad(session, cleaned_name, cleaned_description)
        
        return ad_result, all_replacements

    def clean_text(self, text: str) -> tuple[str, list]:
        """
        Clean text and track all replacements made
        """
        cleaned_text = text
        replacements_made = []

        # Replace misrepresentation keywords
        for category, replacements in self.misrepresentation_replacements.items():
            for keyword, replacement in replacements.items():
                if re.search(re.escape(keyword), cleaned_text, re.IGNORECASE):
                    cleaned_text = re.sub(
                        re.escape(keyword),
                        replacement,
                        cleaned_text,
                        flags=re.IGNORECASE
                    )
                    replacements_made.append({
                        "type": "Misrepresentation",
                        "category": category,
                        "original": keyword,
                        "replacement": replacement
                    })

        # Replace generic phrases and gimmicky terms
        for pattern_type in ["generic_phrases", "gimmicky"]:
            for pattern, replacement in self.cleanup_patterns[pattern_type].items():
                if re.search(pattern, cleaned_text, re.IGNORECASE):
                    matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
                    cleaned_text = re.sub(pattern, replacement, cleaned_text, flags=re.IGNORECASE)
                    for match in matches:
                        replacements_made.append({
                            "type": pattern_type.replace("_", " ").title(),
                            "original": match,
                            "replacement": replacement
                        })

        # Clean up basic patterns
        cleaned_text = re.sub(self.cleanup_patterns["symbols"][0], 
                            self.cleanup_patterns["symbols"][1], 
                            cleaned_text)
        cleaned_text = re.sub(self.cleanup_patterns["repeated_periods"][0], 
                            self.cleanup_patterns["repeated_periods"][1], 
                            cleaned_text)
        cleaned_text = re.sub(self.cleanup_patterns["oxford_comma"][0], 
                            self.cleanup_patterns["oxford_comma"][1], 
                            cleaned_text)

        # Remove extra spaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        return cleaned_text.strip(), replacements_made

    async def generate_compliant_ad(self, session: aiohttp.ClientSession, product_name: str, product_description: str) -> dict:
        """Generate ad using OpenAI with strict content guidelines and proper formatting"""
        
        prompt = f"""
        Create a Google Ads compliant advertisement that strictly avoids ANY sensitive or controversial topics. 
        
        STRICT REQUIREMENTS:
        1. Use only periods (.) for punctuation
        2. Do not use any exclamation marks, question marks, or special characters
        3. Write in a professional, neutral tone
        4. Focus only on positive, non-controversial aspects
        5. Each line must end with a period if it's a complete sentence
        6. Use only lowercase letters - no capitalization anywhere
        7. IMPORTANT: DO NOT mention or reference:
        - Dark humor or dark comedy
        - Taboo or controversial subjects
        - Sensitive topics or themes
        - Serious or challenging topics
        - Anything potentially offensive
        8. Keep content light, positive, and universally acceptable
        
        Product Name: {product_name}
        Product Description: {product_description}  
        
        Format EXACTLY like this with line breaks:
        headline 1: [Light, positive statement without special punctuation]
        
        headline 2: [Engaging, non-controversial statement without special punctuation]
        
        headline 3: [Creative, appropriate statement without special punctuation]
        
        description 1: [Professional statement ending with a period]
        
        description 2: [Engaging statement ending with a period]
        
         
        """

        try:
            async with session.post(
                API_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4o-mini-2024-07-18",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an AI that creates strictly compliant Google Ads. Never mention sensitive, controversial, or potentially offensive topics. Keep content universally acceptable and positive."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 350,
                },
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    generated_ad = result['choices'][0]['message']['content'].strip()
                    
                    # Check for prohibited keywords
                    for category, keywords in self.prohibited_keywords.items():
                        for keyword in keywords:
                            if keyword.lower() in generated_ad.lower():
                                return {
                                    "success": False, 
                                    "error": f"Generated ad contains prohibited term: {keyword}"
                                }
                    
                    # Clean the generated ad
                    cleaned_text, _ = self.clean_text(generated_ad)
                    cleaned_text = cleaned_text.lower()
                    
                    # Format each line properly with line breaks
                    final_lines = []
                    for line in cleaned_text.split('\n'):
                        line = line.strip()
                        if line:
                            if ':' in line:
                                prefix, content = line.split(':', 1)
                                content = content.strip()
                                if content and not content.endswith('.') and len(content.split()) > 2:
                                    content += '.'
                                line = f"{prefix}: {content}"
                                final_lines.append(line)
                                final_lines.append("")  # Add empty line after each component
                    
                    final_ad = '\n'.join(final_lines).strip()
                    
                    # Final verification
                    for category, keywords in self.prohibited_keywords.items():
                        for keyword in keywords:
                            if keyword.lower() in final_ad.lower():
                                return {
                                    "success": False, 
                                    "error": f"Final ad still contains prohibited term: {keyword}"
                                }
                    
                    return {"success": True, "ad": final_ad}
                else:
                    error_content = await response.text()
                    return {"success": False, "error": f"API Error: {response.status} - {error_content}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

async def main():
    st.title("Google Ads Generator with Advanced Policy Compliance")
    
    checker = GoogleAdsPolicyChecker()
    
    if 'result' not in st.session_state:
        st.session_state.result = None
    
    def clear_results():
        st.session_state.result = None
    
    product_name = st.text_input("Enter the product name:")
    product_description = st.text_area("Enter the product description:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Generate Compliant Ad"):
            if not product_name or not product_description:
                st.warning("Please enter both product name and description.")
            else:
                with st.spinner("Checking policy compliance..."):
                    async with aiohttp.ClientSession() as session:
                        initial_check = await checker.initial_policy_check(
                            session,
                            product_name + " " + product_description
                        )
                        
                        if initial_check.get('has_prohibited', False):
                            # Show prohibited content violations and stop
                            st.error("🚫 Content Prohibited - Cannot Generate Ad")
                            st.write("The following violations were detected:")
                            for violation in initial_check.get('prohibited_violations', []):
                                with st.expander(f"Violation: {violation['category']}"):
                                    st.write(f"Found: {violation['found_term']}")
                                    st.write(f"Explanation: {violation['explanation']}")
                            if initial_check.get('confidence_score'):
                                st.write(f"Confidence Score: {initial_check['confidence_score']:.2f}")
                        else:
                            # Process the ad with any necessary misrepresentation fixes
                            misrepresentation_items = initial_check.get('misrepresentation_items', [])
                            result, replacements = await checker.clean_and_generate_ad(
                                session,
                                product_name,
                                product_description,
                                misrepresentation_items
                            )
                            
                            # Show replacements if any were made
                            if replacements:
                                st.info("The following adjustments were made to comply with Google Ads policies:")
                                for replacement in replacements:
                                    if "category" in replacement:
                                        st.write(f"• {replacement['type']} ({replacement['category']}): "
                                               f"'{replacement['original']}' → '{replacement['replacement']}'")
                                    else:
                                        st.write(f"• {replacement['type']}: "
                                               f"'{replacement['original']}' → '{replacement['replacement']}'")
                            
                            st.session_state.result = result
    
    with col2:
        if st.button("Clear Results"):
            clear_results()
    
    if st.session_state.result:
        result = st.session_state.result
        if result["success"]:
            st.success("Ad Generated Successfully!")
            # Display each line of the ad with proper formatting
            ad_lines = result["ad"].split('\n')
            for line in ad_lines:
                st.write(line)
        else:
            st.error("Failed to generate ad.")
            st.write(result["error"])

if __name__ == "__main__":
    asyncio.run(main())