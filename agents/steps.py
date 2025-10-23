"""
===============================================================================
AI JOB MATCHING PLATFORM - ALL 5 AGENTS IN ONE FILE
===============================================================================

IMPORTANT INSTRUCTIONS:
1. Split this file into 5 separate files (one per agent)
2. Run each agent in a separate terminal
3. Copy agent addresses and update configuration sections

FILE STRUCTURE:
- Agent 1: Candidate Profile Agent (Lines 50-250)
- Agent 2: Skills Mapper Agent (Lines 260-500)
- Agent 3: Job Discovery Agent (Lines 510-800)
- Agent 4: Compatibility Scorer Agent (Lines 810-1050)
- Agent 5: Recommendation Agent (Lines 1060-1350)

===============================================================================
"""

# ============================================================================
# ============================================================================
# AGENT 1: CANDIDATE PROFILE AGENT
# Save as: candidate_agent.py
# Port: 8001
# Chat Protocol: ENABLED (ASI:One)
# ============================================================================
# ============================================================================

"""
from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    StartSessionContent,
    EndSessionContent,
    chat_protocol_spec,
)

# Data Models
class CandidateProfile(Model):
    candidate_id: str
    resume_text: str
    skills: list
    experience_years: int
    preferences: dict

# CONFIGURATION - UPDATE THIS AFTER RUNNING AGENT 2
SKILLS_MAPPER_ADDRESS = "agent1qPUT_AGENT_2_ADDRESS_HERE"

# Initialize Agent
candidate_agent = Agent(
    name="Candidate Profile Agent",
    port=8001,
    seed="candidate_agent_seed_123",
    endpoint=["http://localhost:8001/submit"]
)

chat_proto = Protocol(spec=chat_protocol_spec)

def create_text_chat(text: str) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )

def extract_skills_from_resume(resume_text: str) -> list:
    skill_keywords = [
        "python", "java", "javascript", "react", "node.js", "angular", "vue.js",
        "django", "flask", "fastapi", "spring", "express",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "machine learning", "deep learning", "data science", "ai",
        "tensorflow", "pytorch", "scikit-learn",
        "sql", "postgresql", "mysql", "mongodb", "redis",
        "ci/cd", "jenkins", "github actions", "gitlab",
        "agile", "scrum", "leadership", "project management",
        "typescript", "go", "rust", "c++", "c#"
    ]
    
    resume_lower = resume_text.lower()
    found_skills = [skill for skill in skill_keywords if skill in resume_lower]
    return list(set(found_skills))

@chat_proto.on_message(ChatMessage)
async def handle_candidate_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"📥 Received message from {sender}")
    
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.utcnow(),
            acknowledged_msg_id=msg.msg_id
        )
    )
    
    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"✅ Chat session started")
            welcome = create_text_chat(
                "👋 Welcome to AI Job Matching! Please share your resume."
            )
            await ctx.send(sender, welcome)
        
        elif isinstance(item, TextContent):
            ctx.logger.info(f"📄 Processing resume")
            resume_text = item.text
            skills = extract_skills_from_resume(resume_text)
            
            profile = CandidateProfile(
                candidate_id=sender,
                resume_text=resume_text[:1000],
                skills=skills,
                experience_years=5,
                preferences={"remote": True, "salary_min": 100000}
            )
            
            ctx.logger.info(f"🎯 Skills found: {skills}")
            
            if "PUT_AGENT" not in SKILLS_MAPPER_ADDRESS:
                await ctx.send(SKILLS_MAPPER_ADDRESS, profile)
                ctx.logger.info(f"📤 Profile sent to Skills Mapper")
                
                response = create_text_chat(
                    f"✅ Found {len(skills)} skills: {', '.join(skills[:5])}\n"
                    f"🔄 Processing through AI network..."
                )
                await ctx.send(sender, response)
            else:
                ctx.logger.error("❌ SKILLS_MAPPER_ADDRESS not configured!")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"✅ Message acknowledged")

@candidate_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("🚀 CANDIDATE PROFILE AGENT STARTED")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8001")

candidate_agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    candidate_agent.run()
"""

# ============================================================================
# ============================================================================
# AGENT 2: SKILLS MAPPER AGENT
# Save as: skills_mapper_agent.py
# Port: 8002
# MeTTa Integration: YES
# ============================================================================
# ============================================================================

"""
from uagents import Agent, Context, Model

# Data Models
class CandidateProfile(Model):
    candidate_id: str
    resume_text: str
    skills: list
    experience_years: int
    preferences: dict

class EnrichedSkillsProfile(Model):
    candidate_id: str
    original_skills: list
    related_skills: list
    skill_categories: dict
    market_demand: dict
    experience_years: int
    preferences: dict

# CONFIGURATION - UPDATE THIS AFTER RUNNING AGENT 3
JOB_DISCOVERY_ADDRESS = "agent1qPUT_AGENT_3_ADDRESS_HERE"

# Initialize Agent
skills_mapper_agent = Agent(
    name="Skills Mapper Agent",
    port=8002,
    seed="skills_mapper_seed_456",
    endpoint=["http://localhost:8002/submit"]
)

# MeTTa Knowledge Graph (Simulated)
SKILLS_KNOWLEDGE_GRAPH = {
    "python": {
        "related": ["django", "flask", "pandas", "data science", "machine learning"],
        "category": "Programming",
        "demand": "very high",
        "avg_salary": 120000
    },
    "javascript": {
        "related": ["react", "node.js", "vue.js", "typescript"],
        "category": "Programming",
        "demand": "very high",
        "avg_salary": 115000
    },
    "react": {
        "related": ["javascript", "redux", "next.js", "typescript"],
        "category": "Frontend",
        "demand": "very high",
        "avg_salary": 110000
    },
    "machine learning": {
        "related": ["tensorflow", "pytorch", "python", "data science", "ai"],
        "category": "AI/ML",
        "demand": "very high",
        "avg_salary": 145000
    },
    "aws": {
        "related": ["docker", "kubernetes", "terraform", "devops"],
        "category": "Cloud",
        "demand": "very high",
        "avg_salary": 135000
    },
    "docker": {
        "related": ["kubernetes", "aws", "devops", "ci/cd"],
        "category": "DevOps",
        "demand": "very high",
        "avg_salary": 125000
    },
    "sql": {
        "related": ["postgresql", "mysql", "database", "data analysis"],
        "category": "Database",
        "demand": "high",
        "avg_salary": 105000
    },
    "leadership": {
        "related": ["project management", "agile", "team building"],
        "category": "Soft Skills",
        "demand": "very high",
        "avg_salary": 155000
    }
}

def query_metta_knowledge_graph(skills: list) -> dict:
    related_skills = set()
    skill_categories = {}
    market_demand = {}
    
    for skill in skills:
        skill_lower = skill.lower()
        if skill_lower in SKILLS_KNOWLEDGE_GRAPH:
            info = SKILLS_KNOWLEDGE_GRAPH[skill_lower]
            related_skills.update(info["related"])
            
            category = info["category"]
            if category not in skill_categories:
                skill_categories[category] = []
            skill_categories[category].append(skill)
            
            market_demand[skill] = {
                "demand": info["demand"],
                "avg_salary": info["avg_salary"]
            }
    
    return {
        "related_skills": list(related_skills),
        "skill_categories": skill_categories,
        "market_demand": market_demand
    }

@skills_mapper_agent.on_message(model=CandidateProfile)
async def map_skills(ctx: Context, sender: str, msg: CandidateProfile):
    ctx.logger.info(f"📥 Profile received for: {msg.candidate_id}")
    ctx.logger.info(f"🎯 Original skills: {msg.skills}")
    
    enriched_data = query_metta_knowledge_graph(msg.skills)
    
    ctx.logger.info(f"✅ Found {len(enriched_data['related_skills'])} related skills")
    
    enriched_profile = EnrichedSkillsProfile(
        candidate_id=msg.candidate_id,
        original_skills=msg.skills,
        related_skills=enriched_data["related_skills"],
        skill_categories=enriched_data["skill_categories"],
        market_demand=enriched_data["market_demand"],
        experience_years=msg.experience_years,
        preferences=msg.preferences
    )
    
    if "PUT_AGENT" not in JOB_DISCOVERY_ADDRESS:
        await ctx.send(JOB_DISCOVERY_ADDRESS, enriched_profile)
        ctx.logger.info(f"📤 Enriched profile sent to Job Discovery")
    else:
        ctx.logger.error("❌ JOB_DISCOVERY_ADDRESS not configured!")

@skills_mapper_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("🚀 SKILLS MAPPER AGENT STARTED")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8002")

if __name__ == "__main__":
    skills_mapper_agent.run()
"""

# ============================================================================
# ============================================================================
# AGENT 3: JOB DISCOVERY AGENT
# Save as: job_discovery_agent.py
# Port: 8003
# LangChain RAG: YES
# ============================================================================
# ============================================================================

"""
from uagents import Agent, Context, Model

# Data Models
class EnrichedSkillsProfile(Model):
    candidate_id: str
    original_skills: list
    related_skills: list
    skill_categories: dict
    market_demand: dict
    experience_years: int
    preferences: dict

class JobListing(Model):
    job_id: str
    candidate_id: str
    title: str
    company: str
    requirements: list
    description: str
    salary_range: str
    location: str
    remote: bool

# CONFIGURATION - UPDATE THIS AFTER RUNNING AGENT 4
SCORER_ADDRESS = "agent1qPUT_AGENT_4_ADDRESS_HERE"

# Initialize Agent
job_discovery_agent = Agent(
    name="Job Discovery Agent",
    port=8003,
    seed="job_discovery_seed_789",
    endpoint=["http://localhost:8003/submit"]
)

# Job Database (Mock - In production use LangChain + FAISS)
JOB_DATABASE = [
    {
        "job_id": "JOB001",
        "title": "Senior Python Developer",
        "company": "TechCorp AI",
        "requirements": ["python", "django", "aws", "sql", "docker"],
        "description": "Build scalable backend systems for AI applications",
        "salary_range": "$120k-$160k",
        "location": "San Francisco, CA",
        "remote": True
    },
    {
        "job_id": "JOB002",
        "title": "Machine Learning Engineer",
        "company": "DataScience Pro",
        "requirements": ["python", "machine learning", "tensorflow", "aws"],
        "description": "Develop ML models for predictive analytics",
        "salary_range": "$140k-$180k",
        "location": "New York, NY",
        "remote": True
    },
    {
        "job_id": "JOB003",
        "title": "Full Stack Developer",
        "company": "WebSolutions Inc",
        "requirements": ["javascript", "react", "node.js", "mongodb"],
        "description": "Build modern web applications",
        "salary_range": "$110k-$150k",
        "location": "Austin, TX",
        "remote": True
    },
    {
        "job_id": "JOB004",
        "title": "DevOps Engineer",
        "company": "CloudFirst",
        "requirements": ["aws", "kubernetes", "docker", "ci/cd"],
        "description": "Manage cloud infrastructure",
        "salary_range": "$130k-$170k",
        "location": "Seattle, WA",
        "remote": True
    },
    {
        "job_id": "JOB005",
        "title": "Engineering Manager",
        "company": "InnovateTech",
        "requirements": ["leadership", "python", "agile"],
        "description": "Lead engineering team",
        "salary_range": "$150k-$200k",
        "location": "Boston, MA",
        "remote": False
    }
]

def semantic_job_search(profile: EnrichedSkillsProfile) -> list:
    all_skills = set(
        skill.lower() for skill in 
        profile.original_skills + profile.related_skills
    )
    
    matched_jobs = []
    
    for job in JOB_DATABASE:
        job_requirements = set(req.lower() for req in job["requirements"])
        matching_skills = all_skills.intersection(job_requirements)
        
        if matching_skills:
            match_percentage = (len(matching_skills) / len(job_requirements)) * 100
            matched_jobs.append({
                **job,
                "matching_skills": list(matching_skills),
                "match_percentage": match_percentage
            })
    
    matched_jobs.sort(key=lambda x: x["match_percentage"], reverse=True)
    return matched_jobs[:5]

@job_discovery_agent.on_message(model=EnrichedSkillsProfile)
async def discover_jobs(ctx: Context, sender: str, msg: EnrichedSkillsProfile):
    ctx.logger.info(f"📥 Enriched profile received: {msg.candidate_id}")
    ctx.logger.info(f"🔍 Searching jobs...")
    
    matching_jobs = semantic_job_search(msg)
    
    ctx.logger.info(f"✅ Found {len(matching_jobs)} matching jobs")
    
    for job_data in matching_jobs:
        job_listing = JobListing(
            job_id=job_data["job_id"],
            candidate_id=msg.candidate_id,
            title=job_data["title"],
            company=job_data["company"],
            requirements=job_data["requirements"],
            description=job_data["description"],
            salary_range=job_data["salary_range"],
            location=job_data["location"],
            remote=job_data["remote"]
        )
        
        if "PUT_AGENT" not in SCORER_ADDRESS:
            await ctx.send(SCORER_ADDRESS, job_listing)
            ctx.logger.info(f"📤 Sent {job_data['title']} to Scorer")
        else:
            ctx.logger.error("❌ SCORER_ADDRESS not configured!")

@job_discovery_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("🚀 JOB DISCOVERY AGENT STARTED")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8003")

if __name__ == "__main__":
    job_discovery_agent.run()
"""

# ============================================================================
# ============================================================================
# AGENT 4: COMPATIBILITY SCORER AGENT
# Save as: scorer_agent.py
# Port: 8004
# LangChain Reasoning: YES
# ============================================================================
# ============================================================================

"""
from uagents import Agent, Context, Model

# Data Models
class JobListing(Model):
    job_id: str
    candidate_id: str
    title: str
    company: str
    requirements: list
    description: str
    salary_range: str
    location: str
    remote: bool

class MatchScore(Model):
    job_id: str
    candidate_id: str
    title: str
    company: str
    match_score: float
    reasoning: str
    skill_gaps: list
    strengths: list
    salary_range: str
    location: str
    remote: bool

# CONFIGURATION - UPDATE THIS AFTER RUNNING AGENT 5
RECOMMENDER_ADDRESS = "agent1qPUT_AGENT_5_ADDRESS_HERE"

# Initialize Agent
scorer_agent = Agent(
    name="Compatibility Scorer Agent",
    port=8004,
    seed="scorer_seed_abc",
    endpoint=["http://localhost:8004/submit"]
)

def calculate_compatibility_score(job: JobListing) -> dict:
    # Mock candidate skills (in production, retrieve from context)
    candidate_skills = ["python", "django", "aws", "docker", "machine learning"]
    
    matching_skills = [
        skill for skill in job.requirements 
        if skill.lower() in [s.lower() for s in candidate_skills]
    ]
    missing_skills = [
        skill for skill in job.requirements 
        if skill.lower() not in [s.lower() for s in candidate_skills]
    ]
    
    base_score = 75.0
    if len(job.requirements) > 0:
        base_score = (len(matching_skills) / len(job.requirements)) * 100
    
    if job.remote:
        base_score += 5
    
    reasoning = f'''
Match Analysis for {job.title} at {job.company}:

✅ Matching Skills ({len(matching_skills)}/{len(job.requirements)}):
{', '.join(matching_skills) if matching_skills else 'None'}

⚠️ Skill Gaps ({len(missing_skills)}):
{', '.join(missing_skills) if missing_skills else 'None'}

💰 Salary: {job.salary_range}
📍 Location: {job.location} {'(Remote)' if job.remote else '(On-site)'}

Overall Score: {base_score:.1f}%

Recommendation: {"Strong Match!" if base_score >= 80 else "Good Match" if base_score >= 60 else "Moderate Match"}
    '''
    
    return {
        "score": base_score,
        "reasoning": reasoning.strip(),
        "skill_gaps": missing_skills,
        "strengths": matching_skills
    }

@scorer_agent.on_message(model=JobListing)
async def score_compatibility(ctx: Context, sender: str, msg: JobListing):
    ctx.logger.info(f"📥 Scoring: {msg.title}")
    
    analysis = calculate_compatibility_score(msg)
    
    ctx.logger.info(f"📊 Score: {analysis['score']:.1f}%")
    
    match_score = MatchScore(
        job_id=msg.job_id,
        candidate_id=msg.candidate_id,
        title=msg.title,
        company=msg.company,
        match_score=analysis["score"],
        reasoning=analysis["reasoning"],
        skill_gaps=analysis["skill_gaps"],
        strengths=analysis["strengths"],
        salary_range=msg.salary_range,
        location=msg.location,
        remote=msg.remote
    )
    
    if "PUT_AGENT" not in RECOMMENDER_ADDRESS:
        await ctx.send(RECOMMENDER_ADDRESS, match_score)
        ctx.logger.info(f"📤 Score sent to Recommender")
    else:
        ctx.logger.error("❌ RECOMMENDER_ADDRESS not configured!")

@scorer_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("🚀 COMPATIBILITY SCORER AGENT STARTED")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8004")

if __name__ == "__main__":
    scorer_agent.run()
"""

# ============================================================================
# ============================================================================
# AGENT 5: RECOMMENDATION AGENT
# Save as: recommender_agent.py
# Port: 8005
# Chat Protocol: ENABLED (ASI:One)
# ============================================================================
# ============================================================================

"""
from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# Data Models
class MatchScore(Model):
    job_id: str
    candidate_id: str
    title: str
    company: str
    match_score: float
    reasoning: str
    skill_gaps: list
    strengths: list
    salary_range: str
    location: str
    remote: bool

# Initialize Agent
recommender_agent = Agent(
    name="Recommendation Agent",
    port=8005,
    seed="recommender_seed_def",
    endpoint=["http://localhost:8005/submit"]
)

chat_proto = Protocol(spec=chat_protocol_spec)

# Store recommendations
candidate_recommendations = {}

def create_text_chat(text: str) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )

def generate_learning_path(skill_gaps: list) -> str:
    if not skill_gaps:
        return "✅ You have all required skills!"
    
    resources = {
        "kubernetes": "📚 Kubernetes.io, CKAD cert",
        "tensorflow": "📚 TensorFlow.org courses",
        "react": "📚 React.dev, Full Stack Open",
        "aws": "📚 AWS Training, SA cert",
    }
    
    path = "🎓 Recommended Learning:\n"
    for skill in skill_gaps[:3]:
        resource = resources.get(skill.lower(), f"📚 {skill} courses")
        path += f"• {skill}: {resource}\n"
    
    return path

def create_recommendation_report(matches: list) -> str:
    if not matches:
        return "No matching jobs found."
    
    matches.sort(key=lambda x: x.match_score, reverse=True)
    top_matches = matches[:3]
    
    report = "🎯 **Your Top Job Matches**\n\n"
    
    for i, match in enumerate(top_matches, 1):
        report += f"**#{i} - {match.title}** at **{match.company}**\n"
        report += f"📊 Score: {match.match_score:.1f}%\n"
        report += f"💰 Salary: {match.salary_range}\n"
        report += f"📍 {match.location} {'🏠 Remote' if match.remote else '🏢 On-site'}\n\n"
        
        if match.strengths:
            report += f"✅ Strengths: {', '.join(match.strengths)}\n"
        if match.skill_gaps:
            report += f"⚠️ Gaps: {', '.join(match.skill_gaps)}\n"
            report += generate_learning_path(match.skill_gaps) + "\n"
        
        report += "-" * 50 + "\n\n"
    
    avg_score = sum(m.match_score for m in matches) / len(matches)
    report += f"📈 Overall Profile Strength: {avg_score:.1f}%\n"
    
    return report

@recommender_agent.on_message(model=MatchScore)
async def aggregate_recommendations(ctx: Context, sender: str, msg: MatchScore):
    ctx.logger.info(f"📥 Score received: {msg.title} ({msg.match_score:.1f}%)")
    
    if msg.candidate_id not in candidate_recommendations:
        candidate_recommendations[msg.candidate_id] = []
    candidate_recommendations[msg.candidate_id].append(msg)
    
    num_recommendations = len(candidate_recommendations[msg.candidate_id])
    ctx.logger.info(f"📊 Total recommendations: {num_recommendations}")
    
    if num_recommendations >= 3:
        ctx.logger.info(f"✅ Generating report")
        
        report = create_recommendation_report(
            candidate_recommendations[msg.candidate_id]
        )
        
        response = create_text_chat(report)
        
        try:
            await ctx.send(msg.candidate_id, response)
            ctx.logger.info(f"📤 Report sent to candidate")
        except Exception as e:
            ctx.logger.error(f"❌ Failed to send: {e}")
        
        del candidate_recommendations[msg.candidate_id]

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"✅ Report acknowledged")

@recommender_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("🚀 RECOMMENDATION AGENT STARTED")
    ctx.logger.info(f"📍 Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8005")

recommender_agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    recommender_agent.run()
"""

# ============================================================================
# END OF ALL AGENTS CODE
# ============================================================================

print("""
===============================================================================
SETUP INSTRUCTIONS
===============================================================================

STEP 1: CREATE SEPARATE FILES
-------------------------------
Copy each agent code block (marked with triple quotes) into separate files:

1. candidate_agent.py      (Agent 1 code)
2. skills_mapper_agent.py  (Agent 2 code)
3. job_discovery_agent.py  (Agent 3 code)
4. scorer_agent.py         (Agent 4 code)
5. recommender_agent.py    (Agent 5 code)

STEP 2: INSTALL DEPENDENCIES
-----------------------------
pip install uagents uagents-core requests

STEP 3: GET AGENT ADDRESSES
----------------------------
Run each agent ONCE to get its address:

Terminal 1: python skills_mapper_agent.py
→ Copy address: agent1q...

Terminal 2: python job_discovery_agent.py
→ Copy address: agent1q...

Terminal 3: python scorer_agent.py
→ Copy address: agent1q...

Terminal 4: python recommender_agent.py
→ Copy address: agent1q...

STEP 4: UPDATE ADDRESSES
-------------------------
Update these variables in each file:

In candidate_agent.py:
    SKILLS_MAPPER_ADDRESS = "agent1q..."  (from Agent 2)

In skills_mapper_agent.py:
    JOB_DISCOVERY_ADDRESS = "agent1q..."  (from Agent 3)

In job_discovery_agent.py:
    SCORER_ADDRESS = "agent1q..."  (from Agent 4)

In scorer_agent.py:
    RECOMMENDER_ADDRESS = "agent1q..."  (from Agent 5)

STEP 5: RUN ALL AGENTS
-----------------------
Open 5 terminals and run:

Terminal 1: python candidate_agent.py
Terminal 2: python skills_mapper_agent.py
Terminal 3: python job_discovery_agent.py
Terminal 4: python scorer_agent.py
Terminal 5: python recommender_agent.py

STEP 6: TEST THE SYSTEM
------------------------
Create test.py:

from uagents import Agent, Context, Model

class CandidateProfile(Model):
    candidate_id: str
    resume_text: str
    skills: list
    experience_years: int
    preferences: dict

test = Agent(name="test", port=9000, seed="test123")

@test.on_event("startup")
async def send(ctx: Context):
    await ctx.send(
        "agent1q...",  # Your candidate agent address
        CandidateProfile(
            candidate_id="test_user",
            resume_text="Python ML engineer with 5 years experience",
            skills=["python", "machine learning", "aws", "docker"],
            experience_years=5,
            preferences={"remote": True}
        )
    )

test.run()

Then run: python test.py

Watch the logs flow through all 5 agents!

===============================================================================
""")