"""
Agent 1: Candidate Profile Agent (FIXED)
Receives candidate resumes and extracts skills
Chat Protocol enabled for ASI:One integration
"""

from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Model, Protocol
import re
from config.agent_addresses import SKILLS_MAPPER_ADDRESS

# Try to import chat protocol components
try:
    from uagents_core.contrib.protocols.chat import (
        ChatAcknowledgement,
        ChatMessage,
        TextContent,
        StartSessionContent,
        EndSessionContent,
        chat_protocol_spec,
    )
    CHAT_AVAILABLE = True
except ImportError:
    CHAT_AVAILABLE = False
    print("⚠️  Chat protocol not available - running in basic mode")

# ============================================================================
# DATA MODELS
# ============================================================================

class CandidateProfile(Model):
    candidate_id: str
    resume_text: str
    skills: list
    experience_years: int
    preferences: dict

# ============================================================================
# CONFIGURATION - UPDATE THIS!
# ============================================================================

# IMPORTANT: Replace with actual Skills Mapper Agent address after first run
# SKILLS_MAPPER_ADDRESS = 

# ============================================================================
# AGENT INITIALIZATION
# ============================================================================

candidate_agent = Agent(
    name="Candidate Profile Agent",
    port=8001,
    seed="candidate_agent_seed_unique_123456",
    endpoint=["http://localhost:8001/submit"]
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_skills_from_resume(resume_text: str) -> list:
    """
    Extract skills from resume text
    In production, replace with LangChain NLP for better extraction
    """
    skill_keywords = [
        "python", "java", "javascript", "react", "node.js", "angular", "vue.js",
        "django", "flask", "fastapi", "spring", "express",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "machine learning", "deep learning", "data science", "ai",
        "tensorflow", "pytorch", "scikit-learn",
        "sql", "postgresql", "mysql", "mongodb", "redis",
        "ci/cd", "jenkins", "github actions", "gitlab",
        "agile", "scrum", "leadership", "project management",
        "typescript", "go", "rust", "c++", "c#",
        "html", "css", "sass", "tailwind", "bootstrap"
    ]
    
    resume_lower = resume_text.lower()
    found_skills = []
    
    for skill in skill_keywords:
        if skill in resume_lower:
            found_skills.append(skill)
    
    return list(set(found_skills))  # Remove duplicates

def extract_experience_years(resume_text: str) -> int:
    """Extract years of experience from resume"""
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of)?\s*(?:experience)?',
        r'experience:\s*(\d+)\+?\s*years?',
        r'(\d+)\s*yrs?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, resume_text.lower())
        if match:
            return int(match.group(1))
    
    return 3  # Default to 3 years if not found

# ============================================================================
# CHAT PROTOCOL (if available)
# ============================================================================

if CHAT_AVAILABLE:
    chat_proto = Protocol(spec=chat_protocol_spec)
    
    def create_text_chat(text: str) -> ChatMessage:
        """Create a chat message with text content"""
        content = [TextContent(type="text", text=text)]
        return ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=content,
        )
    
    @chat_proto.on_message(ChatMessage)
    async def handle_candidate_message(ctx: Context, sender: str, msg: ChatMessage):
        """Handle messages from ASI:One interface or other agents"""
        ctx.logger.info(f"📥 Received chat message from {sender}")
        
        # Always acknowledge receipt
        await ctx.send(
            sender,
            ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
        )
        
        # Process each content item in the message
        for item in msg.content:
            
            # Handle session start
            if isinstance(item, StartSessionContent):
                ctx.logger.info(f"✅ Chat session started with {sender}")
                
                welcome_msg = create_text_chat(
                    "👋 Welcome to AI Job Matching Platform!\n\n"
                    "I'm your Candidate Profile Agent. Please share your resume or describe:\n"
                    "• Your skills and technologies\n"
                    "• Years of experience\n"
                    "• Job preferences (remote, salary, etc.)\n\n"
                    "I'll process your profile through our AI network! 🚀"
                )
                await ctx.send(sender, welcome_msg)
            
            # Handle text content (resume submission)
            elif isinstance(item, TextContent):
                ctx.logger.info(f"📄 Processing resume from {sender}")
                
                resume_text = item.text
                skills = extract_skills_from_resume(resume_text)
                experience_years = extract_experience_years(resume_text)
                
                ctx.logger.info(f"🎯 Extracted {len(skills)} skills")
                ctx.logger.info(f"📊 Experience: {experience_years} years")
                
                # Create candidate profile
                profile = CandidateProfile(
                    candidate_id=sender,
                    resume_text=resume_text[:1000],
                    skills=skills,
                    experience_years=experience_years,
                    preferences={
                        "remote": "remote" in resume_text.lower(),
                        "salary_min": 100000,
                        "location_preference": "flexible"
                    }
                )
                
                # Send to Skills Mapper Agent
                if "PUT_YOUR" not in SKILLS_MAPPER_ADDRESS:
                    try:
                        await ctx.send(SKILLS_MAPPER_ADDRESS, profile)
                        ctx.logger.info(f"✅ Profile sent to Skills Mapper")
                        
                        response = create_text_chat(
                            f"✅ **Profile Created!**\n\n"
                            f"📊 Found **{len(skills)} skills**: {', '.join(skills[:5])}...\n"
                            f"📈 Experience: **{experience_years} years**\n\n"
                            f"🔄 Processing through AI network..."
                        )
                        await ctx.send(sender, response)
                        
                    except Exception as e:
                        ctx.logger.error(f"❌ Failed to send: {e}")
                else:
                    ctx.logger.error("❌ SKILLS_MAPPER_ADDRESS not configured!")
            
            # Handle session end
            elif isinstance(item, EndSessionContent):
                ctx.logger.info(f"👋 Chat session ended with {sender}")
    
    @chat_proto.on_message(ChatAcknowledgement)
    async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
        """Handle message acknowledgements"""
        ctx.logger.info(f"✅ Message acknowledged")

# ============================================================================
# DIRECT MESSAGE HANDLER (fallback if Chat Protocol not available)
# ============================================================================

@candidate_agent.on_message(model=CandidateProfile)
async def handle_direct_profile(ctx: Context, sender: str, msg: CandidateProfile):
    """Handle profiles sent directly (for testing without Chat Protocol)"""
    ctx.logger.info(f"📥 Received direct profile from {sender}")
    ctx.logger.info(f"🎯 Skills: {msg.skills}")
    
    # Forward to Skills Mapper
    if "PUT_YOUR" not in SKILLS_MAPPER_ADDRESS:
        await ctx.send(SKILLS_MAPPER_ADDRESS, msg)
        ctx.logger.info(f"📤 Profile forwarded to Skills Mapper")
    else:
        ctx.logger.error("❌ SKILLS_MAPPER_ADDRESS not configured!")

# ============================================================================
# STARTUP HANDLER
# ============================================================================

@candidate_agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize agent on startup"""
    ctx.logger.info("="*70)
    ctx.logger.info("🚀 CANDIDATE PROFILE AGENT STARTED")
    ctx.logger.info("="*70)
    ctx.logger.info(f"📍 Agent Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8001")
    ctx.logger.info(f"💬 Chat Protocol: {'ENABLED' if CHAT_AVAILABLE else 'DISABLED'}")
    ctx.logger.info(f"🎯 Ready to receive candidate profiles!")
    ctx.logger.info("="*70 + "\n")
    
    # Check configuration
    if "PUT_YOUR" in SKILLS_MAPPER_ADDRESS:
        ctx.logger.warning("⚠️  WARNING: SKILLS_MAPPER_ADDRESS not configured!")
        ctx.logger.warning("   Run skills_mapper_agent.py and copy its address here")

# ============================================================================
# INCLUDE CHAT PROTOCOL (if available) & RUN
# ============================================================================

if CHAT_AVAILABLE:
    try:
        candidate_agent.include(chat_proto, publish_manifest=True)
        print("✅ Chat Protocol enabled successfully")
    except Exception as e:
        print(f"⚠️  Could not enable Chat Protocol: {e}")
        print("   Agent will run in basic mode (can still receive direct messages)")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AGENT 1: CANDIDATE PROFILE AGENT")
    print("="*70)
    print("\nIMPORTANT SETUP:")
    print("1. Copy this agent's address (shown when it starts)")
    print("2. Run skills_mapper_agent.py and copy its address")
    print("3. Update SKILLS_MAPPER_ADDRESS in this file")
    print("4. Restart this agent")
    print("\n🔧 Starting agent...")
    print("="*70 + "\n")
    
    candidate_agent.run()