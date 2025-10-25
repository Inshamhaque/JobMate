"""
Agent 5: Recommendation Agent with Real-Time Course Search
Aggregates job scores and sends final recommendations
Includes LangChain-powered real-time course discovery
"""

from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Model, Protocol
from config.agent_addresses import TEST_AGENT_ADDRESS
from agents.models import RecommendationReport

# LangChain imports for real-time search
try:
    from langchain_community.tools import DuckDuckGoSearchRun
    # from langchain.agents import initialize_agent, AgentType
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import PromptTemplate
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False
    print("LangChain not available - using fallback resources")

# Chat protocol imports
try:
    from uagents_core.contrib.protocols.chat import (
        ChatAcknowledgement,
        ChatMessage,
        TextContent,
        chat_protocol_spec,
    )
    CHAT_AVAILABLE = True
except ImportError:
    CHAT_AVAILABLE = False
    print("⚠️  Chat protocol not available - running in basic mode")

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
    source_url: str 


# Initialize Agent
recommender_agent = Agent(
    name="Recommendation Agent",
    port=8005,
    seed="recommender_seed_def_unique_12345",
    endpoint=["http://localhost:8005/submit"]
)

# Store recommendations by candidate
candidate_recommendations = {}

# ============================================================================
# REAL-TIME SEARCH FUNCTIONS
# ============================================================================

def extract_url_from_search(text: str, domain: str) -> str:
    """Extract clean URL from search results"""
    import re
    
    # Try to find URL patterns
    url_pattern = rf'https?://(?:www\.)?{domain}[^\s\)]*'
    matches = re.findall(url_pattern, text)
    
    if matches:
        # Return the first clean URL
        url = matches[0].rstrip('.,;)')
        return url
    
    return None

def search_youtube_courses(skill: str) -> str:
    """Search for top-rated YouTube courses and return direct video link"""
    if not SEARCH_AVAILABLE:
        return "🎥 https://www.youtube.com/results?search_query=freeCodeCamp+" + skill.replace(' ', '+')
    
    try:
        search = DuckDuckGoSearchRun()
        query = f"site:youtube.com {skill} tutorial full course freeCodeCamp OR programming with mosh OR traversy media"
        results = search.run(query)
        
        # Extract YouTube URL
        url = extract_url_from_search(results, r'(?:youtube\.com|youtu\.be)')
        
        if url:
            return f"🎥 {url}"
        
        # Fallback: construct search URL
        search_query = f"freeCodeCamp {skill} full course".replace(' ', '+')
        return f"🎥 https://www.youtube.com/results?search_query={search_query}"
    
    except Exception as e:
        search_query = f"freeCodeCamp {skill}".replace(' ', '+')
        return f"🎥 https://www.youtube.com/results?search_query={search_query}"

def search_udemy_courses(skill: str) -> str:
    """Search for top-rated Udemy courses and return direct course link"""
    if not SEARCH_AVAILABLE:
        return "💎 https://www.udemy.com/courses/search/?q=" + skill.replace(' ', '%20') + "&sort=highest-rated"
    
    try:
        search = DuckDuckGoSearchRun()
        query = f"site:udemy.com {skill} course highest rated complete guide"
        results = search.run(query)
        
        # Extract Udemy URL
        url = extract_url_from_search(results, r'udemy\.com')
        
        if url and '/course/' in url:
            return f"💎 {url}"
        
        # Fallback: construct search URL with highest-rated filter
        search_query = skill.replace(' ', '%20')
        return f"💎 https://www.udemy.com/courses/search/?q={search_query}&sort=highest-rated"
    
    except Exception as e:
        search_query = skill.replace(' ', '%20')
        return f"💎 https://www.udemy.com/courses/search/?q={search_query}&sort=highest-rated"

def search_coursera_courses(skill: str) -> str:
    """Search for Coursera specializations and return direct course link"""
    if not SEARCH_AVAILABLE:
        return "🎓 https://www.coursera.org/search?query=" + skill.replace(' ', '%20')
    
    try:
        search = DuckDuckGoSearchRun()
        query = f"site:coursera.org {skill} specialization professional certificate"
        results = search.run(query)
        
        # Extract Coursera URL
        url = extract_url_from_search(results, r'coursera\.org')
        
        if url and ('/specializations/' in url or '/professional-certificates/' in url or '/learn/' in url):
            return f"🎓 {url}"
        
        # Fallback: construct search URL
        search_query = skill.replace(' ', '%20')
        return f"🎓 https://www.coursera.org/search?query={search_query}"
    
    except Exception as e:
        search_query = skill.replace(' ', '%20')
        return f"🎓 https://www.coursera.org/search?query={search_query}"

def get_comprehensive_learning_resources(skill: str) -> dict:
    """Get comprehensive learning resources with direct links"""
    
    # Fallback direct links (used if search fails)
    fallback_resources = {
        "kubernetes": {
            "youtube": "🎥 https://youtu.be/X48VuDVv0do",
            "premium": "💎 https://www.udemy.com/course/learn-devops-the-complete-kubernetes-course/"
        },
        "tensorflow": {
            "youtube": "🎥 https://youtu.be/tPYj3fFJGjk",
            "premium": "💎 https://www.coursera.org/professional-certificates/tensorflow-in-practice"
        },
        "react": {
            "youtube": "🎥 https://youtu.be/bMknfKXIFA8",
            "premium": "💎 https://www.udemy.com/course/react-the-complete-guide-incl-redux/"
        },
        "aws": {
            "youtube": "🎥 https://youtu.be/Ia-UEYYR44s",
            "premium": "💎 https://www.udemy.com/course/aws-certified-solutions-architect-associate-saa-c03/"
        },
        "python": {
            "youtube": "🎥 https://youtu.be/rfscVS0vtbw",
            "premium": "💎 https://www.udemy.com/course/100-days-of-code/"
        },
        "docker": {
            "youtube": "🎥 https://youtu.be/3c-iBn73dDE",
            "premium": "💎 https://www.udemy.com/course/docker-mastery/"
        },
        "typescript": {
            "youtube": "🎥 https://youtu.be/30LWjhZzg50",
            "premium": "💎 https://www.udemy.com/course/understanding-typescript/"
        },
        "node.js": {
            "youtube": "🎥 https://youtu.be/Oe421EPjeBE",
            "premium": "💎 https://www.udemy.com/course/the-complete-nodejs-developer-course-2/"
        },
        "django": {
            "youtube": "🎥 https://youtu.be/F5mRW0jo-U4",
            "premium": "💎 https://www.udemy.com/course/python-django-dev-to-deployment/"
        },
        "machine learning": {
            "youtube": "🎥 https://youtu.be/i_LwzRVP7bg",
            "premium": "💎 https://www.coursera.org/specializations/machine-learning-introduction"
        },
        "golang": {
            "youtube": "🎥 https://youtu.be/YS4e4q9oBaU",
            "premium": "💎 https://www.udemy.com/course/go-the-complete-developers-guide/"
        },
        "angular": {
            "youtube": "🎥 https://youtu.be/3qBXWUpoPHo",
            "premium": "💎 https://www.udemy.com/course/the-complete-guide-to-angular-2/"
        },
        "vue.js": {
            "youtube": "🎥 https://youtu.be/FXpIoQ_rT_c",
            "premium": "💎 https://www.udemy.com/course/vuejs-2-the-complete-guide/"
        }
    }
    
    skill_lower = skill.lower()
    
    # Try real-time search first
    if SEARCH_AVAILABLE:
        try:
            youtube_link = search_youtube_courses(skill)
            premium_link = search_udemy_courses(skill) or search_coursera_courses(skill)
            
            return {
                "youtube": youtube_link,
                "premium": premium_link
            }
        except Exception as e:
            print(f"⚠️ Search failed for {skill}: {e}")
    
    # Fallback to curated direct links
    if skill_lower in fallback_resources:
        return fallback_resources[skill_lower]
    
    # Generic fallback with direct search URLs
    search_query = skill.replace(' ', '%20')
    youtube_query = skill.replace(' ', '+')
    
    return {
        "youtube": f"🎥 https://www.youtube.com/results?search_query=freeCodeCamp+{youtube_query}+full+course",
        "premium": f"💎 https://www.udemy.com/courses/search/?q={search_query}&sort=highest-rated"
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_learning_path(skill_gaps: list) -> str:
    """Generate personalized learning recommendations with direct clickable links"""
    if not skill_gaps:
        return "✅ You have all required skills!"
    
    path = "\n🎓 **Recommended Learning Path:**\n"
    
    for i, skill in enumerate(skill_gaps[:3], 1):
        resources = get_comprehensive_learning_resources(skill)
        
        path += f"\n**{i}. {skill.title()}**\n"
        
        # YouTube (Free) - Direct link
        if isinstance(resources, dict) and 'youtube' in resources:
            path += f"   FREE: {resources['youtube']}\n"
        
        # Premium (Udemy/Coursera) - Direct link
        if isinstance(resources, dict) and 'premium' in resources:
            path += f"   PREMIUM: {resources['premium']}\n"
    
    path += "\n💡 **Pro Tip:** Click the links above to start learning immediately!\n"
    
    return path

def create_recommendation_report(matches: list) -> str:
    """Create comprehensive recommendation report"""
    if not matches:
        return "No matching jobs found. Please update your profile or try different skills."
    
    # Sort by score
    matches.sort(key=lambda x: x.match_score, reverse=True)
    top_matches = matches[:5]
    
    report = "\n" + "="*70 + "\n"
    report += "🎯 **YOUR TOP JOB MATCHES**\n"
    report += "="*70 + "\n\n"
    
    for i, match in enumerate(top_matches, 1):
        report += f"**#{i} - {match.title}** at **{match.company}**\n"
        report += f"📊 Match Score: {match.match_score:.1f}%\n"
        report += f"💰 Salary: {match.salary_range}\n"
        report += f"📍 Location: {match.location}\n"
        report += f"🏠 Remote: {'Yes ✅' if match.remote else 'No ❌'}\n"
        report += f"🔗 Apply: {match.source_url}\n\n"
        
        if match.strengths:
            report += f"✅ **Your Strengths:**\n"
            report += f"   {', '.join(match.strengths[:5])}\n\n"
        
        if match.skill_gaps:
            report += f"⚠️  **Skills to Develop:**\n"
            report += f"   {', '.join(match.skill_gaps[:5])}\n"
            report += generate_learning_path(match.skill_gaps)
        
        report += "\n" + "-"*70 + "\n\n"
    
    # Overall recommendations
    avg_score = sum(m.match_score for m in matches) / len(matches)
    report += f"📈 **Overall Profile Strength:** {avg_score:.1f}%\n\n"
    
    if avg_score >= 80:
        report += "🌟 Excellent profile! Apply to these positions with confidence.\n"
    elif avg_score >= 60:
        report += "💪 Strong profile! Consider upskilling in gap areas to reach 80%+.\n"
    else:
        report += "📚 Focus on developing high-demand skills to improve match scores.\n"
    
    report += f"\n📊 **Statistics:**\n"
    report += f"   - Total jobs analyzed: {len(matches)}\n"
    report += f"   - Top 5 shown above\n"
    report += f"   - Average match score: {avg_score:.1f}%\n"
    report += f"   - Remote jobs: {sum(1 for m in matches if m.remote)}/{len(matches)}\n"
    
    report += "\n" + "="*70 + "\n"
    
    return report

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
    async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
        """Handle incoming chat messages"""
        ctx.logger.info(f"💬 Received chat message from {sender}")
        
        await ctx.send(
            sender,
            ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
        )
        
        if sender in candidate_recommendations:
            report = create_recommendation_report(candidate_recommendations[sender])
            response = create_text_chat(report)
            await ctx.send(sender, response)
            del candidate_recommendations[sender]
        else:
            welcome = create_text_chat(
                "👋 Welcome! Your job recommendations will appear here once processing is complete."
            )
            await ctx.send(sender, welcome)
    
    @chat_proto.on_message(ChatAcknowledgement)
    async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
        """Handle acknowledgements"""
        ctx.logger.info(f"✅ Message {msg.acknowledged_msg_id} acknowledged by {sender}")

# ============================================================================
# MAIN MESSAGE HANDLER
# ============================================================================

@recommender_agent.on_message(model=MatchScore)
async def aggregate_recommendations(ctx: Context, sender: str, msg: MatchScore):
    """Aggregate job scores and generate final recommendations"""
    
    ctx.logger.info("="*70)
    ctx.logger.info(f"📥 MATCH SCORE RECEIVED")
    ctx.logger.info("="*70)
    ctx.logger.info(f"Job: {msg.title} at {msg.company}")
    ctx.logger.info(f"Score: {msg.match_score:.1f}%")
    ctx.logger.info(f"Candidate: {msg.candidate_id}")
    ctx.logger.info(f"Apply Link: {msg.source_url[:50]}...")
    
    if msg.candidate_id not in candidate_recommendations:
        candidate_recommendations[msg.candidate_id] = []
    candidate_recommendations[msg.candidate_id].append(msg)
    
    num_recommendations = len(candidate_recommendations[msg.candidate_id])
    ctx.logger.info(f"📊 Total recommendations collected: {num_recommendations}")
    
    if num_recommendations >= 5:
        ctx.logger.info("\n" + "="*70)
        ctx.logger.info("✅ GENERATING FINAL REPORT WITH REAL-TIME COURSE SEARCH")
        ctx.logger.info("="*70)
        
        report = create_recommendation_report(
            candidate_recommendations[msg.candidate_id]
        )
        
        ctx.logger.info("\n" + report)
        
        if CHAT_AVAILABLE:
            try:
                response = create_text_chat(report)
                await ctx.send(msg.candidate_id, response)
                ctx.logger.info("📤 Report sent to candidate via Chat Protocol")
            except Exception as e:
                ctx.logger.warning(f"⚠️ Could not send via Chat Protocol: {e}")

        try:
            await ctx.send(
                TEST_AGENT_ADDRESS,
                RecommendationReport(
                    candidate_id=msg.candidate_id,
                    report=report,
                    top_matches=[m.job_id for m in candidate_recommendations[msg.candidate_id][:5]]
                )
            )
            ctx.logger.info(f"📤 Report also sent to test agent: {TEST_AGENT_ADDRESS}")
        except Exception as e:
            ctx.logger.warning(f"⚠️ Could not send report to test agent: {e}")
        
        del candidate_recommendations[msg.candidate_id]
        ctx.logger.info("🧹 Recommendations cleared for candidate")
        ctx.logger.info("="*70 + "\n")
    else:
        ctx.logger.info(f"⏳ Waiting for more recommendations ({num_recommendations}/5)")
        ctx.logger.info("="*70 + "\n")

# ============================================================================
# STARTUP HANDLER
# ============================================================================

@recommender_agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize agent on startup"""
    ctx.logger.info("="*70)
    ctx.logger.info("🚀 RECOMMENDATION AGENT STARTED")
    ctx.logger.info("="*70)
    ctx.logger.info(f"📍 Agent Address: {ctx.agent.address}")
    ctx.logger.info(f"🔌 Port: 8005")
    ctx.logger.info(f"💬 Chat Protocol: {'ENABLED' if CHAT_AVAILABLE else 'DISABLED'}")
    ctx.logger.info(f"🔍 Real-time Search: {'ENABLED' if SEARCH_AVAILABLE else 'DISABLED'}")
    ctx.logger.info(f"🎯 Minimum recommendations before report: 5")
    ctx.logger.info("="*70 + "\n")

# ============================================================================
# INCLUDE CHAT PROTOCOL & RUN
# ============================================================================

if CHAT_AVAILABLE:
    try:
        recommender_agent.include(chat_proto, publish_manifest=True)
        print("✅ Chat Protocol enabled successfully")
    except Exception as e:
        print(f"⚠️  Could not enable Chat Protocol: {e}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AGENT 5: RECOMMENDATION AGENT (Real-Time Course Search)")
    print("="*70)
    print(f"🔍 LangChain Search: {'AVAILABLE' if SEARCH_AVAILABLE else 'UNAVAILABLE'}")
    print("\n🔧 Starting agent...")
    print("="*70 + "\n")
    
    recommender_agent.run()