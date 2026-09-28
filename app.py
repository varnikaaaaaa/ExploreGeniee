import streamlit as st
import os
import json
import re
import requests
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

MODEL = "openai/gpt-oss-120b"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ExploreGenie",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SESSION STATE
# ============================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_trip" not in st.session_state:
    st.session_state.last_trip = None

if "last_hotels" not in st.session_state:
    st.session_state.last_hotels = []


# ============================================================
# LOAD DESTINATIONS
# ============================================================

@st.cache_data
def load_destinations():

    paths = [
        BASE_DIR / "data" / "destinations.json",
        BASE_DIR / "destinations.json"
    ]

    for path in paths:

        if path.exists():

            try:

                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)

                if isinstance(data, list):
                    return data

                if isinstance(data, dict):

                    if "destinations" in data:
                        return data["destinations"]

                    return list(data.values())

            except Exception as e:

                st.error(
                    f"Error loading destinations.json: {e}"
                )

                return []

    return []


destinations = load_destinations()


# ============================================================
# GROQ AI
# ============================================================

def generate_groq_response(
    prompt,
    system_prompt="You are ExploreGenie, a helpful AI tourism assistant."
):

    if not client:

        return (
            "⚠️ GROQ_API_KEY is missing.\n\n"
            "Please add your Groq API key to your .env file."
        )

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.7,

            max_completion_tokens=3000
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"⚠️ Groq API error: {e}"


# ============================================================
# WIKIMEDIA IMAGE SEARCH
# ============================================================

@st.cache_data(show_spinner=False)
def get_wikimedia_image(search_term):

    try:

        url = "https://commons.wikimedia.org/w/api.php"

        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": search_term,
            "gsrnamespace": 6,
            "gsrlimit": 1,
            "prop": "imageinfo",
            "iiprop": "url",
            "iiurlwidth": 900,
            "format": "json"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={
                "User-Agent": "ExploreGenie/1.0"
            }
        )

        response.raise_for_status()

        data = response.json()

        pages = (
            data
            .get("query", {})
            .get("pages", {})
        )

        for page in pages.values():

            image_info = page.get(
                "imageinfo",
                []
            )

            if image_info:

                return (
                    image_info[0].get("thumburl")
                    or image_info[0].get("url")
                )

    except Exception:
        return None

    return None


# ============================================================
# DESTINATION HELPERS
# ============================================================

def get_destination(name):

    for destination in destinations:

        if destination.get(
            "name",
            ""
        ).lower() == name.lower():

            return destination

    return None


def get_place_name(place):

    if isinstance(place, str):
        return place

    if isinstance(place, dict):

        return (
            place.get("name")
            or place.get("title")
            or place.get("place")
            or "Tourist Place"
        )

    return str(place)


def get_restaurant_name(restaurant):

    if isinstance(restaurant, str):
        return restaurant

    if isinstance(restaurant, dict):

        return (
            restaurant.get("name")
            or restaurant.get("restaurant")
            or restaurant.get("title")
            or "Restaurant"
        )

    return str(restaurant)


# ============================================================
# AI HOTEL SUGGESTIONS
# ============================================================

def get_ai_hotels(destination, budget):

    if not client:
        return []

    prompt = f"""
You are helping a tourism application.

Destination: {destination}
Budget: {budget}

Suggest 4 real, well-known hotels in {destination}.

Return ONLY valid JSON using this exact structure:

[
  {{
    "name": "Hotel name",
    "reason": "Short reason"
  }}
]

Do not include prices.
Do not include ratings.
Do not include booking links.
Do not invent hotels.
"""

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "Return only valid JSON. "
                        "You are a tourism recommendation assistant."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.2,

            max_completion_tokens=1000
        )

        raw = response.choices[0].message.content.strip()

        # Remove markdown code fences if present
        raw = re.sub(
            r"```json",
            "",
            raw,
            flags=re.IGNORECASE
        )

        raw = raw.replace(
            "```",
            ""
        ).strip()

        data = json.loads(raw)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            if isinstance(data.get("hotels"), list):
                return data["hotels"]

            for value in data.values():

                if isinstance(value, list):
                    return value

    except Exception:
        return []

    return []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🌍 ExploreGenie")

    st.caption(
        "AI-Powered Smart Tourism Assistant"
    )

    st.divider()

    page = st.radio(
        "Navigate",
        [
            "🏠 Home",
            "✈️ AI Trip Planner",
            "💬 Travel Assistant",
            "🗺️ Explore Destinations"
        ]
    )

    st.divider()

    st.subheader("✨ Powered by")

    st.write("🤖 Groq AI")
    st.write("🐍 Python")
    st.write("🎨 Streamlit")
    st.write("📸 Wikimedia Commons")


# ============================================================
# HOME
# ============================================================

if page == "🏠 Home":

    st.title("🌍 ExploreGenie")

    st.subheader(
        "Your AI-powered smart tourism assistant"
    )

    st.write(
        """
        Plan personalized trips, discover destinations,
        find places to visit, explore food and restaurants,
        and get AI-powered travel suggestions.
        """
    )

    st.divider()

    st.header("✨ What can ExploreGenie do?")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.subheader("✈️ AI Trip Planner")

        st.write(
            """
            Generate personalized day-by-day
            itineraries based on your destination,
            budget, interests and travel style.
            """
        )

    with col2:

        st.subheader("🗺️ Destination Explorer")

        st.write(
            """
            Explore tourist attractions,
            restaurants, food recommendations
            and destination information.
            """
        )

    with col3:

        st.subheader("🤖 AI Travel Assistant")

        st.write(
            """
            Ask travel questions and receive
            personalized AI-generated answers
            using natural language.
            """
        )

    st.divider()

    st.header("🌎 Popular Destinations")

    if destinations:

        cols = st.columns(4)

        for index, destination in enumerate(
            destinations[:8]
        ):

            with cols[index % 4]:

                name = destination.get(
                    "name",
                    "Destination"
                )

                image = get_wikimedia_image(
                    destination.get(
                        "cover_wiki",
                        name
                    )
                )

                if image:

                    st.image(
                        image,
                        use_container_width=True
                    )

                st.subheader(name)

                st.caption(
                    destination.get(
                        "tagline",
                        "Explore this destination"
                    )
                )

    else:

        st.warning(
            "No destinations found. "
            "Please check destinations.json."
        )


# ============================================================
# AI TRIP PLANNER
# ============================================================

elif page == "✈️ AI Trip Planner":

    st.title("✈️ AI Trip Planner")

    st.write(
        "Tell ExploreGenie what kind of trip you want "
        "and AI will create your itinerary."
    )

    if not destinations:

        st.error(
            "No destinations found."
        )

    else:

        destination_names = [
            d.get("name")
            for d in destinations
            if d.get("name")
        ]

        col1, col2 = st.columns(2)

        with col1:

            destination = st.selectbox(
                "📍 Choose destination",
                destination_names
            )

            days = st.slider(
                "📅 Number of days",
                min_value=1,
                max_value=15,
                value=3
            )

            budget = st.selectbox(
                "💰 Budget",
                [
                    "Budget",
                    "Moderate",
                    "Luxury"
                ]
            )

        with col2:

            interests = st.multiselect(
                "❤️ Your interests",
                [
                    "History",
                    "Nature",
                    "Adventure",
                    "Food",
                    "Shopping",
                    "Culture",
                    "Photography",
                    "Nightlife",
                    "Beaches",
                    "Spirituality"
                ]
            )

            travel_style = st.selectbox(
                "🎒 Travel style",
                [
                    "Relaxed",
                    "Balanced",
                    "Adventure-packed",
                    "Family-friendly",
                    "Romantic",
                    "Solo"
                ]
            )

        preferences = st.text_area(
            "📝 Additional preferences",
            placeholder=(
                "Example: I love local food and photography. "
                "Avoid very crowded places."
            )
        )

        generate_button = st.button(
            "✨ Generate My AI Trip",
            type="primary",
            use_container_width=True
        )

        if generate_button:

            if interests:

                interests_text = ", ".join(
                    interests
                )

            else:

                interests_text = (
                    "General sightseeing and local experiences"
                )

            prompt = f"""
Create a personalized travel itinerary.

Destination:
{destination}

Trip duration:
{days} days

Budget:
{budget}

Interests:
{interests_text}

Travel style:
{travel_style}

Additional preferences:
{preferences if preferences else "None"}

Include:

1. Trip overview
2. Day-by-day itinerary
3. Tourist attractions
4. Food experiences
5. Restaurant suggestions
6. Approximate budget categories
7. Travel tips
8. Packing suggestions

Use clear headings and bullet points.

Do not invent exact hotel prices,
ticket prices, opening hours or live availability.
"""

            with st.spinner(
                "🤖 ExploreGenie is planning your trip..."
            ):

                result = generate_groq_response(
                    prompt,
                    """
                    You are ExploreGenie,
                    an expert AI tourism planner.

                    Create useful, realistic,
                    practical and personalized
                    travel itineraries.
                    """
                )

            st.session_state.last_trip = {
                "destination": destination,
                "budget": budget,
                "days": days,
                "result": result
            }

            with st.spinner(
                "🏨 Finding hotel suggestions..."
            ):

                st.session_state.last_hotels = (
                    get_ai_hotels(
                        destination,
                        budget
                    )
                )

        # ----------------------------------------------------
        # SHOW TRIP
        # ----------------------------------------------------

        if st.session_state.last_trip:

            trip = st.session_state.last_trip

            st.divider()

            st.header(
                f"✈️ Your {trip['days']}-Day Trip "
                f"to {trip['destination']}"
            )

            st.caption(
                f"Budget: {trip['budget']}"
            )

            st.markdown(
                trip["result"]
            )

            st.divider()

            selected_destination = get_destination(
                trip["destination"]
            )

            if selected_destination:

                # ==================================================
                # PLACES
                # ==================================================

                st.header("📍 Places to Visit")

                places = selected_destination.get(
                    "places",
                    []
                )

                place_cols = st.columns(3)

                for index, place in enumerate(
                    places[:6]
                ):

                    place_name = get_place_name(
                        place
                    )

                    with place_cols[index % 3]:

                        image_url = (
                            get_wikimedia_image(
                                f"{place_name} "
                                f"{trip['destination']}"
                            )
                        )

                        if image_url:

                            st.image(
                                image_url,
                                use_container_width=True
                            )

                        st.subheader(
                            f"📍 {place_name}"
                        )

                # ==================================================
                # FOOD
                # ==================================================

                st.header("🍛 Food & Restaurants")

                restaurants = (
                    selected_destination.get(
                        "restaurants",
                        []
                    )
                )

                restaurant_cols = st.columns(3)

                for index, restaurant in enumerate(
                    restaurants[:6]
                ):

                    restaurant_name = (
                        get_restaurant_name(
                            restaurant
                        )
                    )

                    with restaurant_cols[
                        index % 3
                    ]:

                        image_url = (
                            get_wikimedia_image(
                                f"{restaurant_name} "
                                f"{trip['destination']}"
                            )
                        )

                        if image_url:

                            st.image(
                                image_url,
                                use_container_width=True
                            )

                        st.subheader(
                            f"🍛 {restaurant_name}"
                        )

                # ==================================================
                # HOTELS
                # ==================================================

                st.header("🏨 Suggested Hotels")

                st.caption(
                    "AI-generated suggestions. "
                    "Verify current prices and availability "
                    "before booking."
                )

                hotels = (
                    st.session_state.last_hotels
                )

                if hotels:

                    hotel_cols = st.columns(2)

                    for index, hotel in enumerate(
                        hotels[:4]
                    ):

                        if not isinstance(
                            hotel,
                            dict
                        ):
                            continue

                        hotel_name = hotel.get(
                            "name",
                            "Hotel"
                        )

                        reason = hotel.get(
                            "reason",
                            ""
                        )

                        with hotel_cols[
                            index % 2
                        ]:

                            image_url = (
                                get_wikimedia_image(
                                    f"{hotel_name} "
                                    f"{trip['destination']}"
                                )
                            )

                            if image_url:

                                st.image(
                                    image_url,
                                    use_container_width=True
                                )

                            st.subheader(
                                f"🏨 {hotel_name}"
                            )

                            st.write(reason)

                else:

                    st.info(
                        "Hotel suggestions could not "
                        "be generated right now."
                    )


# ============================================================
# TRAVEL ASSISTANT
# ============================================================

elif page == "💬 Travel Assistant":

    st.title("💬 AI Travel Assistant")

    st.write(
        "Ask ExploreGenie anything about your travel plans."
    )

    for message in st.session_state.chat_history:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    user_question = st.chat_input(
        "Ask something like: What should I eat in Hyderabad?"
    )

    if user_question:

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": user_question
            }
        )

        with st.chat_message("user"):

            st.markdown(
                user_question
            )

        context = ""

        if st.session_state.last_trip:

            context = f"""
The user recently planned a trip to
{st.session_state.last_trip['destination']}
for {st.session_state.last_trip['days']} days.

Budget:
{st.session_state.last_trip['budget']}
"""

        prompt = f"""
{context}

User question:
{user_question}

Answer as a friendly AI tourism assistant.

Give practical and clear information.

If something depends on current prices,
availability or opening hours, tell the user
to verify the latest information.
"""

        with st.chat_message("assistant"):

            with st.spinner(
                "🤖 Thinking..."
            ):

                answer = generate_groq_response(
                    prompt,
                    """
                    You are ExploreGenie,
                    a friendly AI travel assistant.

                    Give concise but useful
                    tourism advice.
                    """
                )

            st.markdown(
                answer
            )

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

    st.divider()

    if st.button(
        "🗑️ Clear Chat"
    ):

        st.session_state.chat_history = []

        st.rerun()


# ============================================================
# EXPLORE DESTINATIONS
# ============================================================

elif page == "🗺️ Explore Destinations":

    st.title("🗺️ Explore Destinations")

    st.write(
        "Browse destinations and discover places, "
        "food and travel information."
    )

    if destinations:

        destination_names = [
            d.get("name")
            for d in destinations
            if d.get("name")
        ]

        selected_name = st.selectbox(
            "🔎 Select a destination",
            destination_names
        )

        selected = get_destination(
            selected_name
        )

        if selected:

            st.divider()

            # ==================================================
            # COVER
            # ==================================================

            cover_term = selected.get(
                "cover_wiki",
                selected_name
            )

            cover_image = get_wikimedia_image(
                cover_term
            )

            if cover_image:

                st.image(
                    cover_image,
                    use_container_width=True
                )

            st.header(
                f"🌍 {selected_name}"
            )

            st.write(
                selected.get(
                    "description",
                    ""
                )
            )

            # ==================================================
            # QUICK INFO
            # ==================================================

            col1, col2, col3, col4 = st.columns(4)

            with col1:

                st.metric(
                    "Best Time",
                    selected.get(
                        "best_time",
                        "Varies"
                    )
                )

            with col2:

                st.metric(
                    "Budget",
                    selected.get(
                        "budget_level",
                        "Varies"
                    )
                )

            with col3:

                st.metric(
                    "Ideal Days",
                    selected.get(
                        "ideal_days",
                        "Varies"
                    )
                )

            with col4:

                st.metric(
                    "Country",
                    selected.get(
                        "country",
                        ""
                    )
                )

            # ==================================================
            # PLACES
            # ==================================================

            st.header("📍 Tourist Places")

            places = selected.get(
                "places",
                []
            )

            cols = st.columns(3)

            for index, place in enumerate(
                places
            ):

                place_name = get_place_name(
                    place
                )

                with cols[index % 3]:

                    image_url = (
                        get_wikimedia_image(
                            f"{place_name} "
                            f"{selected_name}"
                        )
                    )

                    if image_url:

                        st.image(
                            image_url,
                            use_container_width=True
                        )

                    st.subheader(
                        f"📍 {place_name}"
                    )

            # ==================================================
            # RESTAURANTS
            # ==================================================

            st.header("🍛 Restaurants & Food")

            restaurants = selected.get(
                "restaurants",
                []
            )

            cols = st.columns(3)

            for index, restaurant in enumerate(
                restaurants
            ):

                restaurant_name = (
                    get_restaurant_name(
                        restaurant
                    )
                )

                with cols[index % 3]:

                    image_url = (
                        get_wikimedia_image(
                            f"{restaurant_name} "
                            f"{selected_name}"
                        )
                    )

                    if image_url:

                        st.image(
                            image_url,
                            use_container_width=True
                        )

                    st.subheader(
                        f"🍛 {restaurant_name}"
                    )

            # ==================================================
            # AI GUIDE
            # ==================================================

            st.header(
                "🤖 Ask AI About This Destination"
            )

            question = st.text_input(
                f"Ask something about {selected_name}",
                placeholder=(
                    "Example: Plan a 2-day food "
                    "and culture trip"
                )
            )

            if st.button(
                "✨ Generate AI Guide"
            ):

                if not question.strip():

                    st.warning(
                        "Please enter a question first."
                    )

                else:

                    prompt = f"""
Destination:
{selected_name}

Destination information:
{json.dumps(
    selected,
    indent=2,
    ensure_ascii=False
)}

User request:
{question}

Create a useful personalized tourism guide.
"""

                    with st.spinner(
                        "🤖 Generating your guide..."
                    ):

                        guide = generate_groq_response(
                            prompt
                        )

                    st.markdown(
                        guide
                    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🌍 ExploreGenie — AI-Powered Smart Tourism Assistant"
)

st.caption(
    "Built with Python + Streamlit + Groq"
)
