# OpenAI integration utilities for marketplace application
import json
import os
import re
import unicodedata
from datetime import datetime, date
from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL",
                              "gpt-4o-mini")  # Faster and cheaper than GPT-5
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def extract_search_intent(user_query):
    """
    STAGE 1: Extract structured search parameters and normalized tags from user query.

    Args:
        user_query: Raw user search query in Bosnian

    Returns:
        dict with intent, categories, budget, search_tags, exclude_tags, etc.
    """
    system_prompt = """You are a query parser for a Bosnian supermarket app with tag-based search.

Extract structured search parameters AND search tags from user queries.

RULES:
1. Extract intent type, meal type, budget, categories
2. **CRITICAL**: Extract and normalize search tags - keywords describing what user wants
3. Correct common typos: "coKlada"→"čokolada", "riza"→"riža", "pile"→"piletina"
4. For meal queries, expand to relevant tags: "ručak"→["ručak","meso","protein","glavno jelo"]
5. For dietary signals, add appropriate tags: "zdravo"→["zdravo","protein","povrće"] + exclude ["čokolada","slatko"]
6. **SHOPPING LISTS**: When user lists specific items, set categories=[] (empty) to search all categories

TAG NORMALIZATION:
- "cokolada", "coKlada", "choco" → "čokolada"
- "pile", "chicken" → "piletina"
- "riza", "rice" → "riža"
- "hleb", "kruh" → "hljeb"
- "paradajz", "rajčica" → "paradajz"
- "grickalice", "grickalica" → "čokolada", "slatkiš", "slatko", "desert"

DIETARY/MEAL TAG EXPANSION:
- "zdravo jesti" → search_tags: ["zdravo","protein","povrće","voće"], exclude_tags: ["čokolada","slatko","slatkiš"]
- "ručak" → search_tags: ["ručak","glavno jelo","obrok","meso","protein"]
- "brzo" → search_tags: ["brzo","instant","gotovo jelo"]
- "doručak" → search_tags: ["doručak","jogurt","žitarice","hljeb"]
- "vegetarijansko" → search_tags: ["povrće","vegetarian"], exclude_tags: ["meso","riba"]
- "grickalice" → search_tags: ["grickalice","čokolada","slatkiš","slatko","desert","užina"]

Return ONLY valid JSON (no markdown):
{
  "intent": "meal_prep" | "shopping_list" | "specific_product" | "category_browse",
  "meal_type": "doručak" | "ručak" | "večera" | "užina" | null,
  "categories": ["Meso", "Namirnice", "Voće/Povrće", "Pića", "Mliječni proizvodi", "Higijena", "Čišćenje", "Auto", "Bebe"],
  "budget_max": number | null,
  "budget_min": number | null,
  "dietary_preferences": [],
  "exclude_categories": [],
  "search_tags": ["tag1", "tag2"],
  "exclude_tags": ["tag3", "tag4"],
  "tag_match_type": "all" | "any"
}

EXAMPLES:

Query: "Zelim da napravim rucak ispod 20 KM"
{
  "intent": "meal_prep",
  "meal_type": "ručak",
  "categories": ["Meso", "Namirnice", "Voće/Povrće"],
  "budget_max": 20,
  "budget_min": null,
  "dietary_preferences": [],
  "exclude_categories": ["Higijena", "Čišćenje", "Auto", "Bebe"],
  "search_tags": ["ručak", "glavno jelo", "obrok", "meso", "protein"],
  "exclude_tags": ["desert", "slatko", "slatkiš"],
  "tag_match_type": "any"
}

Query: "piletina i coKlada ispod 15 KM"
{
  "intent": "shopping_list",
  "meal_type": null,
  "categories": [],
  "budget_max": 15,
  "budget_min": null,
  "dietary_preferences": [],
  "exclude_categories": [],
  "search_tags": ["piletina", "čokolada"],
  "exclude_tags": [],
  "tag_match_type": "any"
}

Query: "zdravo jesti ispod 25 KM"
{
  "intent": "meal_prep",
  "meal_type": null,
  "categories": ["Meso", "Namirnice", "Voće/Povrće", "Mliječni proizvodi"],
  "budget_max": 25,
  "budget_min": null,
  "dietary_preferences": ["zdravo"],
  "exclude_categories": ["Higijena", "Čišćenje", "Auto", "Bebe"],
  "search_tags": ["zdravo", "protein", "povrće", "voće", "piletina"],
  "exclude_tags": ["čokolada", "slatko", "slatkiš", "grickalica"],
  "tag_match_type": "any"
}

Query: "trebam šampon"
{
  "intent": "specific_product",
  "meal_type": null,
  "categories": ["Higijena"],
  "budget_max": null,
  "budget_min": null,
  "dietary_preferences": [],
  "exclude_categories": [],
  "search_tags": ["šampon"],
  "exclude_tags": [],
  "tag_match_type": "any"
}

Query: "nesto slatko za uzinu"
{
  "intent": "specific_product",
  "meal_type": "užina",
  "categories": ["Namirnice"],
  "budget_max": null,
  "budget_min": null,
  "dietary_preferences": [],
  "exclude_categories": [],
  "search_tags": ["slatko", "desert", "čokolada", "slatkiš", "užina"],
  "exclude_tags": [],
  "tag_match_type": "any"
}

Query: "zelim neke grickalice"
{
  "intent": "specific_product",
  "meal_type": null,
  "categories": [],
  "budget_max": null,
  "budget_min": null,
  "dietary_preferences": [],
  "exclude_categories": [],
  "search_tags": ["grickalice", "čokolada", "slatkiš", "slatko", "desert", "užina"],
  "exclude_tags": [],
  "tag_match_type": "any"
}

Query: "piletinu i cokoladu i deterdzent"
{
  "intent": "shopping_list",
  "meal_type": null,
  "categories": [],
  "budget_max": null,
  "budget_min": null,
  "dietary_preferences": [],
  "exclude_categories": [],
  "search_tags": ["piletina", "čokolada", "deterđent"],
  "exclude_tags": [],
  "tag_match_type": "any"
}"""

    user_prompt = f'Now extract from: "{user_query}"'

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap for structured extraction
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},  # Force valid JSON
            temperature=0.2,
            max_tokens=800
        )

        result_text = response.choices[0].message.content.strip()
        print(f"Stage 1 - Intent extraction for '{user_query}': {result_text}")

        # Clean markdown if present
        if "```" in result_text:
            result_text = re.search(r'\{.*\}', result_text, re.DOTALL).group(0)

        intent_data = json.loads(result_text)
        return intent_data

    except Exception as e:
        print(f"Error in extract_search_intent: {e}")
        import traceback
        traceback.print_exc()
        # Return basic fallback
        return {
            "intent": "specific_product",
            "meal_type": None,
            "categories": [],
            "budget_max": None,
            "budget_min": None,
            "dietary_preferences": [],
            "exclude_categories": [],
            "search_tags": [user_query.lower()],
            "exclude_tags": [],
            "tag_match_type": "any"
        }


def match_products_by_tags(intent_data, products_list):
    """
    STAGE 2: Match products based on extracted tags and filters.

    Args:
        intent_data: Output from extract_search_intent() with search_tags, categories, budget, etc.
        products_list: List of dicts with {id, title, category, tags, base_price, discount_price}

    Returns:
        List of product IDs that match the criteria
    """
    search_tags = [tag.lower() for tag in intent_data.get('search_tags', [])]
    exclude_tags = [tag.lower() for tag in intent_data.get('exclude_tags', [])]
    categories = intent_data.get('categories', [])
    exclude_categories = intent_data.get('exclude_categories', [])
    budget_max = intent_data.get('budget_max')
    budget_min = intent_data.get('budget_min')
    tag_match_type = intent_data.get('tag_match_type', 'any')

    matched_products = []

    for product in products_list:
        # Get product data
        product_id = product['id']
        product_tags = [tag.lower() for tag in (product.get('tags') or [])]
        product_category = product.get('category', '')
        final_price = product.get('discount_price') or product.get('base_price')

        # Filter by excluded categories
        if exclude_categories and product_category in exclude_categories:
            continue

        # Filter by included categories (if specified)
        if categories and product_category not in categories:
            continue

        # Filter by budget
        if budget_max and final_price and final_price > budget_max:
            continue
        if budget_min and final_price and final_price < budget_min:
            continue

        # Filter by excluded tags
        if exclude_tags:
            has_excluded = any(exc_tag in product_tags for exc_tag in exclude_tags)
            if has_excluded:
                continue

        # Match by search tags
        if search_tags:
            if tag_match_type == 'all':
                # All search tags must match
                matches = all(any(s_tag in p_tag for p_tag in product_tags) for s_tag in search_tags)
            else:  # 'any'
                # At least one search tag must match
                matches = any(any(s_tag in p_tag or p_tag in s_tag for p_tag in product_tags) for s_tag in search_tags)

            if matches:
                matched_products.append(product_id)
        else:
            # No search tags, just category/budget filtering
            matched_products.append(product_id)

    print(f"Stage 2 - Tag matching: {len(matched_products)} products matched from {len(products_list)} total")
    print(f"  Search tags: {search_tags}")
    print(f"  Exclude tags: {exclude_tags}")
    print(f"  Matched IDs: {matched_products}")

    return matched_products


def smart_rank_products(original_query, intent_data, candidate_products):
    """
    STAGE 3: Smart filtering and ranking using LLM reasoning.

    Args:
        original_query: Original user query
        intent_data: Output from Stage 1
        candidate_products: List of product dicts with full details (from Stage 2)

    Returns:
        dict with selected_products, total_cost, meal_suggestion, budget_status
    """
    # Prepare products data for LLM
    products_for_llm = []
    for p in candidate_products:
        product_dict = {
            "id": p.id if hasattr(p, 'id') else p.get('id'),
            "title": p.title if hasattr(p, 'title') else p.get('title'),
            "category": p.category if hasattr(p, 'category') else p.get('category'),
            "tags": p.tags if hasattr(p, 'tags') else p.get('tags', []),
            "original_price": p.base_price if hasattr(p, 'base_price') else p.get('base_price'),
            "final_price": (p.discount_price if hasattr(p, 'discount_price') else p.get('discount_price')) or
                           (p.base_price if hasattr(p, 'base_price') else p.get('base_price')),
            "discount_percentage": 0,
            "store_name": p.business.name if hasattr(p, 'business') else p.get('business', {}).get('name', 'Unknown')
        }

        # Calculate discount percentage
        if product_dict['final_price'] and product_dict['original_price']:
            if product_dict['final_price'] < product_dict['original_price']:
                product_dict['discount_percentage'] = int(
                    ((product_dict['original_price'] - product_dict['final_price']) / product_dict['original_price']) * 100
                )

        products_for_llm.append(product_dict)

    products_json = json.dumps(products_for_llm, ensure_ascii=False, indent=2)
    intent_json = json.dumps(intent_data, ensure_ascii=False, indent=2)

    system_prompt = """You are a Bosnian meal planning and shopping expert.

YOUR TASK: Analyze user intent and select 8-12 most relevant products from pre-filtered candidates.

SELECTION CRITERIA:

1. **Respect Search Tags** (MOST IMPORTANT):
   - User's search_tags tell you what they want
   - If search_tags = ["piletina", "čokolada"], include BOTH types
   - Products are already filtered by these tags

2. **Meal Composition** (for meal_prep intent):
   - "ručak"/"večera" needs: 1-2 proteins + 1-2 carbs + 1-2 vegetables
   - Avoid repetition (don't select 5 chicken products)
   - Think complete meal: "piletina + riža + paradajz" = good

3. **Dietary Preferences**:
   - "zdravo" = prioritize lean proteins, vegetables; deprioritize processed
   - Search/exclude tags already reflect dietary preferences

4. **Budget Optimization**:
   - If budget specified, stay UNDER budget (leave room for error)
   - Provide good value (high discount_percentage)
   - Make sense together

5. **Shopping List Intent**:
   - User listed specific items → find ALL of them
   - Don't add unrequested items

6. **Practical Value**:
   - Prefer products with higher discounts
   - Consider portion sizes
   - Products from same store are convenient

RETURN FORMAT (valid JSON only, no markdown):
{
  "selected_products": [
    {
      "id": 123,
      "relevance_score": 0.95,
      "reason": "Main protein for lunch, excellent discount"
    }
  ],
  "total_estimated_cost": 18.50,
  "meal_suggestion": "Možete napraviti: piletina sa rižom i povrćem",
  "budget_status": "under_budget" | "at_budget" | "over_budget",
  "remaining_budget": 1.50
}

STRICT RULES:
- Return 8-12 products (unless shopping_list with fewer specific items)
- All IDs must exist in provided candidates
- Total cost ≤ budget_max (if specified)
- Rank by relevance_score (1.0 = perfect, 0.5 = acceptable)
- meal_suggestion in Bosnian, natural language
- For meal_prep: ensure variety (not all same category)
- For shopping_list: prioritize finding requested items"""

    user_prompt = f"""ORIGINAL USER QUERY: "{original_query}"

EXTRACTED INTENT:
{intent_json}

PRE-FILTERED PRODUCTS (already filtered by tags, categories, price):
{products_json}

Now analyze and select 8-12 most relevant products."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Use gpt-4o for better reasoning if available, fallback to gpt-4o-mini
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},  # Force valid JSON
            temperature=0.4,
            max_tokens=1500
        )

        result_text = response.choices[0].message.content.strip()
        print(f"Stage 3 - Smart ranking response: {result_text[:200]}...")

        # Clean markdown if present
        if "```" in result_text:
            result_text = re.search(r'\{.*\}', result_text, re.DOTALL).group(0)

        ranking_result = json.loads(result_text)
        return ranking_result

    except Exception as e:
        print(f"Error in smart_rank_products: {e}")
        import traceback
        traceback.print_exc()

        # Fallback: return all products with basic ranking
        return {
            "selected_products": [
                {"id": p.id if hasattr(p, 'id') else p.get('id'), "relevance_score": 0.8, "reason": "Matched search criteria"}
                for p in candidate_products[:12]
            ],
            "total_estimated_cost": sum([
                (p.discount_price if hasattr(p, 'discount_price') else p.get('discount_price')) or
                (p.base_price if hasattr(p, 'base_price') else p.get('base_price'))
                for p in candidate_products[:12]
            ]),
            "meal_suggestion": None,
            "budget_status": "unknown",
            "remaining_budget": None
        }


def match_products_by_intent(user_query, products_list):
    """
    Master Chef + NLP Expert that matches products to user intent.

    Args:
        user_query: User's search query (e.g., 'zelim da jedem zdravo danas', 'proizvodi ispod 10 KM')
        products_list: List of dicts with {id, title, category, base_price, discount_price}

    Returns:
        List of product IDs that match the user's intent
    """
    if not products_list:
        return []

    # Prepare product list as text for AI with full price information
    products_text = "\n".join([
        f"ID: {p['id']}, Title: {p['title']}, Category: {p.get('category', 'N/A')}, "
        f"Original Price: {p.get('base_price')} KM, "
        f"Sale Price: {p.get('discount_price') or 'N/A'} KM, "
        f"Final Price: {p.get('discount_price') or p.get('base_price')} KM"
        for p in products_list
    ])

    system_prompt = """You are a Master Chef and NLP Expert for a Bosnian marketplace. Your job is to understand user intent and match ONLY relevant products.

CRITICAL RULES:
1. FOOD queries (ručak, jelo, hrana, kuvati, jesti) → ONLY return FOOD products (Meso, Namirnice categories)
2. "Healthy" food (zdravo jesti) → chicken/meat, NOT chocolate/sweets
3. CLEANING queries (čišćenje, pranje) → ONLY cleaning products (Čišćenje category)
4. HYGIENE queries (higijena) → ONLY hygiene products (Higijena category)
5. AUTOMOTIVE queries (auto, motorno ulje) → ONLY automotive products
6. BABY queries (bebe, djeca) → ONLY baby products
7. BUDGET constraints → ONLY products where Final Price is BELOW the specified amount
8. SHOPPING LISTS → If user lists multiple items (lista za kupovinu, 1. X, 2. Y), find ALL items mentioned
9. BE STRICT: Don't return products from wrong categories (except for shopping lists where user explicitly lists different categories)

Examples:
- "napravim ručak ispod 20 KM" → ONLY Meso/Namirnice under 20 KM (chicken=YES, coffee=NO, chocolate=NO, cleaning=NO)
- "želim da jedem zdravo" → chicken YES, chocolate NO, cleaning NO
- "trebam nešto za čišćenje" → cleaning products ONLY, NOT food
- "motorno ulje ispod 50 KM" → motor oil products under 50 KM ONLY
- "piletina, šampon i deterđent" → find ALL three items
- "lista za kupovinu: 1. meso 2. čokolada" → find BOTH chicken/meat AND chocolate (user explicitly listed both)

Return ONLY a JSON array of product IDs that STRICTLY match: [1, 5, 7]
If no products match, return: []"""

    user_prompt = f"""User query: "{user_query}"

Available products:
{products_text}

Task: Analyze the user's query and return ONLY product IDs that STRICTLY match their intent.
- If they want food/lunch (ručak), return ONLY products from Meso or Namirnice categories
- If they mention a budget, ONLY include products under that price
- DO NOT include unrelated categories (no cleaning products for food queries, no chocolate for healthy eating)

Return ONLY the matching product IDs as a JSON array: [1, 3, 5]"""

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Lower temperature for more consistent, strict matching
            max_tokens=500
        )

        result_text = response.choices[0].message.content.strip()
        print(f"AI Response for query '{user_query}': {result_text}")

        # Parse the JSON array of IDs
        # Handle if AI returns markdown code blocks
        if "```" in result_text:
            result_text = re.search(r'\[.*\]', result_text, re.DOTALL).group(0)

        product_ids = json.loads(result_text)

        # Validate that all IDs are integers
        product_ids = [int(pid) for pid in product_ids if isinstance(pid, (int, str)) and str(pid).isdigit()]

        print(f"Matched product IDs: {product_ids}")
        return product_ids

    except Exception as e:
        print(f"Error in match_products_by_intent: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: return empty list if AI fails (don't return all products)
        return []


def normalize_text_for_search(text):
    """Remove diacritics and normalize text for search comparison"""
    if not text:
        return ""
    # Convert to lowercase and remove diacritics
    normalized = unicodedata.normalize('NFD', text.lower())
    # Remove combining characters (diacritics)
    ascii_text = ''.join(char for char in normalized
                         if unicodedata.category(char) != 'Mn')
    return ascii_text


def normalize_expiry_date(result):
    """Normalize and validate expiry date field"""
    if not isinstance(result, dict):
        return result

    # Ensure expires field exists
    if 'expires' not in result:
        result['expires'] = None
        return result

    expires = result.get('expires')
    if not expires or expires == "null":
        result['expires'] = None
        return result

    # Check if already in correct ISO format
    iso_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if isinstance(expires, str) and re.match(iso_pattern, expires):
        # Validate it's a real date
        try:
            datetime.strptime(expires, '%Y-%m-%d')
            return result
        except ValueError:
            result['expires'] = None
            return result

    # Try to normalize common formats
    if isinstance(expires, str):
        expires = expires.strip()

        # Bosnian months mapping
        months = {
            'januar': '01',
            'januara': '01',
            'jan': '01',
            'februar': '02',
            'februara': '02',
            'feb': '02',
            'mart': '03',
            'marta': '03',
            'mar': '03',
            'april': '04',
            'aprila': '04',
            'apr': '04',
            'maj': '05',
            'maja': '05',
            'juni': '06',
            'juna': '06',
            'jun': '06',
            'juli': '07',
            'jula': '07',
            'jul': '07',
            'august': '08',
            'avgusta': '08',
            'avg': '08',
            'septembar': '09',
            'septembra': '09',
            'sep': '09',
            'oktobar': '10',
            'oktobra': '10',
            'okt': '10',
            'novembar': '11',
            'novembra': '11',
            'nov': '11',
            'decembar': '12',
            'decembra': '12',
            'dec': '12'
        }

        # Try dd.mm.yyyy or d.m.yyyy
        dot_pattern = r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
        match = re.search(dot_pattern, expires)
        if match:
            day, month, year = match.groups()
            try:
                normalized = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                datetime.strptime(normalized, '%Y-%m-%d')  # Validate
                result['expires'] = normalized
                return result
            except ValueError:
                pass

        # Try dd/mm/yyyy or d/m/yyyy
        slash_pattern = r'(\d{1,2})/(\d{1,2})/(\d{2,4})'
        match = re.search(slash_pattern, expires)
        if match:
            day, month, year = match.groups()
            if len(year) == 2:
                year = f"20{year}"  # Assume 2000s
            try:
                normalized = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                datetime.strptime(normalized, '%Y-%m-%d')  # Validate
                result['expires'] = normalized
                return result
            except ValueError:
                pass

        # Try "dd month yyyy" format
        for month_name, month_num in months.items():
            pattern = rf'(\d{{1,2}})\s+{month_name}\s+(\d{{4}})'
            match = re.search(pattern, expires.lower())
            if match:
                day, year = match.groups()
                try:
                    normalized = f"{year}-{month_num}-{day.zfill(2)}"
                    datetime.strptime(normalized, '%Y-%m-%d')  # Validate
                    result['expires'] = normalized
                    return result
                except ValueError:
                    pass

    # If we can't normalize, set to None
    result['expires'] = None
    return result


def parse_user_preferences(preference_text):
    """Parse user preference text using OpenAI to extract city and interests"""
    try:
        prompt = f"""
        Analiziraj sledeći tekst o korisničkim preferencijama i izvuci grad i kategorije interesovanja.
        Vrati rezultat u JSON formatu sa poljima: city, categories, budget.
        Kategorije treba da budu lista stringova.
        Budget može biti: "low", "medium", "high".
        
        Tekst: "{preference_text}"
        
        Odgovori samo sa JSON objektom, bez dodatnog teksta.
        """

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{
                "role":
                "system",
                "content":
                "Ti si pomoćnik koji parsira korisničke preferencije u JSON format."
            }, {
                "role": "user",
                "content": prompt
            }],
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        # Return default values if parsing fails
        return {"city": "Tuzla", "categories": ["opšte"], "budget": "medium"}


def parse_product_text(product_text):
    """Parse free-text product description into structured data"""
    try:
        prompt = f"""
        Analiziraj sledeći opis proizvoda i izvuci strukturirane podatke.
        Vrati rezultat u JSON formatu sa poljima:
        - title (string): naziv proizvoda
        - base_price (number): osnovna cena
        - discount_price (number ili null): cena sa popustom
        - expires (string ili null): OBAVEZNO tačno format "YYYY-MM-DD" ili null ako nema datuma
        - category (string): kategorija proizvoda
        - tags (array): OBAVEZNO lista tagova (minimum 3-5 tagova)
        - product_metadata (object): dodatni podaci kao brand, size, warranty

        NAZIV PROIZVODA PRAVILA:
        - OBAVEZNO čuvaj sve bosanske dijakritike (ć, č, š, ž, đ)
        - Piši gramatički ispravno: "juneće" ne "junece", "svježe" ne "svjeze", "pileće" ne "pilece"
        - Koristi ispravne padežne oblike i množinu
        - Primjeri: "Mljeveno juneće meso", "Svježi sir", "Pečene kobasice", "Svježe voće"
        - Nikad ne zamjenjuj dijakritike običnim slovima

        TAGOVI PRAVILA (OBAVEZNO):
        - UVIJEK generiši minimum 3-5 relevantnih tagova
        - Tagovi su lowercase, bez dijakritika za lakše pretraživanje
        - Tagovi uključuju: vrstu proizvoda, kategoriju, sinonime, namenu

        Primjeri tagova:
        "Mljeveno meso" → ["meso", "mljeveno meso", "govedina", "hrana", "protein"]
        "Piletina svježa" → ["piletina", "meso", "svjeze", "hrana", "protein", "belo meso"]
        "Milka čokolada" → ["cokolada", "milka", "slatkis", "desert", "grickalica"]
        "Head & Shoulders šampon" → ["sampon", "head shoulders", "higijena", "kosa", "njega"]
        "Persil deterdžent" → ["deterdent", "persil", "pranje", "ciscenje", "higijena"]

        DATUM PRAVILA:
        - Traži fraze: "do", "važi do", "rok trajanja", "istice", "vrijedi do"
        - MORA biti format "YYYY-MM-DD" sa nulama (2025-09-22, ne 2025-9-2)
        - Ako format nije tačan, stavi null

        Primjeri datuma:
        "do 22 Septembra 2025" → "2025-09-22"
        "važi do 5.10.2025" → "2025-10-05"
        "rok trajanja 01.12.2025" → "2025-12-01"
        "do 5/10/25" → "2025-10-05"

        Tekst: "{product_text}"

        Odgovori samo sa JSON objektom, bez dodatnog teksta.
        """

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{
                "role":
                "system",
                "content":
                "Ti si pomoćnik koji parsira opise proizvoda u JSON format."
            }, {
                "role": "user",
                "content": prompt
            }],
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)

        # Validate and normalize expiry date
        result = normalize_expiry_date(result)
        return result

    except Exception as e:
        # Return default structure if parsing fails
        return {
            "title": product_text[:100],
            "base_price": 0,
            "discount_price": None,
            "expires": None,
            "category": "ostalo",
            "tags": [],
            "product_metadata": {}
        }


def generate_enriched_description(product_title, category=None):
    """
    Generate a rich, semantic search-optimized description for a product.

    Args:
        product_title: Product title/name
        category: Optional product category

    Returns:
        String containing one paragraph optimized for vector search
    """
    try:
        # Build the input for the prompt
        product_info = product_title
        if category:
            product_info = f"{product_title} (kategorija: {category})"

        system_prompt = """Ti si ekspert za opis proizvoda i tvoj zadatak je da napišeš jedan bogat, detaljan paragraf koji maksimizira semantičku pretragu u vektorskoj bazi podataka.
Opis treba da pomogne algoritmu da pronađe proizvod čak i kada korisnik pretražuje koristeći djelimične informacije, sinonime, namjere ili opisne fraze.

Pridržavaj se sljedećih pravila:

Uvijek uključi tačan naziv proizvoda onako kako je dat u inputu.

Piši jedan paragraf, 3–6 rečenica.

U opis uvrsti sinonime, alternativne nazive, tipične upotrebe, kontekst, korisničke namjere i terminologiju specifičnu za kategoriju proizvoda.

Ne koristi marketinški stil — budi jasan, informativan i faktografski.

Ne izmišljaj sastojke; koristi samo ono što je tipično za kategoriju proizvoda.

Uključuj riječi i fraze koje ljudi često koriste u pretragama za tu vrstu proizvoda (npr. svježina, zaštita zuba, začin za variva, začin za gulaš, higijena, miris, okus — zavisno od proizvoda).

Ton treba biti prirodan, koherentan, bez listi i bez tačaka.

Zabranjene su liste, bullet points i podnaslovi — samo jedan tečan paragraf.

TASK
Na osnovu naziva proizvoda ispod, generiši jedan paragraf optimizovan za semantičku pretragu.

OUTPUT:
Jedan paragraf koji uključuje:
- kategoriju i namjenu proizvoda
- sinonime i riječi koje korisnici često ukucavaju
- tipične kontekste upotrebe
- povezana svojstva, arome, mirise, funkcije
- koristi i situacije u kojima se proizvod koristi
- dodatne fraze relevantne za pretragu"""

        user_prompt = f"""INPUT:
{product_info}

OUTPUT:"""

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        description = response.choices[0].message.content.strip()
        return description

    except Exception as e:
        # Fallback to basic description if AI fails
        return f"{product_title} je proizvod" + (f" iz kategorije {category}" if category else "") + "."


def generate_search_filters(query):
    """Generate search filters from user query - SIMPLIFIED"""
    query_lower = query.lower()

    # Extract keywords from query
    keywords = []

    # Common food items
    food_keywords = {
        'meso': [
            'meso', 'govedina', 'piletina', 'juneće', 'junetina', 'svinjsko',
            'pileće'
        ],
        'piletina': ['piletina', 'pile', 'file', 'pileće'],
        'govedina': ['govedina', 'junetina', 'juneće'],
        'mlijeko': ['mlijeko', 'mleko'],
        'sir': ['sir', 'svježi sir'],
        'jaja': ['jaja', 'jaje'],
        'hleb': ['hleb', 'kruh'],
        'voće': ['voće', 'banane', 'jabuke', 'naranče', 'svježe voće'],
        'povrće': ['povrće', 'paradajz', 'luk', 'krompir', 'svježe povrće']
    }

    # Find matching keywords
    for category, words in food_keywords.items():
        for word in words:
            if word in query_lower:
                keywords.append(word)
                break

    # If no specific keywords found, use the query
    if not keywords:
        keywords = [query.strip()]

    # Check for discount keywords
    discount_only = any(word in query_lower
                        for word in ['popust', 'akcija', 'snižen', 'jeftin'])

    # Check for cities
    cities = [
        'tuzla', 'sarajevo', 'banja luka', 'mostar', 'zenica', 'bijeljina'
    ]
    city = None
    for c in cities:
        if c in query_lower:
            city = c.title()
            break

    # Simple category detection
    category = None
    if any(word in query_lower for word in ['meso', 'piletina', 'govedina']):
        category = 'Meso'
    elif any(word in query_lower for word in ['mlijeko', 'sir', 'jogurt']):
        category = 'Mliječni proizvodi'
    elif any(word in query_lower for word in ['voće', 'banane']):
        category = 'Voće'
    elif any(word in query_lower for word in ['povrće', 'paradajz']):
        category = 'Povrće'

    return {
        "category": category,
        "city": city,
        "max_price": None,
        "keywords": keywords,
        "discount_only": discount_only
    }


def generate_single_ai_response(query, products):
    """Single AI call to generate structured response with only existing fields"""
    try:
        # Prepare clean product data - only include fields that exist
        clean_products = []
        for product in products:
            # Handle both product objects and serialized dictionaries
            if isinstance(product, dict):
                # Product is already a serialized dictionary from product_to_dict()
                product_data = {
                    "title":
                    product.get("title"),
                    "base_price":
                    product.get("base_price"),
                    "business_name":
                    product.get("business", {}).get("name", "Unknown"),
                    "city":
                    product.get("city")
                    or product.get("business", {}).get("city", "Unknown")
                }

                # Only add fields that have values
                if product.get("discount_price") and product.get(
                        "discount_price") < product.get("base_price"):
                    product_data["discount_price"] = product.get(
                        "discount_price")

                if product.get("expires"):
                    # Handle ISO date format
                    from datetime import datetime
                    try:
                        if isinstance(product.get("expires"), str):
                            expires_date = datetime.fromisoformat(
                                product.get("expires"))
                            if expires_date.date() >= date.today():
                                product_data[
                                    "expires"] = expires_date.strftime(
                                        '%d.%m.%Y')
                    except:
                        pass

                if product.get("category"):
                    product_data["category"] = product.get("category")

                if product.get("business", {}).get("logo_path"):
                    product_data["business_logo"] = product.get(
                        "business", {}).get("logo_path")

            else:
                # Product might be an object or a different dict format - handle both
                app.logger.warning(f"Product in unexpected format: {type(product)}")
                
                try:
                    # Try to handle as object first
                    if hasattr(product, '__dict__'):
                        product_data = {
                            "title": getattr(product, 'title', 'Unknown'),
                            "base_price": getattr(product, 'base_price', 0),
                            "business_name": "Unknown",
                            "city": getattr(product, 'city', 'Unknown')
                        }

                        # Try to get business info safely
                        if hasattr(product, 'business') and product.business:
                            product_data["business_name"] = getattr(product.business, 'name', 'Unknown')
                            if hasattr(product.business, 'logo_path') and product.business.logo_path:
                                product_data["business_logo"] = product.business.logo_path
                        elif hasattr(product, 'business_name'):
                            product_data["business_name"] = getattr(product, 'business_name', 'Unknown')

                        # Handle discount price
                        discount_price = getattr(product, 'discount_price', None)
                        if discount_price and discount_price < product_data["base_price"]:
                            product_data["discount_price"] = discount_price

                        # Handle expires
                        expires = getattr(product, 'expires', None)
                        if expires:
                            from datetime import date, datetime
                            try:
                                if isinstance(expires, str):
                                    expires_date = datetime.strptime(expires, '%Y-%m-%d').date()
                                    if expires_date >= date.today():
                                        product_data["expires"] = expires_date.strftime('%d.%m.%Y')
                                elif hasattr(expires, 'date') and expires.date() >= date.today():
                                    product_data["expires"] = expires.strftime('%d.%m.%Y')
                            except:
                                pass

                        # Handle category
                        category = getattr(product, 'category', None)
                        if category:
                            product_data["category"] = category

                    else:
                        # Fallback: treat as unknown format
                        product_data = {
                            "title": str(product) if product else "Unknown Product",
                            "base_price": 0,
                            "business_name": "Unknown Business",
                            "city": "Unknown"
                        }
                        
                except Exception as format_error:
                    app.logger.error(f"Error processing unexpected product format: {format_error}")
                    product_data = {
                        "title": "Unknown Product",
                        "base_price": 0,
                        "business_name": "Unknown Business", 
                        "city": "Unknown"
                    }

            clean_products.append(product_data)

        prompt = f"""
        Korisnik je pitao: "{query}"
        
        Proizvodi pronađeni:
        {json.dumps(clean_products, ensure_ascii=False, indent=2)}
        
        Vrati JSON odgovor sa:
        {{
            "success": true,
            "response": "kratak tekst odgovor na bosanskom",
            "products_count": broj_proizvoda,
            "products": [lista proizvoda sa SAMO postojećim poljima]
        }}
        
        OBAVEZNA PRAVILA - PRATI IH STRIKTNO:
        
        ⚠️ NIKAD ne koristit generičke odgovore kao "Pronašao sam X proizvoda"
        ⚠️ UVIJEK počni sa emotikonom i detaljnim opisom
        ⚠️ UVIJEK navedi konkretne cijene i nazive trgovina
        
        FORMAT ODGOVORA:
        1. Počni sa emotikonom povezanim sa kategorijom
        2. Navedi konkretne proizvode sa cijenama 
        3. Spomeni nazive trgovina
        4. Za popuste koristi format "(umjesto X KM)"
        5. Završi sa "Pogledajte cijene i kontaktirajte ih za više informacija"
        
        OBAVEZNO KORISTI HTML STYLING ZA CIJENE:
        - Popust/niža cijena: <span style="background-color: #dcfce7; color: #16a34a; padding: 2px 4px; border-radius: 3px; font-weight: bold;">7.5 KM</span>
        - Originalna/prethodna cijena (SAMO kad ima popust): <span style="background-color: #fecaca; color: #dc2626; padding: 2px 4px; border-radius: 3px; text-decoration: line-through;">8.8 KM</span>
        - Obična cijena (bez popusta): <span style="background-color: #f3f4f6; color: #374151; padding: 2px 4px; border-radius: 3px; font-weight: bold;">7.95 KM</span>
        
        VAŽNO: Koristi crossed-out (line-through) styling SAMO za originalnu cijenu kada proizvod ima aktivni popust!
        
        EMOJI MAPIRANJE:
        - Meso: 🥩 (govedina, junettina, svinjetina), 🐔 (piletina), 🥓 (kobasice)
        - Voće: 🍎 🍌 🍊 🍇 🍓 🍑
        - Mliječni: 🥛 🧀 🧈 🍦
        - Povrće: 🥕 🥔 🍅 🥒 🧅
        - Tehnika: 📱 💻 📺 🎧
        - Auto: 🚗 🔧 ⚙️
        
        PRIMJER ODLIČNOG ODGOVORA:
        "🥩 Mljeveno meso je danas na popustu - u Bingu za <span style=\"background-color: #dcfce7; color: #16a34a; padding: 2px 4px; border-radius: 3px; font-weight: bold;\">10 KM</span> (umjesto <span style=\"background-color: #fecaca; color: #dc2626; padding: 2px 4px; border-radius: 3px; text-decoration: line-through;\">15 KM</span>), u Menpromu za <span style=\"background-color: #dcfce7; color: #16a34a; padding: 2px 4px; border-radius: 3px; font-weight: bold;\">14 KM</span> (umjesto <span style=\"background-color: #fecaca; color: #dc2626; padding: 2px 4px; border-radius: 3px; text-decoration: line-through;\">20 KM</span>), a govedina mljevano u Bingu za <span style=\"background-color: #dcfce7; color: #16a34a; padding: 2px 4px; border-radius: 3px; font-weight: bold;\">7.5 KM</span> (umjesto <span style=\"background-color: #fecaca; color: #dc2626; padding: 2px 4px; border-radius: 3px; text-decoration: line-through;\">8.8 KM</span>). Pogledajte cijene i kontaktirajte ih za više informacija."
        
        ⚠️ STRIKTNO ZABRANJENO: "Pronašao sam", "Evo rezultata", generički odgovori
        """

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role":
                "system",
                "content":
                "Vraćaš strukturirane odgovore u JSON formatu sa samo postojećim podacima."
            }, {
                "role": "user",
                "content": prompt
            }],
            response_format={"type": "json_object"},
            max_tokens=500,
            temperature=0.3)

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        # Simple fallback response with safe data access
        clean_products = []
        for product in products:
            from models import Business
            from app import db
            
            # Safely get values from both dict and object
            def safe_get(obj, key, default=None):
                if isinstance(obj, dict):
                    return obj.get(key, default)
                else:
                    return getattr(obj, key, default)
            
            business_id = safe_get(product, 'business_id')
            business = None
            if business_id:
                business = db.session.query(Business).filter(
                    Business.id == business_id).first()

            base_price = safe_get(product, 'base_price')
            discount_price = safe_get(product, 'discount_price')
            
            product_data = {
                "title": safe_get(product, 'title'),
                "base_price": base_price,
                "business_name": business.name if business else "Unknown",
                "city": safe_get(product, 'city') or (business.city if business else "Unknown")
            }

            if discount_price and base_price and float(discount_price) < float(base_price):
                product_data["discount_price"] = discount_price

            clean_products.append(product_data)

        if products:
            return {
                "success": True,
                "response":
                f"Pronašao sam {len(products)} proizvoda koji odgovaraju vašoj pretrazi.",
                "products_count": len(products),
                "products": clean_products
            }
        else:
            return {
                "success": True,
                "response":
                "Nažalost, nisam pronašao proizvode koji odgovaraju vašoj pretrazi.",
                "products_count": 0,
                "products": []
            }


def get_dynamic_categories_and_tags():
    """Dynamically fetch all categories and tags from the database"""
    try:
        from models import Product
        from app import db
        import logging
        
        logging.info("Starting dynamic categories fetch...")

        # Get all unique categories
        categories_result = db.session.query(Product.category).filter(
            Product.category.isnot(None)).distinct().all()
        categories = [cat[0] for cat in categories_result if cat[0]]
        logging.info(f"Found {len(categories)} categories")

        # Get all unique tags from JSON arrays - simplified approach
        # First try the simple query without tags
        tags = []
        try:
            from sqlalchemy import text
            tags_query = text("""
            SELECT DISTINCT jsonb_array_elements_text(tags::jsonb) as tag 
            FROM products 
            WHERE tags IS NOT NULL AND tags::text != 'null'
            """)
            tags_result = db.session.execute(tags_query).fetchall()
            tags = [tag[0] for tag in tags_result if tag[0]]
            logging.info(f"Found {len(tags)} tags")
        except Exception as tag_error:
            logging.error(f"Tags query failed: {tag_error}")
            # Just use basic tags if JSON query fails
            tags = ['bijeli', 'prirodni', 'brašno', 'pšenično', 'domaći', 'popust', 'akcija']

        logging.info(f"Returning {len(categories)} categories and {len(tags)} tags")
        return sorted(categories), sorted(tags)

    except Exception as e:
        import logging
        logging.error(f"Dynamic categories failed: {e}")
        # Fallback to hardcoded lists if database query fails
        return ([
            'Pekarski proizvodi', 'Voće', 'Ulja i začini', 'Svježi proizvodi',
            'Povrće', 'Meso', 'Mliječni proizvodi', 'Osnovno'
        ], [
            'bijeli', 'prirodni', 'brašno', 'pšenično', 'suncokret', 'ulje',
            'svježa', 'povrće', 'mljeveno', 'akcija', 'pekara', 'jaja', 'hleb',
            'mlijeko', 'A klasa', 'uvoz', 'popust', 'domaći', 'banane',
            'junetina', 'šećer', 'jogurt', 'mljevano', 'piletina', 'svježe',
            'govedina', 'voće', 'svježi', 'paradajz', 'file', 'mljeveno meso',
            'kristal', 'meso', 'danas', 'sir'
        ])


def generate_search_sql(query):
    """Generate complete SQL query using LLM with database schema knowledge"""
    try:
        # Get current categories and tags from database
        available_categories, available_tags = get_dynamic_categories_and_tags(
        )

        schema_info = f"""
        DATABASE SCHEMA:
        
        TABLE: products
        - id: INTEGER PRIMARY KEY
        - business_id: INTEGER (Foreign Key to businesses.id)
        - city: VARCHAR (može biti NULL)
        - title: VARCHAR NOT NULL (naziv proizvoda)
        - base_price: FLOAT NOT NULL (osnovna cijena)
        - discount_price: FLOAT (cijena sa popustom, može biti NULL)
        - expires: DATE (datum isteka, može biti NULL)
        - category: VARCHAR (kategorija proizvoda, može biti NULL)
        - tags: JSON (array stringova, može biti NULL)
        - product_metadata: JSON (dodatni podaci, može biti NULL)
        - image_path: VARCHAR (može biti NULL)
        - views: INTEGER (broj pregleda)
        - created_at: TIMESTAMP
        
        TABLE: businesses
        - id: INTEGER PRIMARY KEY
        - name: VARCHAR NOT NULL (ime poslovanja)
        - contact_phone: VARCHAR (može biti NULL)
        - city: VARCHAR (grad, default 'Tuzla')
        - logo_path: VARCHAR (može biti NULL)
        - status: VARCHAR (default 'active')
        
        DOSTUPNE KATEGORIJE: {', '.join(available_categories)}
        DOSTUPNI TAGOVI: {', '.join(available_tags)}
        
        ## KRITIČNA PRAVILA ZA SQL:
        1. UVIJEK JOIN sa businesses: FROM products JOIN businesses ON products.business_id = businesses.id
        2. Proizvodi sa isteklim popustom se i dalje prikazuju (bez filtera na expires)
        3. Za pretragu koristiti SAMO ILIKE - NIKAD jsonb operatore!
        4. Sortiranje: ORDER BY COALESCE(products.discount_price, products.base_price) ASC, products.views DESC
        5. LIMIT 50
        
        ## OBAVEZNA SELECT STRUKTURA:
        SELECT products.*, 
               businesses.name AS business_name,
               businesses.city AS business_city,
               businesses.contact_phone,
               businesses.logo_path
        FROM products JOIN businesses ON products.business_id = businesses.id
        
        ## PRIMJERI ISPRAVNIH UPITA:
        Za "šampon":
        WHERE products.title ILIKE '%šampon%' OR products.category ILIKE '%higijena%'
        
        Za "slatko":  
        WHERE products.category ILIKE '%slatkiš%' OR products.title ILIKE '%čokola%'
        
        Za "piletina u Tuzli":
        WHERE products.title ILIKE '%piletina%' AND (products.city = 'Tuzla' OR businesses.city = 'Tuzla')

        ## AUTOMATSKA KOREKCIJA TIPOVA I KARAKTERA:
        UVIJEK ispraviti slova bez dijakritika u Bosanski/Hrvatski/Srpski:
        - "sampon" → "šampon" 
        - "cokolada" → "čokolada"
        - "secer" → "šećer"
        - "caj" → "čaj"
        - "pice" → "piće"  
        - "duvan" → "duhan"
        - "brasno" → "brašno"
        - "kafa" → "kafa" (već ispravno)
        - "mesa" → "mesa" (već ispravno)
        - "tjestenina/testenina" → "tjestenina"
        
        UVIJEK koristiti ispravljena slova u SQL upitima da odgovara podacima u bazi.

        ## Balkan Cultural Context
        - "šampon", "higijena", "sapun" → category "Higijena" or "Kozmetika"
        - "slatko", "desert" → category "Slatkiši" ili title čokolada/keks/bombon
        - "meso", "piletina" → category "Meso" ili title piletina/govedina
        - "piće", "napici" → category "Pića" ili "Sokovi"

        """

        prompt = f"""
        ANALIZIRAJ korisnikov upit i generiši PostgreSQL SQL.
        
        {schema_info}
        
        Korisnikov upit: "{query}"
        
        MAPIRANJE PRIRODNOG JEZIKA:
        
        Example mapping:
        - User: "Piletina u Tuzli" → filter by `p.title ILIKE '%piletina%' OR p.tags::jsonb @>         '["piletina"]'`.
        - User: "Želim nešto slatko" → map to tags `[čokolada, sladoled, keks, napolitanke, puding, banane, jogurt]` and categories `[Mliječni proizvodi]`.
        - User: "Večeras gledam film sa porodicom, volim da grickamo nešto slatko" → expand to `[čokolada, sladoled, čips, flips, kikiriki, štapići, napolitanke, puding]`.

        Your job:  
        Given a user’s natural language request, **analyze the intent**, map it to relevant categories/tags in Balkan context, and generate an **optimized SQL query** following all rules.
        
        Vrati JSON:
        {{
            "sql_query": "kompletan SELECT statement",
            "explanation": "kratak opis"
        }}
        """

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role":
                "system",
                "content":
                "Ti si ekspert za PostgreSQL. Generiši kompletne i optimizovane SQL queries na osnovu schema-e."
            }, {
                "role": "user",
                "content": prompt
            }],
            response_format={"type": "json_object"},
            max_tokens=800,
            temperature=0.1)

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        # Fallback to simple query if LLM fails
        words = query.lower().split()
        stop_words = [
            'gdje', 'kupiti', 'najjeftinije', 'trebam', 'da', 'u', 'i', 'za',
            'na'
        ]
        key_words = [w for w in words if w not in stop_words and len(w) > 2]
        search_term = ' '.join(key_words[:2]) if key_words else query.strip()

        fallback_sql = f"""
        SELECT products.*, businesses.name as business_name, businesses.city as business_city, 
               businesses.contact_phone, businesses.logo_path
        FROM products 
        JOIN businesses ON products.business_id = businesses.id 
        WHERE (products.title ILIKE '%{search_term}%' OR products.category ILIKE '%{search_term}%')
        ORDER BY products.discount_price ASC NULLS LAST 
        LIMIT 50
        """

        return {
            "sql_query": fallback_sql,
            "explanation": f"Fallback query searching for '{search_term}'"
        }


def parse_search_query(query):
    """Legacy function - now calls generate_search_sql"""
    result = generate_search_sql(query)
    return {"search_term": "Generated by LLM SQL", "sql_result": result}


def generate_bulk_product_tags(products_data):
    """
    Generate tags for multiple products in a single API call.

    Args:
        products_data: List of dicts with 'title', 'category', 'base_price', etc.

    Returns:
        List of tag arrays matching the input order
    """
    try:
        # Prepare products for batch processing
        products_for_llm = []
        for idx, product in enumerate(products_data):
            products_for_llm.append({
                "index": idx,
                "title": product.get('title', ''),
                "category": product.get('category', ''),
                "base_price": product.get('base_price', 0)
            })

        products_json = json.dumps(products_for_llm, ensure_ascii=False, indent=2)

        system_prompt = """You are a product tagging expert for a Bosnian marketplace with DEEP SEARCH INTENT understanding.

Your task: Generate comprehensive search tags for MULTIPLE products at once.

⚠️ CRITICAL REQUIREMENT: YOU MUST GENERATE A MINIMUM OF 10-15 TAGS PER PRODUCT ⚠️

MANDATORY TAG STRUCTURE - EVERY product MUST include ALL of these:

1. **BRAND** (if identifiable):
   - Extract and include brand name (lowercase, no diacritics)
   - Examples: "milka", "nivea", "persil", "ajax", "teta violeta", "head shoulders"
   - If no brand, skip this tag

2. **GENERAL CATEGORY** (REQUIRED):
   - High-level product category (lowercase, no diacritics)
   - Examples: "higijena", "hrana", "pice", "ciscenje", "meso", "mljecni proizvodi"

3. **SPECIFIC PRODUCT TYPE** (REQUIRED):
   - What exactly the product is (lowercase, no diacritics)
   - Examples: "cokolada", "sampon", "deterdent", "toalet papir", "meso", "jogurt"

4. **PRODUCT VARIANTS** (REQUIRED - add 2-3 tags):
   - Alternative names and spellings
   - Generic terms people use to search
   - Examples for toilet paper: "papir", "toaletni papir", "wc papir", "higijenska hartija"

5. **USE CASE TAGS** (REQUIRED - add 3-5 tags):
   - Purpose: "pranje", "ciscenje", "njega", "ishrana"
   - Room/location: "kupatilo", "kuhinja", "tus", "wc"
   - Activity: "pranje vesa", "ciscenje podova", "kuvanje"

6. **SEARCH INTENT TAGS** (REQUIRED - add 3-5 tags):
   - Common search phrases
   - English equivalents for common products
   - Related terms users might search
   - Examples: "toilet paper", "shampoo", "chocolate", "cleaning"

COMPLETE TAG EXAMPLES (YOU MUST MATCH THIS LEVEL OF DETAIL):

"TETA VIOLETA MEGA ROLL" → MUST HAVE 10-15 TAGS:
[
  "teta violeta", "higijena", "toalet papir", "papir", "mega roll", "kupatilo", "wc", "toaletni papir", "toalet", "papir za wc", "meki papir", "higijenska hartija", "toilet paper", "bathroom", "wc papir"
]
COUNT: 15 tags ✓

"Milka čokolada 100g" → MUST HAVE 10-15 TAGS:
[
  "milka", "hrana", "cokolada", "slatkis", "desert", "grickalica", "slatko", "uzina", "chocolate", "candy", "grickanje", "snack", "slatka hrana", "cokolada sa mlekom"
]
COUNT: 14 tags ✓

"Head & Shoulders šampon protiv peruti" → MUST HAVE 10-15 TAGS:
[
  "head shoulders", "higijena", "sampon", "head and shoulders", "kosa", "njega", "pranje kose", "kupatilo", "tus", "perut", "shampoo", "hair", "anti dandruff", "njega kose", "pranje"
]
COUNT: 15 tags ✓

"Persil deterdžent za pranje" → MUST HAVE 10-15 TAGS:
[
  "persil", "ciscenje", "deterdent", "pranje", "higijena", "ves", "pranje vesa", "prasak", "hemija", "detergent", "washing", "laundry", "sredstvo za pranje", "prasak za ves"
]
COUNT: 14 tags ✓

"AJAX sredstvo za čišćenje podova" → MUST HAVE 10-15 TAGS:
[
  "ajax", "ciscenje", "sredstvo za ciscenje", "podovi", "ciscenje podova", "kuhinja", "higijena", "hemija", "dezinfekcija", "floor cleaner", "cleaning", "pod", "ciscenje kuce", "sredstvo"
]
COUNT: 14 tags ✓

"Svježa piletina file 1kg" → MUST HAVE 10-15 TAGS:
[
  "meso", "piletina", "pile", "file", "svjeza", "belo meso", "protein", "chicken", "kuhinja", "glavno jelo", "rucak", "piletina file", "svjeze meso", "pileci file"
]
COUNT: 14 tags ✓

Return ONLY valid JSON with this structure:
{
  "products_tags": [
    {
      "index": 0,
      "tags": ["tag1", "tag2", "tag3", ... at least 10 tags ...]
    },
    {
      "index": 1,
      "tags": ["tag1", "tag2", ... at least 10 tags ...]
    }
  ]
}

CRITICAL RULES - FOLLOW STRICTLY:
✓ MINIMUM 10 tags per product, MAXIMUM 15 tags
✓ First tags: brand (if exists), general_category, product_type
✓ Then add: product variants (2-3), use case tags (3-5), search intent tags (3-5)
✓ All lowercase, no diacritics (čokolada → cokolada, šampon → sampon)
✓ Think: "How would 5 different people search for this product?"
✓ Include English terms for common products (chocolate, shampoo, cleaning, etc.)
✓ Return tags in SAME ORDER as input using index field
✓ NO empty strings or duplicate tags

IF YOU RETURN LESS THAN 10 TAGS FOR ANY PRODUCT, YOU HAVE FAILED THE TASK."""

        user_prompt = f"""Generate tags for these products:

{products_json}

Return tags for ALL products in the same order."""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.5,  # Increased for more creative/comprehensive tagging
            max_tokens=5000  # Increased for more comprehensive tags
        )

        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)
        print("RAW TAGS RESPONSE:", result)

        # Extract tags in correct order
        products_tags_list = result.get('products_tags', [])

        # Sort by index to ensure correct order
        products_tags_list.sort(key=lambda x: x.get('index', 0))

        # Filter and validate tags
        validated_tags = []
        for idx, item in enumerate(products_tags_list):
            tags = [tag for tag in item.get('tags', []) if tag and tag.strip()]

            # Validation: warn if less than 10 tags
            if len(tags) < 10:
                print(f"WARNING: Product at index {idx} only has {len(tags)} tags (minimum 10 required)")
                print(f"  Product: {products_data[idx].get('title', 'Unknown')}")
                print(f"  Tags: {tags}")

            validated_tags.append(tags)

        return validated_tags

    except Exception as e:
        print(f"Error in generate_bulk_product_tags: {e}")
        import traceback
        traceback.print_exc()

        # Fallback: generate basic tags from title and category
        fallback_tags = []
        for product in products_data:
            tags = []
            # Only add non-empty title
            title = product.get('title', '').lower().strip()
            if title:
                tags.append(title)
            # Only add non-empty category
            category = product.get('category', '').lower().strip()
            if category:
                tags.append(category)
            fallback_tags.append(tags)

        return fallback_tags


def check_query_relevance(query):
    """Check if query is relevant to products/discounts - SIMPLIFIED"""
    # Simple keyword-based relevance check to avoid API calls
    query_lower = query.lower()

    # Relevant keywords in Bosnian
    relevant_keywords = [
        # Products
        'proizvod',
        'artikal',
        'roba',
        'stvari',
        'kupiti',
        'kupim',
        'kupit',
        'trebam',
        'tražim',
        # Discounts
        'popust',
        'akcija',
        'snižen',
        'jeftin',
        'povoljn',
        'cijena',
        'cena',
        'košta',
        # Stores/places
        'trgovina',
        'radnja',
        'market',
        'centar',
        'prodavnic',
        'shop',
        'gdje',
        'gdje',
        'di',
        # Food items
        'meso',
        'piletina',
        'govedina',
        'sir',
        'mlijeko',
        'hleb',
        'kruh',
        'jogurt',
        'ulje',
        'jaja',
        'voće',
        'povrće',
        'banane',
        'paradajz',
        'šećer',
        'brašno',
        # Categories
        'hrana',
        'pića',
        'auto',
        'gume',
        'dijelovi',
        'tehnika',
        'telefon',
        'kompjuter'
    ]

    # Check if any relevant keyword is in the query
    for keyword in relevant_keywords:
        if keyword in query_lower:
            return True

    # If no keywords found, it's probably not relevant
    return False


def extract_product_from_image(image_base64: str) -> dict:
    """
    Use GPT-4o Vision to extract product information from a product image.

    Args:
        image_base64: Base64 encoded image data (without data URL prefix)

    Returns:
        dict with title, base_price, discount_price, brand, category, tags, description, etc.
    """
    system_prompt = """You are a product information extractor for a Bosnian grocery/retail marketplace.
Analyze the product image and extract COMPREHENSIVE product information for database storage AND product matching.

Extract the following information:
- title: Full product name in Bosnian (preserve diacritics: ć, č, š, ž, đ)
- brand: Brand name if visible (e.g., "Milka", "Nivea", "Persil", "Meggle")
- base_price: Regular price in KM if visible on price tag
- discount_price: Sale price in KM if visible (null if not on sale)
- weight_volume: Weight or volume as string (e.g., "1L", "500g", "250ml", "1kg")
- category: Product category - MUST be one of:
  ["Meso", "Namirnice", "Voće/Povrće", "Pića", "Mliječni proizvodi", "Higijena", "Čišćenje", "Auto", "Bebe", "Tehnika", "Ostalo"]

PRODUCT MATCHING FIELDS (critical for clone/sibling detection):
- product_type: Normalized generic product type in Bosnian, lowercase. Examples:
  * "mlijeko", "jogurt", "sir", "maslac", "pavlaka" (dairy)
  * "čokolada", "keks", "bomboni", "grickalice" (sweets)
  * "deterdžent", "omekšivač", "sredstvo za čišćenje" (cleaning)
  * "šampon", "gel za tuširanje", "sapun", "pasta za zube" (hygiene)
  * "piletina", "govedina", "svinjetina", "riba" (meat)
  * "sok", "voda", "pivo", "energetsko piće" (drinks)
- size_value: Numeric size value only (e.g., 1, 0.5, 500, 250, 100)
- size_unit: Size unit only - MUST be one of: "kg", "g", "l", "ml", "kom"
- variant: Product variant/differentiator if any (e.g., "3.2%", "bez laktoze", "light", "s lješnicima", "gorka", "original")

SEARCH & SEO FIELDS:
- tags: Array of 10-15 search tags (lowercase, no diacritics) for matching. Include:
  * Brand name, product type, category, use cases, variants, English equivalents
- description: SEO-friendly description (2-3 sentences)

IMPORTANT RULES:
- Prices in Bosnia use KM (Konvertibilna Marka)
- If you see crossed-out price, that's base_price; highlighted price is discount_price
- ALWAYS extract product_type, size_value, size_unit for product matching
- Normalize sizes: 1000ml = 1l, 1000g = 1kg
- Tags must be lowercase without diacritics (čokolada → cokolada)
- Return ONLY valid JSON, no markdown

Return JSON format:
{
    "title": "Milka čokolada s lješnicima 100g",
    "brand": "Milka",
    "base_price": 3.50,
    "discount_price": 2.99,
    "weight_volume": "100g",
    "product_type": "čokolada",
    "size_value": 100,
    "size_unit": "g",
    "variant": "s lješnicima",
    "category": "Namirnice",
    "tags": ["milka", "cokolada", "slatkis", "hrana", "desert", "grickalica", "slatko", "uzina", "chocolate", "ljesnik", "hazelnut", "mljecna cokolada"],
    "description": "Milka čokolada s lješnicima je kremasta mliječna čokolada sa dodatkom hrskave lješnikove krokante. Idealna za užinu, desert ili poklon. Popularan slatkiš za sve generacije.",
    "confidence": "high" | "medium" | "low"
}"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Use gpt-4o for vision tasks
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract product information from this image."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "low"  # Use low detail to save tokens
                            }
                        }
                    ]
                }
            ],
            max_tokens=700
        )

        content = response.choices[0].message.content.strip()

        # Clean up markdown if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)
        return result

    except json.JSONDecodeError as e:
        return {
            "title": "Nepoznat proizvod",
            "brand": None,
            "base_price": None,
            "discount_price": None,
            "weight_volume": None,
            "product_type": None,
            "size_value": None,
            "size_unit": None,
            "variant": None,
            "description": None,
            "confidence": "low",
            "error": f"Failed to parse response: {str(e)}"
        }
    except Exception as e:
        return {
            "title": "Greška",
            "brand": None,
            "base_price": None,
            "discount_price": None,
            "weight_volume": None,
            "description": None,
            "confidence": "low",
            "error": str(e)
        }
