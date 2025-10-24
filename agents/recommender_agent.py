"""
Agent 5: Recommendation Agent (FIXED)
Aggregates job scores and sends final recommendations
Chat Protocol enabled for ASI:One integration
"""

from datetime import datetime
from uuid import uuid4
from uagents import Agent, Context, Model, Protocol
from config.agent_addresses import TEST_AGENT_ADDRESS
from agents.models import RecommendationReport

# Try to import chat protocol components
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
# HELPER FUNCTIONS
# ============================================================================

def generate_learning_path(skill_gaps: list) -> str:
    """Generate personalized learning recommendations"""
    if not skill_gaps:
        return "✅ You have all required skills!"
    
    learning_resources = {
        "kubernetes": "📚 Kubernetes.io tutorials, CKAD certification",
        "tensorflow": "📚 TensorFlow.org courses, Deep Learning Specialization",
        "react": "📚 React.dev documentation, Full Stack Open course",
        "aws": "📚 AWS Training, Solutions Architect certification",
        "typescript": "📚 TypeScript Handbook, Execute Program",
        "docker": "📚 Docker Documentation, Docker Certified Associate",
        "django": "📚 Django Documentation, Two Scoops of Django book",
        "node.js": "📚 Node.js Documentation, You Don't Know Node",
        "mongodb": "📚 MongoDB University, MongoDB Certified Developer",
        "golang": "📚 Go by Example, A Tour of Go",
        "rust": "📚 The Rust Book, Rustlings exercises",
        "graphql": "📚 GraphQL.org tutorials, How to GraphQL",
        "redis": "📚 Redis University, Redis Certified Developer",
    }
    
    path = "\n🎓 **Recommended Learning Path:**\n"
    for i, skill in enumerate(skill_gaps[:3], 1):
        resource = learning_resources.get(
            skill.lower(), 
            f"📚 Search for {skill} courses on Coursera/Udemy"
        )
        path += f"{i}. **{skill.title()}**: {resource}\n"
    
    return path

def create_recommendation_report(matches: list) -> str:
    """Create comprehensive recommendation report"""
    if not matches:
        return "No matching jobs found. Please update your profile or try different skills."
    
    # Sort by score
    matches.sort(key=lambda x: x.match_score, reverse=True)
    top_matches = matches[:5]  # Show top 5 instead of 3
    
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
        
        # Send acknowledgement
        await ctx.send(
            sender,
            ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
        )
        
        # Check if we have recommendations for this user
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
    
    # Store recommendation
    if msg.candidate_id not in candidate_recommendations:
        candidate_recommendations[msg.candidate_id] = []
    candidate_recommendations[msg.candidate_id].append(msg)
    
    num_recommendations = len(candidate_recommendations[msg.candidate_id])
    ctx.logger.info(f"📊 Total recommendations collected: {num_recommendations}")
    
    # After receiving 5+ recommendations, generate report
    # (Changed from 3 to 5 to match optimized job discovery limit)
    if num_recommendations >= 5:
        ctx.logger.info("\n" + "="*70)
        ctx.logger.info("✅ GENERATING FINAL REPORT")
        ctx.logger.info("="*70)
        
        # Generate comprehensive report
        report = create_recommendation_report(
            candidate_recommendations[msg.candidate_id]
        )
        
        # Log the report
        ctx.logger.info("\n" + report)
        
        # Try Chat Protocol first (for ASI:One)
        if CHAT_AVAILABLE:
            try:
                response = create_text_chat(report)
                await ctx.send(msg.candidate_id, response)
                ctx.logger.info("📤 Report sent to candidate via Chat Protocol")
            except Exception as e:
                ctx.logger.warning(f"⚠️ Could not send via Chat Protocol: {e}")

        # Always send to test agent (local)
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
        
        # Clear stored recommendations
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
    ctx.logger.info(f"🎯 Minimum recommendations before report: 5")
    ctx.logger.info(f"🎯 Ready to aggregate recommendations!")
    ctx.logger.info("="*70 + "\n")

# ============================================================================
# INCLUDE CHAT PROTOCOL (if available) & RUN
# ============================================================================

if CHAT_AVAILABLE:
    try:
        recommender_agent.include(chat_proto, publish_manifest=True)
        print("✅ Chat Protocol enabled successfully")
    except Exception as e:
        print(f"⚠️  Could not enable Chat Protocol: {e}")
        print("   Agent will run in basic mode")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("AGENT 5: RECOMMENDATION AGENT")
    print("="*70)
    print("\n🔧 Starting agent...")
    print("="*70 + "\n")
    
    recommender_agent.run()