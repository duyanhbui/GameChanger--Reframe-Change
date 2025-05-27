"""
Mental Models for Change Management Assessment
Maps response combinations to 16 distinct mental models
"""

# Mental model definitions with detailed information
MENTAL_MODELS = {
    "strategic_analyst": {
        "name": "Strategic Analyst",
        "description": "You approach change through careful analysis and strategic planning.",
        "strengths": [
            "Excellent at risk assessment and mitigation",
            "Data-driven decision making",
            "Long-term strategic thinking",
            "Process optimization expertise"
        ],
        "challenges": [
            "May over-analyze and delay action",
            "Could miss emotional aspects of change",
            "Might resist rapid pivots when data is incomplete"
        ],
        "recommendations": [
            "Balance analysis with action - set decision deadlines",
            "Include stakeholder feedback in your data collection",
            "Practice scenario planning for uncertain situations",
            "Develop emotional intelligence alongside analytical skills"
        ]
    },
    "innovation_catalyst": {
        "name": "Innovation Catalyst",
        "description": "You thrive on transformation and see change as an opportunity for breakthrough innovation.",
        "strengths": [
            "Visionary thinking and creative problem-solving",
            "Comfortable with uncertainty and ambiguity",
            "Inspires others to embrace new possibilities",
            "Quick to identify emerging opportunities"
        ],
        "challenges": [
            "May move too fast for others to follow",
            "Could underestimate implementation challenges",
            "Might overlook the value of existing processes"
        ],
        "recommendations": [
            "Build in checkpoints to ensure team alignment",
            "Partner with detail-oriented colleagues for execution",
            "Communicate the 'why' behind changes clearly",
            "Celebrate small wins to maintain momentum"
        ]
    },
    "collaborative_facilitator": {
        "name": "Collaborative Facilitator",
        "description": "You excel at bringing people together and ensuring everyone's voice is heard during change.",
        "strengths": [
            "Strong relationship building and communication",
            "Skilled at conflict resolution and consensus building",
            "High emotional intelligence and empathy",
            "Creates inclusive environments for change"
        ],
        "challenges": [
            "Decision-making may be slower due to consultation needs",
            "Could struggle with unpopular but necessary changes",
            "May avoid difficult conversations that are needed"
        ],
        "recommendations": [
            "Set clear timelines for consultation and decision phases",
            "Develop skills for having tough conversations",
            "Learn to balance individual needs with organizational goals",
            "Use your influence to help others see the bigger picture"
        ]
    },
    "results_optimizer": {
        "name": "Results Optimizer",
        "description": "You focus on measurable outcomes and ensuring change delivers tangible business value.",
        "strengths": [
            "Clear focus on ROI and business impact",
            "Excellent at setting and tracking KPIs",
            "Drives accountability and performance",
            "Skilled at resource allocation and efficiency"
        ],
        "challenges": [
            "May prioritize metrics over people considerations",
            "Could miss intangible benefits of change",
            "Might push too hard for immediate results"
        ],
        "recommendations": [
            "Include people-focused metrics in your measurements",
            "Allow time for change adoption and learning curves",
            "Communicate the human value behind the numbers",
            "Balance short-term wins with long-term sustainability"
        ]
    },
    "stability_guardian": {
        "name": "Stability Guardian",
        "description": "You value consistency and work to preserve what works while carefully managing change.",
        "strengths": [
            "Deep institutional knowledge and experience",
            "Risk-aware and thorough in planning",
            "Protects valuable existing processes and culture",
            "Provides stability during turbulent times"
        ],
        "challenges": [
            "May resist necessary changes too strongly",
            "Could be seen as a blocker to innovation",
            "Might focus too much on potential problems"
        ],
        "recommendations": [
            "Practice identifying which traditions truly add value",
            "Become a bridge between old and new approaches",
            "Share your knowledge to help others avoid past mistakes",
            "Focus on how change can strengthen core values"
        ]
    },
    "adaptive_navigator": {
        "name": "Adaptive Navigator",
        "description": "You're flexible and intuitive, helping others navigate change with confidence.",
        "strengths": [
            "Highly adaptable to changing circumstances",
            "Strong intuition for reading situations",
            "Helps others feel comfortable with uncertainty",
            "Balances multiple perspectives effectively"
        ],
        "challenges": [
            "May lack consistency in approach",
            "Could struggle to provide clear direction",
            "Might avoid making firm commitments"
        ],
        "recommendations": [
            "Develop a personal framework for decision-making",
            "Practice articulating your intuitive insights",
            "Set clear boundaries and expectations",
            "Use your adaptability to model resilience for others"
        ]
    },
    "relationship_builder": {
        "name": "Relationship Builder",
        "description": "You prioritize human connections and ensure change strengthens rather than damages relationships.",
        "strengths": [
            "Exceptional interpersonal skills",
            "Builds trust and psychological safety",
            "Understands emotional dynamics of change",
            "Creates strong networks and alliances"
        ],
        "challenges": [
            "May avoid necessary but difficult decisions",
            "Could prioritize harmony over progress",
            "Might take team conflicts personally"
        ],
        "recommendations": [
            "Learn to have caring but direct conversations",
            "Practice separating relationships from business decisions",
            "Use your influence to advocate for necessary changes",
            "Help others see how change can improve relationships"
        ]
    },
    "performance_driver": {
        "name": "Performance Driver",
        "description": "You're motivated by achievement and push for changes that deliver superior results.",
        "strengths": [
            "Strong drive for continuous improvement",
            "Motivates others to exceed expectations",
            "Results-oriented and goal-focused",
            "Competitive advantage mindset"
        ],
        "challenges": [
            "May push too hard and burn out team members",
            "Could overlook the importance of process",
            "Might underestimate time needed for adoption"
        ],
        "recommendations": [
            "Balance achievement drive with team sustainability",
            "Celebrate progress, not just final outcomes",
            "Include team development in your performance metrics",
            "Practice patience with different learning speeds"
        ]
    },
    "methodical_planner": {
        "name": "Methodical Planner",
        "description": "You bring structure and systematic thinking to change initiatives.",
        "strengths": [
            "Excellent project management and organization",
            "Thorough risk assessment and mitigation",
            "Clear communication of steps and expectations",
            "Reliable execution and follow-through"
        ],
        "challenges": [
            "May be inflexible when plans need to change",
            "Could get bogged down in planning details",
            "Might resist agile or iterative approaches"
        ],
        "recommendations": [
            "Build flexibility checkpoints into your plans",
            "Practice rapid prototyping and testing",
            "Learn to embrace 'good enough' to start",
            "Use your planning skills to prepare for multiple scenarios"
        ]
    },
    "creative_explorer": {
        "name": "Creative Explorer",
        "description": "You bring fresh perspectives and innovative solutions to change challenges.",
        "strengths": [
            "Generates novel ideas and approaches",
            "Sees connections others might miss",
            "Energizes teams with enthusiasm for new possibilities",
            "Comfortable with experimentation and iteration"
        ],
        "challenges": [
            "May struggle with routine implementation tasks",
            "Could jump to new ideas before finishing current ones",
            "Might not adequately consider practical constraints"
        ],
        "recommendations": [
            "Partner with implementation-focused colleagues",
            "Set up systems to capture and evaluate ideas",
            "Practice translating creative concepts into actionable plans",
            "Use your creativity to solve implementation challenges"
        ]
    },
    "team_harmonizer": {
        "name": "Team Harmonizer",
        "description": "You focus on maintaining team cohesion and morale throughout change processes.",
        "strengths": [
            "Sensitive to team dynamics and emotional needs",
            "Skilled at resolving conflicts and building consensus",
            "Creates inclusive and supportive environments",
            "Maintains team morale during difficult transitions"
        ],
        "challenges": [
            "May avoid necessary confrontations",
            "Could slow down decisions to maintain harmony",
            "Might take team resistance personally"
        ],
        "recommendations": [
            "Learn to frame difficult messages with care but clarity",
            "Practice distinguishing between healthy and unhealthy conflict",
            "Use your skills to help teams process change emotions",
            "Advocate for team needs while supporting organizational goals"
        ]
    },
    "efficiency_expert": {
        "name": "Efficiency Expert",
        "description": "You excel at streamlining processes and maximizing resource utilization during change.",
        "strengths": [
            "Identifies waste and optimization opportunities",
            "Skilled at process improvement and automation",
            "Maximizes ROI on change investments",
            "Creates sustainable and scalable solutions"
        ],
        "challenges": [
            "May prioritize efficiency over effectiveness",
            "Could overlook human factors in optimization",
            "Might resist changes that don't show immediate efficiency gains"
        ],
        "recommendations": [
            "Include human satisfaction in your efficiency metrics",
            "Consider long-term effectiveness alongside short-term efficiency",
            "Help others understand the value of process improvements",
            "Balance automation with maintaining human skills"
        ]
    },
    "tradition_keeper": {
        "name": "Tradition Keeper",
        "description": "You preserve valuable organizational culture and knowledge while adapting to necessary changes.",
        "strengths": [
            "Deep understanding of organizational history",
            "Protects valuable cultural elements",
            "Provides continuity and stability",
            "Helps others learn from past experiences"
        ],
        "challenges": [
            "May resist beneficial changes due to attachment to past",
            "Could be seen as opposing necessary progress",
            "Might struggle to see value in new approaches"
        ],
        "recommendations": [
            "Identify which traditions truly serve current needs",
            "Help others understand the wisdom behind existing practices",
            "Find ways to honor the past while embracing the future",
            "Become a cultural translator between old and new"
        ]
    },
    "possibility_seeker": {
        "name": "Possibility Seeker",
        "description": "You're energized by potential and help others see opportunities in change.",
        "strengths": [
            "Optimistic and forward-thinking mindset",
            "Inspires others to embrace new opportunities",
            "Comfortable with ambiguity and uncertainty",
            "Generates enthusiasm for change initiatives"
        ],
        "challenges": [
            "May underestimate implementation challenges",
            "Could overlook risks and potential downsides",
            "Might lose interest once the initial excitement fades"
        ],
        "recommendations": [
            "Partner with detail-oriented planners for execution",
            "Practice realistic timeline and resource planning",
            "Stay engaged through implementation phases",
            "Use your enthusiasm to help others through difficult periods"
        ]
    },
    "consensus_builder": {
        "name": "Consensus Builder",
        "description": "You excel at bringing diverse stakeholders together to support change initiatives.",
        "strengths": [
            "Skilled at managing multiple stakeholder perspectives",
            "Builds broad support for change initiatives",
            "Excellent negotiation and diplomacy skills",
            "Creates win-win solutions for competing interests"
        ],
        "challenges": [
            "May compromise too much to achieve consensus",
            "Could slow down urgent decisions",
            "Might avoid taking stands on controversial issues"
        ],
        "recommendations": [
            "Learn when consensus is valuable vs. when leadership is needed",
            "Practice making decisions with incomplete agreement",
            "Use your skills to build coalitions for necessary changes",
            "Help stakeholders understand when compromise serves the greater good"
        ]
    },
    "impact_maximizer": {
        "name": "Impact Maximizer",
        "description": "You focus on ensuring change creates the greatest possible positive impact.",
        "strengths": [
            "Strong focus on outcomes and value creation",
            "Skilled at prioritizing high-impact initiatives",
            "Motivates others by connecting work to purpose",
            "Balances multiple success metrics effectively"
        ],
        "challenges": [
            "May try to do too much at once",
            "Could overlook the importance of small improvements",
            "Might become frustrated with incremental progress"
        ],
        "recommendations": [
            "Practice sequencing initiatives for maximum cumulative impact",
            "Celebrate small wins that contribute to larger goals",
            "Help others see how their contributions create impact",
            "Balance breadth of impact with depth of execution"
        ]
    }
}

def calculate_mental_model(q1, q2, q3):
    """
    Calculate mental model based on responses to three questions.
    Each question has 4 options (A, B, C, D) representing different approaches:
    A = Stability/Process-focused
    B = Innovation/Vision-focused  
    C = People/Relationship-focused
    D = Results/Performance-focused
    """
    
    # Create a response pattern
    pattern = q1 + q2 + q3
    
    # Mapping of response patterns to mental models
    pattern_map = {
        'AAA': 'tradition_keeper',
        'AAB': 'possibility_seeker', 
        'AAC': 'relationship_builder',
        'AAD': 'methodical_planner',
        'ABA': 'stability_guardian',
        'ABB': 'adaptive_navigator',
        'ABC': 'team_harmonizer',
        'ABD': 'strategic_analyst',
        'ACA': 'consensus_builder',
        'ACB': 'collaborative_facilitator',
        'ACC': 'relationship_builder',
        'ACD': 'team_harmonizer',
        'ADA': 'methodical_planner',
        'ADB': 'efficiency_expert',
        'ADC': 'performance_driver',
        'ADD': 'results_optimizer',
        'BAA': 'creative_explorer',
        'BAB': 'innovation_catalyst',
        'BAC': 'possibility_seeker',
        'BAD': 'strategic_analyst',
        'BBA': 'adaptive_navigator',
        'BBB': 'innovation_catalyst',
        'BBC': 'creative_explorer',
        'BBD': 'possibility_seeker',
        'BCA': 'collaborative_facilitator',
        'BCB': 'adaptive_navigator',
        'BCC': 'team_harmonizer',
        'BCD': 'consensus_builder',
        'BDA': 'strategic_analyst',
        'BDB': 'innovation_catalyst',
        'BDC': 'impact_maximizer',
        'BDD': 'performance_driver',
        'CAA': 'relationship_builder',
        'CAB': 'collaborative_facilitator',
        'CAC': 'team_harmonizer',
        'CAD': 'consensus_builder',
        'CBA': 'adaptive_navigator',
        'CBB': 'creative_explorer',
        'CBC': 'collaborative_facilitator',
        'CBD': 'impact_maximizer',
        'CCA': 'consensus_builder',
        'CCB': 'team_harmonizer',
        'CCC': 'relationship_builder',
        'CCD': 'collaborative_facilitator',
        'CDA': 'strategic_analyst',
        'CDB': 'impact_maximizer',
        'CDC': 'performance_driver',
        'CDD': 'results_optimizer',
        'DAA': 'efficiency_expert',
        'DAB': 'strategic_analyst',
        'DAC': 'performance_driver',
        'DAD': 'results_optimizer',
        'DBA': 'methodical_planner',
        'DBB': 'possibility_seeker',
        'DBC': 'impact_maximizer',
        'DBD': 'performance_driver',
        'DCA': 'results_optimizer',
        'DCB': 'impact_maximizer',
        'DCC': 'performance_driver',
        'DCD': 'results_optimizer',
        'DDA': 'efficiency_expert',
        'DDB': 'performance_driver',
        'DDC': 'results_optimizer',
        'DDD': 'results_optimizer'
    }
    
    return pattern_map.get(pattern, 'adaptive_navigator')  # Default fallback

def get_mental_model_data(model_id):
    """Get the complete data for a specific mental model"""
    return MENTAL_MODELS.get(model_id, MENTAL_MODELS['adaptive_navigator'])
