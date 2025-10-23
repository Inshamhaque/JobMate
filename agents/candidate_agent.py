"""
Agent 1: Candidate Profile Agent (UPGRADED)
Receives candidate resumes (PDF or text), extracts skills, experience, and project skills
Chat Protocol enabled for ASI:One integration
"""

from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Protocol
import re
import io
import base64
from config.agent_addresses import SKILLS_MAPPER_ADDRESS

# Import shared models
from agents.models import PDFResume, CandidateProfile

# PDF parsing library
from PyPDF2 import PdfReader

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

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from PDF bytes"""
    try:
        pdf = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def extract_skills_from_text(resume_text: str) -> list:
    """Extract skills from resume text"""
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
        "html", "css", "sass", "tailwind", "bootstrap",
        "git", "rest api", "graphql", "microservices",
        "linux", "bash", "shell scripting", "devops"
    ]
    
    resume_lower = resume_text.lower()
    found_skills = [skill for skill in skill_keywords if skill in resume_lower]
    return list(set(found_skills))

def extract_experience_years(resume_text: str) -> int:
    """Extract years of experience from resume text"""
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of)?\s*(?:experience)?',
        r'experience:\s*(\d+)\+?\s*years?',
        r'(\d+)\s*yrs?',
    ]
    for pattern in patterns:
        match = re.search(pattern, resume_text.lower())
        if match:
            return int(match.group(1))
    return 3  # default

def extract_project_skills(resume_text: str, skill_list: list) -> list:
    """
    Extract skills mentioned specifically in projects sections
    Looks for lines containing 'project' and matches skills
    """
    project_skills = []
    lines = resume_text.splitlines()
    for line in lines:
        if "project" in line.lower():
            for skill in skill_list:
                if skill.lower() in line.lower():
                    project_skills.append(skill)
    return list(set(project_skills))

def process_resume(resume_text: str, sender: str) -> CandidateProfile:
    """Process resume text and create candidate profile"""
    # Extract skills
    skills = extract_skills_from_text(resume_text)
    top_skills = extract_project_skills(resume_text, skills)
    experience_years = extract_experience_years(resume_text)
    
    # Build profile
    profile = CandidateProfile(
        candidate_id=sender,
        resume_text=resume_text[:5000],  # limit for transport
        skills=skills,
        top_skills=top_skills if top_skills else skills[:5],  # fallback to top 5 skills
        experience_years=experience_years,
        preferences={
            "remote": "remote" in resume_text.lower(),
            "salary_min": 100000,
            "location_preference": "flexible"
        }
    )
    
    return profile

# ============================================================================
# PDF RESUME HANDLER (Direct messaging)
# ============================================================================

@candidate_agent.on_message(model=PDFResume)
async def handle_pdf_resume(ctx: Context, sender: str, msg: PDFResume):
    """Handle PDF resumes sent directly"""
    ctx.logger.info(f"📄 Received PDF resume: {msg.filename} from {sender}")
    ctx.logger.info(f"👤 Candidate name: {msg.candidate_name}")
    
    try:
        # Decode base64 to bytes
        pdf_bytes = base64.b64decode(msg.content)
        ctx.logger.info(f"✅ Decoded {len(pdf_bytes)} bytes from base64")
        
        # Extract text from PDF
        resume_text = extract_text_from_pdf(pdf_bytes)
        
        if not resume_text or len(resume_text) < 50:
            ctx.logger.error(f"❌ Failed to extract meaningful text from PDF")
            return
            
        ctx.logger.info(f"✅ Extracted {len(resume_text)} characters from PDF")
        
        # Process resume
        profile = process_resume(resume_text, sender)
        
        ctx.logger.info(f"🎯 Extracted {len(profile.skills)} skills: {profile.skills}")
        ctx.logger.info(f"⭐ Top {len(profile.top_skills)} skills from projects: {profile.top_skills}")
        ctx.logger.info(f"📊 Experience: {profile.experience_years} years")
        ctx.logger.info(f"🏠 Remote preference: {profile.preferences.get('remote', False)}")
        
        # Send to Skills Mapper
        if SKILLS_MAPPER_ADDRESS and "PUT_YOUR" not in SKILLS_MAPPER_ADDRESS:
            await ctx.send(SKILLS_MAPPER_ADDRESS, profile)
            ctx.logger.info(f"✅ Profile sent to Skills Mapper Agent at {SKILLS_MAPPER_ADDRESS}")
        else:
            ctx.logger.warning("⚠️  SKILLS_MAPPER_ADDRESS not configured - profile not forwarded")
            ctx.logger.info("📋 Profile created successfully (stored locally)")
            
    except base64.binascii.Error as e:
        ctx.logger.error(f"❌ Base64 decoding error: {e}")
    except Exception as e:
        ctx.logger.error(f"❌ Failed to process PDF: {type(e).__name__}: {e}")
        import traceback
        ctx.logger.error(traceback.format_exc())

# ============================================================================
# CHAT PROTOCOL HANDLERS
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
        
        resume_text = ""
        
        for item in msg.content:
            
            # Handle session start
            if isinstance(item, StartSessionContent):
                ctx.logger.info(f"✅ Chat session started with {sender}")
                
                welcome_msg = create_text_chat(
                    "👋 Welcome to JobMate!\n\n"
                    "I can help you find the perfect job match. Please share your resume:\n"
                    "• Paste your resume text here, or\n"
                    "• Send a PDF using the PDFResume message type\n\n"
                    "I'll analyze your skills and experience to find the best opportunities for you!"
                )
                await ctx.send(sender, welcome_msg)
            
            # Handle text content (plain resume)
            elif isinstance(item, TextContent):
                resume_text = item.text
                ctx.logger.info(f"📝 Received text resume ({len(resume_text)} chars)")
        
        # Process text resume if provided
        if resume_text and len(resume_text) > 50:
            try:
                profile = process_resume(resume_text, sender)
                
                ctx.logger.info(f"🎯 Extracted {len(profile.skills)} skills, {len(profile.top_skills)} top skills")
                ctx.logger.info(f"📊 Experience: {profile.experience_years} years")
                
                # Send to Skills Mapper
                if SKILLS_MAPPER_ADDRESS and "PUT_YOUR" not in SKILLS_MAPPER_ADDRESS:
                    await ctx.send(SKILLS_MAPPER_ADDRESS, profile)
                    ctx.logger.info(f"✅ Profile sent to Skills Mapper Agent")
                    
                    response = create_text_chat(
                        f"✅ **Profile Created Successfully!**\n\n"
                        f"📊 **Skills Found:** {len(profile.skills)}\n"
                        f"   Top skills: {', '.join(profile.skills[:5])}{'...' if len(profile.skills) > 5 else ''}\n\n"
                        f"🌟 **Project Skills:** {len(profile.top_skills)}\n"
                        f"   {', '.join(profile.top_skills[:5]) if profile.top_skills else 'None detected'}\n\n"
                        f"📈 **Experience:** {profile.experience_years} years\n"
                        f"🏠 **Remote:** {'Yes' if profile.preferences.get('remote') else 'No'}\n\n"
                        f"🔄 Your profile is now being processed through our AI network to find the best job matches..."
                    )
                    await ctx.send(sender, response)
                else:
                    ctx.logger.warning("⚠️  SKILLS_MAPPER_ADDRESS not configured")
                    response = create_text_chat(
                        f"✅ **Profile Created!**\n\n"
                        f"📊 Found **{len(profile.skills)} skills**\n"
                        f"⚠️  Skills Mapper not configured - profile stored locally"
                    )
                    await ctx.send(sender, response)
                    
            except Exception as e:
                ctx.logger.error(f"❌ Failed to process resume: {e}")
                error_msg = create_text_chat(
                    f"❌ **Error:** Failed to process your resume.\n"
                    f"Please ensure your resume contains clear information about your skills and experience."
                )
                await ctx.send(sender, error_msg)
    
    # IMPORTANT: Include chat protocol INSIDE the if CHAT_AVAILABLE block
    try:
        candidate_agent.include(chat_proto, publish_manifest=True)
        print("✅ Chat Protocol enabled successfully")
    except Exception as e:
        print(f"⚠️ Could not enable Chat Protocol: {e}")
        print("   Agent will run in basic mode")
        CHAT_AVAILABLE = False

# ============================================================================
# DIRECT MESSAGE HANDLER (fallback)
# ============================================================================

@candidate_agent.on_message(model=CandidateProfile)
async def handle_direct_profile(ctx: Context, sender: str, msg: CandidateProfile):
    """Handle profiles sent directly (for testing without Chat Protocol)"""
    ctx.logger.info(f"📥 Received direct profile from {sender}")
    ctx.logger.info(f"🎯 Skills: {msg.skills}")
    ctx.logger.info(f"⭐ Top skills: {msg.top_skills}")
    ctx.logger.info(f"📊 Experience: {msg.experience_years} years")
    
    # Forward to Skills Mapper
    if SKILLS_MAPPER_ADDRESS and "PUT_YOUR" not in SKILLS_MAPPER_ADDRESS:
        await ctx.send(SKILLS_MAPPER_ADDRESS, msg)
        ctx.logger.info(f"📤 Profile forwarded to Skills Mapper")
    else:
        ctx.logger.warning("⚠️  SKILLS_MAPPER_ADDRESS not configured!")

# ============================================================================
# STARTUP HANDLER
# ============================================================================

@candidate_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("="*70)
    ctx.logger.info("🚀 CANDIDATE PROFILE AGENT (PDF+Projects) STARTED")
    ctx.logger.info("="*70)
    ctx.logger.info(f"📍 Agent Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8001")
    ctx.logger.info(f"💬 Chat Protocol: {'ENABLED ✅' if CHAT_AVAILABLE else 'DISABLED ⚠️'}")
    ctx.logger.info(f"🔗 Skills Mapper: {SKILLS_MAPPER_ADDRESS if SKILLS_MAPPER_ADDRESS else 'NOT CONFIGURED'}")
    ctx.logger.info(f"🎯 Ready to receive candidate resumes!")
    ctx.logger.info("="*70 + "\n")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AGENT 1: CANDIDATE PROFILE AGENT (PDF+Projects)")
    print("="*70 + "\n")
    candidate_agent.run()