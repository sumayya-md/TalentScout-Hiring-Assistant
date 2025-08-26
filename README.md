🤖 TalentScout — Hiring Assistant Chatbot (Streamlit)
An intelligent screening assistant for tech roles. It collects candidate details and generates tailored technical questions from the candidate’s declared tech stack using an LLM (OpenAI by default). Falls back to a deterministic offline generator if no API key is set.

✨ Features
Friendly greeting + clear purpose

Step-by-step information gathering (name, email, phone, years of experience, desired role, location, tech stack)

3–5 tailored technical questions based on the declared stack

Context-aware flow with validation and a fallback mechanism

Conversation exit keywords: end, exit, quit, bye

Privacy-first storage: only salted hashes of email/phone are saved for deduping; no plaintext PII persisted

Export JSON record of the conversation (candidate + questions)

Clean Streamlit UI with session management

🚀 Installation & Setup
bash
Copy
Edit
# Clone the repository
git clone https://github.com/yourusername/talentscout-chatbot.git
cd talentscout-chatbot

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
🔑 Note:

To use LLM-powered question generation, set your OPENAI_API_KEY as an environment variable.

Without a key, the chatbot will fall back to built-in static questions.

🖥️ Usage Guide
Open the app in your browser after running streamlit run app.py.

The chatbot will greet you and explain its purpose.

Provide details step by step:

Full Name

Email Address

Phone Number

Years of Experience

Desired Position(s)

Current Location

Tech Stack (languages, frameworks, tools)

Receive tailored technical questions based on your stack.

Type end / exit / bye to gracefully conclude the conversation.

⚙️ Tech Stack
Python

Streamlit (UI)

OpenAI API / fallback logic (LLM-powered question generation)

JSON storage for conversation export

🧑‍💻 Prompt Design
Information Gathering Prompt → Collects candidate info in a structured way.

Tech Stack Prompt → Maps declared skills to specific question templates.

Contextual Follow-ups → Ensures smooth flow of the interview.

Fallback Handling → Returns helpful clarifications if input is unclear.

🏆 Challenges & Solutions
Context Handling → Solved using Streamlit st.session_state to persist data.

Data Privacy → Instead of saving raw PII, only hashed identifiers are stored.

No API Key Case → Implemented offline static generator for robustness.

📹 Demo
Loom/Video link here (if recorded)

Or include screenshots in /demo/ folder

📂 Repository Structure
bash
Copy
Edit
├── app.py                 # Main Streamlit app
├── prompts.py             # Prompt templates
├── utils.py               # Helper functions (hashing, fallback Qs)
├── requirements.txt       # Dependencies
├── README.md              # Project documentation
└── demo/                  # Screenshots or video link (optional)
📜 License
For educational/demo purposes only.