import os
import re
import json
import time
import streamlit as st

from prompts import SYSTEM_PROMPT, QUESTION_GEN_PROMPT
from utils import (
    validate_email,
    validate_phone,
    save_candidate_record,
    hash_identifier,
    generate_questions_offline,
)

# ---------- App Config ----------
st.set_page_config(page_title="TalentScout Hiring Assistant", page_icon="🤖", layout="centered")

# ---------- Helpers ----------
END_KEYWORDS = {"end", "exit", "quit", "bye", "goodbye", "thanks", "thank you"}

FIELDS = [
    ("full_name", "Please share your Full Name."),
    ("email", "What's your Email Address?"),
    ("phone", "Your Phone Number (with country code if outside India)."),
    ("experience_years", "How many Years of Experience do you have? (e.g., 2, 3.5)"),
    ("desired_positions", "What role(s) are you applying for? (e.g., 'Data Scientist', 'ML Engineer')"),
    ("location", "Your Current Location (City, Country)."),
    ("tech_stack", "List your Tech Stack: programming languages, frameworks, databases, tools (comma-separated)."),
]

def get_next_field(info: dict):
    for key, prompt in FIELDS:
        if not info.get(key):
            return key, prompt
    return None, None

def render_message(role, content):
    with st.chat_message(role):
        st.markdown(content)

# ---------- LLM Client (OpenAI style; gracefully handles missing key) ----------
def llm_chat_completion(messages, model=None, temperature=0.2, max_tokens=600):
    """
    Tries OpenAI SDK v1.x style first. If OPENAI_API_KEY not set, returns None.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None  # No API available; caller should use offline fallback
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:
        # If anything fails, use offline fallback by returning None
        return None

# ---------- Session State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "candidate" not in st.session_state:
    st.session_state.candidate = {}
if "state" not in st.session_state:
    st.session_state.state = "greeting"  # greeting -> collecting -> questioning -> ended
if "questions" not in st.session_state:
    st.session_state.questions = []

# ---------- Sidebar ----------
with st.sidebar:
    st.title("⚙️ Settings")
    st.info("This app uses an LLM if OPENAI_API_KEY is set. Without it, a rules-based offline generator is used for questions.")
    st.write("**Environment**")
    st.code("export OPENAI_API_KEY=sk-...\nexport OPENAI_MODEL=gpt-4o-mini", language="bash")
    st.write("**Conversation Controls**")
    if st.button("🔄 Reset Session"):
        st.session_state.clear()
        st.rerun()
    st.divider()
    st.write("**Collected Data (live)**")
    st.json(st.session_state.candidate)

st.title("🤖 TalentScout Hiring Assistant")
st.caption("Hi! I collect your basic details and generate tailored technical questions based on your tech stack.")

# ---------- Initial Greeting ----------
if st.session_state.state == "greeting" and not st.session_state.messages:
    greeting = (
        "Hello! I’m **TalentScout**, your hiring assistant. "
        "I’ll collect a few details and then ask technical questions based on your tech stack. "
        "You can type **end/exit/quit** anytime to finish."
    )
    st.session_state.messages.append({"role": "assistant", "content": greeting})

# ---------- Chat Display ----------
for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"])

# ---------- Input ----------
user_input = st.chat_input("Type here...")
if user_input:
    # End intent?
    if user_input.strip().lower() in END_KEYWORDS:
        st.session_state.state = "ended"
        st.session_state.messages.append({"role": "user", "content": user_input})
        render_message("user", user_input)
        closing = (
            "Thank you for your time! 🎉 We’ve recorded your info. "
            "Our team will review and get back to you with the next steps."
        )
        st.session_state.messages.append({"role": "assistant", "content": closing})
        render_message("assistant", closing)
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        render_message("user", user_input)

        # Flow control
        if st.session_state.state in ("greeting", "collecting"):
            st.session_state.state = "collecting"
            key, prompt = get_next_field(st.session_state.candidate)
            if key is None:
                # All info collected; proceed to questions
                st.session_state.state = "questioning"
            else:
                # Try to map the latest user_input to the expected field
                value = user_input.strip()

                # Validation for email / phone / years
                if key == "email":
                    if not validate_email(value):
                        reply = "That email doesn't look valid. Please provide a valid email (e.g., name@example.com)."
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        render_message("assistant", reply)
                    else:
                        st.session_state.candidate["email"] = value
                        # Ask next field
                        _, next_prompt = get_next_field(st.session_state.candidate)
                        reply = next_prompt or "Thanks!"
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        render_message("assistant", reply)
                elif key == "phone":
                    if not validate_phone(value):
                        reply = "Please enter a valid phone number (digits, spaces, +, -, parentheses allowed)."
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        render_message("assistant", reply)
                    else:
                        st.session_state.candidate["phone"] = value
                        _, next_prompt = get_next_field(st.session_state.candidate)
                        reply = next_prompt or "Thanks!"
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        render_message("assistant", reply)
                elif key == "experience_years":
                    # Accept numeric-like input
                    num = re.findall(r"[0-9]+\.?[0-9]*", value)
                    if not num:
                        reply = "Please enter your experience in years (e.g., 2 or 3.5)."
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        render_message("assistant", reply)
                    else:
                        st.session_state.candidate["experience_years"] = float(num[0])
                        _, next_prompt = get_next_field(st.session_state.candidate)
                        reply = next_prompt or "Thanks!"
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        render_message("assistant", reply)
                else:
                    # General assignment
                    st.session_state.candidate[key] = value
                    _, next_prompt = get_next_field(st.session_state.candidate)
                    reply = next_prompt or "Thanks!"
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    render_message("assistant", reply)

            # If after handling we completed collection, move to questioning
            if st.session_state.state == "collecting":
                k, _ = get_next_field(st.session_state.candidate)
                if k is None:
                    st.session_state.state = "questioning"

        if st.session_state.state == "questioning":
            # Generate questions based on tech_stack
            tech_stack = st.session_state.candidate.get("tech_stack", "")
            if not tech_stack:
                # If somehow missing, ask again
                ask = "Could you please provide your tech stack (languages, frameworks, databases, tools)?"
                st.session_state.messages.append({"role": "assistant", "content": ask})
                render_message("assistant", ask)
            else:
                # Try LLM first
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": QUESTION_GEN_PROMPT.format(tech_stack=tech_stack)},
                ]
                llm_out = llm_chat_completion(messages)
                if llm_out is None:
                    # Offline deterministic fallback
                    questions = generate_questions_offline(tech_stack)
                    st.session_state.questions = questions
                    reply = "**Here are your tailored technical questions (offline mode):**\n\n" + "\n".join(
                        [f"{i+1}. {q}" for i, q in enumerate(questions)]
                    )
                else:
                    st.session_state.questions = [q.strip("- ").strip() for q in llm_out.split("\n") if q.strip()]
                    reply = "**Here are your tailored technical questions:**\n\n" + "\n".join(
                        [f"{i+1}. {q}" for i, q in enumerate(st.session_state.questions)]
                    )

                st.session_state.messages.append({"role": "assistant", "content": reply})
                render_message("assistant", reply)

                # Save anonymized record
                try:
                    save_candidate_record(st.session_state.candidate, st.session_state.questions)
                except Exception:
                    pass

                # Close out
                st.session_state.state = "ended"
                closing = (
                    "Thanks for completing the screening! We’ll review your responses and reach out with next steps. "
                    "If you wish to end now, type **end** or **exit**."
                )
                st.session_state.messages.append({"role": "assistant", "content": closing})
                render_message("assistant", closing)

# ---------- Download Section ----------
st.divider()
st.subheader("⬇️ Export")
if st.session_state.candidate:
    bundle = {
        "candidate": st.session_state.candidate,
        "questions": st.session_state.questions,
        "timestamp": int(time.time()),
    }
    st.download_button(
        label="Download my record (JSON)",
        data=json.dumps(bundle, indent=2),
        file_name="talentscout_record.json",
        mime="application/json",
    )

st.caption("🔒 Privacy: Emails and phone numbers are never stored in plain text—only salted hashes are saved to disk for deduplication.")
