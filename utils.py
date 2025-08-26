import os
import re
import json
import time
import hashlib
from typing import List, Dict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

_SALT = os.environ.get("TALENTSCOUT_SALT", "default_salt_change_me")

def validate_email(value: str) -> bool:
    pattern = r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, value.strip()) is not None

def validate_phone(value: str) -> bool:
    # Allows digits, spaces, +, -, parentheses; requires at least 7 digits
    digits = re.sub(r"\D", "", value)
    return len(digits) >= 7

def hash_identifier(value: str) -> str:
    h = hashlib.sha256((_SALT + value.strip()).encode("utf-8")).hexdigest()
    return h

def generate_questions_offline(tech_stack: str) -> List[str]:
    """
    Deterministic fallback in case LLM API is unavailable.
    Maps common tech to representative questions. If unknown, returns generic prompts.
    """
    techs = [t.strip().lower() for t in tech_stack.split(",") if t.strip()]
    bank = {
        "python": [
            "Explain list vs tuple and when you'd use each in Python.",
            "How do generators differ from list comprehensions? Provide a use case.",
            "What is GIL and how does it affect multithreading?",
            "Write a Python snippet to merge two dictionaries.",
        ],
        "django": [
            "How do middleware and signals differ in Django? Provide an example use case.",
            "Explain Django ORM select_related vs prefetch_related with an example.",
            "How do you secure a Django REST API (auth, throttling, permissions)?",
        ],
        "javascript": [
            "Explain event loop and microtask queue in JavaScript.",
            "When would you use closures? Provide a practical example.",
            "What is debouncing vs throttling and when to use each?",
        ],
        "react": [
            "How do React hooks replace class lifecycle methods? Map useEffect/useMemo examples.",
            "Explain reconciliation and keys in lists; why do incorrect keys cause bugs?",
            "How would you implement infinite scroll efficiently in React?",
        ],
        "node": [
            "What are streams in Node.js and how do they improve performance?",
            "Explain cluster module and when you'd use it.",
            "How do you handle backpressure when reading/writing large files?",
        ],
        "sql": [
            "How do you detect and resolve N+1 query problems?",
            "Explain indexing strategy for a table with frequent writes and analytical reads.",
            "What is a window function? Give an example query.",
        ],
        "mongodb": [
            "How do you model many-to-many relationships in MongoDB?",
            "Explain aggregation pipeline stages for grouping and filtering efficiently.",
            "How do you design indexes for compound queries in MongoDB?",
        ],
        "aws": [
            "Design a fault-tolerant web app using ALB, ASG, and RDS—explain trade-offs.",
            "When do you pick SQS vs SNS? Provide a scenario.",
            "How do you secure secrets on AWS without hardcoding them?",
        ],
        "docker": [
            "Explain multi-stage builds and why they matter for image size/security.",
            "How do you persist data in containers and avoid permission issues?",
            "What is the difference between ENTRYPOINT and CMD?",
        ],
        "kubernetes": [
            "Explain Deployments vs StatefulSets; when to pick each?",
            "How would you implement blue/green or canary deployments on Kubernetes?",
            "What are liveness vs readiness probes and common pitfalls?",
        ],
        "tensorflow": [
            "How do you prevent overfitting in a CNN trained on limited data?",
            "Explain tf.data pipelines and how to optimize input performance.",
            "When would you use tf.function and autograph?",
        ],
        "pytorch": [
            "What is the role of autograd? Show how to freeze layers during fine-tuning.",
            "Contrast DataLoader num_workers, pin_memory and their impact.",
            "How do you implement gradient clipping and why?",
        ],
    }

    chosen: List[str] = []
    for t in techs:
        for key, qs in bank.items():
            if key in t and len(chosen) < 5:
                chosen.extend(qs[:2])  # pick top 2 per matched tech
    if not chosen:
        chosen = [
            "Describe a challenging bug you fixed recently and how you diagnosed it.",
            "Explain how you design for scalability and observability in your services.",
            "Walk through your process for profiling and optimizing a slow endpoint.",
        ]
    # Deduplicate and cap at 5
    uniq = []
    for q in chosen:
        if q not in uniq:
            uniq.append(q)
    return uniq[:5]

def save_candidate_record(candidate: Dict, questions: List[str]) -> None:
    # Store only hashed identifiers; never store plain email/phone
    record = {
        "id_email": hash_identifier(candidate.get("email", "")) if candidate.get("email") else None,
        "id_phone": hash_identifier(candidate.get("phone", "")) if candidate.get("phone") else None,
        "full_name": candidate.get("full_name"),
        "experience_years": candidate.get("experience_years"),
        "desired_positions": candidate.get("desired_positions"),
        "location": candidate.get("location"),
        "tech_stack": candidate.get("tech_stack"),
        "questions": questions,
        "ts": int(time.time()),
        "privacy": "Identifiers salted-hash only; no plaintext PII persisted.",
    }
    path = os.path.join(DATA_DIR, "records.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
