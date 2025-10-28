from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Protocol
import re
from models import CandidateProfile, RecommendationReport

from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    EndSessionContent,
    chat_protocol_spec,
)

# 🔗 Replace this with the actual Job Discovery agent address
JOB_DISCOVERY_ADDRESS = "agent1qd8vlyl2wte96ktqxl4uvhqac3m5uq2ag999qe0fhvr5qzywv0k9720yjmz"

# For Agentverse Hosted Agent
agent = Agent()

# Storage for conversation state
user_sessions = {}

# ---------------------- Utility functions ----------------------

def extract_skills_from_text(text: str) -> list:
    """Extract technical skills from text"""
    skill_keywords = [
        "python", "java", "javascript", "react", "node.js", "nodejs", "angular", "vue.js", "vue",
        "django", "flask", "fastapi", "spring", "express", "typescript",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
        "machine learning", "deep learning", "data science", "ai", "ml",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "ci/cd", "jenkins", "github actions", "gitlab", "agile", "scrum",
        "html", "css", "tailwind", "bootstrap", "sass", "git", "rest api", "restful",
        "graphql", "microservices", "linux", "devops", "springboot", "kafka",
        "rabbitmq", "nginx", "apache", "bash", "shell", "powershell",
        "c++", "c#", "go", "golang", "rust", "php", "ruby", "rails",
        "frontend", "backend", "fullstack", "full-stack", "cloud"
    ]
    
    text_lower = text.lower()
    found_skills = []
    
    # Direct skill matching
    for skill in skill_keywords:
        if skill in text_lower:
            found_skills.append(skill)
    
    # Extract quoted skills
    import re
    quoted = re.findall(r'["\']([^"\']+)["\']', text)
    for item in quoted:
        item_lower = item.lower().strip()
        if item_lower and len(item_lower) > 2:
            found_skills.append(item_lower)
    
    return list(set(found_skills))

def extract_experience_years(text: str) -> int:
    """Extract years of experience from text"""
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of)?\s*(?:experience)?',
        r'experience[:\s]+(\d+)\+?\s*years?',
        r'(\d+)\s*yrs?\.?\s*(?:experience)?',
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    return 3  # Default experience

def is_resume_text(text: str) -> bool:
    """Detect if text is a resume"""
    resume_indicators = [
        'experience', 'education', 'skills', 'work history',
        'employment', 'university', 'bachelor', 'master',
        'degree', 'graduated', 'certification', 'project',
        'responsibilities', 'achievements'
    ]
    text_lower = text.lower()
    matches = sum(1 for indicator in resume_indicators if indicator in text_lower)
    return matches >= 2 or len(text) > 200

def create_profile_from_input(text: str, sender: str) -> CandidateProfile:
    """Create candidate profile from any input"""
    skills = extract_skills_from_text(text)
    experience_years = extract_experience_years(text)
    
    # If no skills found but text mentions looking for jobs, use general search
    if not skills:
        skills = ["software developer", "programming"]
    
    profile = CandidateProfile(
        candidate_id=sender,
        resume_text=text[:3000],
        skills=skills,
        experience_years=experience_years,
        preferences={
            "remote": "remote" in text.lower() or "wfh" in text.lower(),
            "salary_min": 80000,
            "location_preference": "flexible"
        }
    )
    return profile

# ---------------------- Chat Protocol ----------------------
chat_proto = Protocol(spec=chat_protocol_spec)

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages"""
    ctx.logger.info(f"📨 Message from {sender}")
    
    # Always acknowledge first
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(),
            acknowledged_msg_id=msg.msg_id
        ),
    )
    
    # Collect text content
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
    
    text = text.strip()
    ctx.logger.info(f"📝 Text received ({len(text)} chars): {text[:100]}...")
    
    # Handle empty or very short messages
    if len(text) < 10:
        await ctx.send(
            sender,
            ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[
                    TextContent(
                        type="text",
                        text="👋 Hi! I help match candidates with jobs.\n\n"
                             "You can:\n"
                             "• List your skills (e.g., 'python, react, docker')\n"
                             "• Paste your full resume\n"
                             "• Tell me about your experience\n\n"
                             "What would you like to do?"
                    ),
                    EndSessionContent(type="end-session"),
                ]
            )
        )
        return
    
    # Process the input
    try:
        ctx.logger.info(f"🧠 Processing profile for {sender}...")
        profile = create_profile_from_input(text, sender)
        
        # Store session
        user_sessions[sender] = {
            'profile': profile,
            'timestamp': datetime.now()
        }
        
        ctx.logger.info(f"✅ Profile created - Skills: {profile.skills}, Experience: {profile.experience_years}y")
        
        # Send to Job Discovery Agent
        await ctx.send(JOB_DISCOVERY_ADDRESS, profile)
        
        # Determine response based on input type
        if is_resume_text(text):
            response_text = (
                f"✅ Resume processed successfully!\n\n"
                f"📊 Profile Summary:\n"
                f"• Skills detected: {', '.join(profile.skills[:5])}"
                f"{' and more' if len(profile.skills) > 5 else ''}\n"
                f"• Experience: {profile.experience_years} years\n"
                f"• Remote preference: {'Yes' if profile.preferences.get('remote') else 'No'}\n\n"
                f"🔍 Searching for matching jobs... You'll receive recommendations shortly!"
            )
        else:
            response_text = (
                f"✅ Got it! Looking for jobs matching your skills:\n\n"
                f"🎯 Skills: {', '.join(profile.skills)}\n"
                f"💼 Experience: {profile.experience_years} years\n\n"
                f"🔍 Searching job boards... I'll send you the best matches!"
            )
        
        await ctx.send(
            sender,
            ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[
                    TextContent(type="text", text=response_text),
                    EndSessionContent(type="end-session"),
                ]
            )
        )
        
    except Exception as e:
        ctx.logger.error(f"❌ Error: {e}")
        await ctx.send(
            sender,
            ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[
                    TextContent(
                        type="text",
                        text="❌ Sorry, something went wrong. Please try again or rephrase your input."
                    ),
                    EndSessionContent(type="end-session"),
                ]
            )
        )

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle acknowledgements"""
    ctx.logger.info(f"✅ Ack from {sender}")

# Include protocol
agent.include(chat_proto, publish_manifest=True)

# ---------------------- Recommendation Handler ----------------------

@agent.on_message(model=RecommendationReport)
async def handle_recommendation(ctx: Context, sender: str, msg: RecommendationReport):
    """Receive and forward job recommendations"""
    ctx.logger.info(f"📬 Recommendations for {msg.candidate_id}")
    
    try:
        await ctx.send(
            msg.candidate_id,
            ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[
                    TextContent(
                        type="text",
                        text=f"🎯 Your Job Recommendations:\n\n{msg.report}"
                    ),
                    EndSessionContent(type="end-session"),
                ]
            )
        )
        ctx.logger.info(f"✅ Sent recommendations to {msg.candidate_id}")
    except Exception as e:
        ctx.logger.error(f"Error sending recommendations: {e}")

@agent.on_event("startup")
async def startup(ctx: Context):
    """Startup event"""
    ctx.logger.info("="*70)
    ctx.logger.info("🚀 CANDIDATE PROFILE AGENT (JOB MATCHER)")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"🔗 Job Discovery: {JOB_DISCOVERY_ADDRESS}")
    ctx.logger.info(f"💬 Chat Protocol: Enabled")
    ctx.logger.info("="*70)

if __name__ == "__main__":
    agent.run()