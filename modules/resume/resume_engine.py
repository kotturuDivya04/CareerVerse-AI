# =============================================================================
# modules/resume/resume_engine.py  —  CareerVerse AI
# ATS Resume Scoring Engine
#
# Workflow:
#   1. Extract skills from resume text via keyword matching
#   2. Compare against role-specific required skills database
#   3. Score each ATS section with the defined weight distribution
#   4. Build strengths and suggestions lists
#   5. Return structured result dict (shape app.py + resume.js expect)
#
# ATS Scoring weights:
#   Projects       30%
#   Skills         25%
#   Experience     20%
#   Role Match     15%
#   Achievements    5%
#   Certifications  5%
# =============================================================================

from __future__ import annotations
import re

# =============================================================================
# ROLE SKILL DATABASE
# Each role maps to: required_skills (must-have) + bonus_skills (nice-to-have)
# =============================================================================

ROLE_SKILLS: dict[str, dict[str, list[str]]] = {
    'Data Analyst': {
        'required': [
            'sql', 'excel', 'python', 'tableau', 'power bi', 'data visualization',
            'statistics', 'data analysis', 'pandas', 'numpy', 'reporting',
        ],
        'bonus': [
            'r', 'matplotlib', 'seaborn', 'google analytics', 'looker',
            'data cleaning', 'etl', 'business intelligence', 'pivot tables',
        ],
    },
    'Business Analyst': {
        'required': [
            'sql', 'excel', 'requirements gathering', 'data analysis', 'reporting',
            'stakeholder management', 'process mapping', 'documentation', 'jira',
        ],
        'bonus': [
            'power bi', 'tableau', 'python', 'agile', 'scrum', 'uml', 'visio',
        ],
    },
    'Data Scientist': {
        'required': [
            'python', 'machine learning', 'statistics', 'sql', 'pandas', 'numpy',
            'scikit-learn', 'data visualization', 'model evaluation', 'feature engineering',
        ],
        'bonus': [
            'deep learning', 'tensorflow', 'pytorch', 'keras', 'nlp',
            'computer vision', 'spark', 'mlflow', 'r', 'jupyter',
        ],
    },
    'Machine Learning Engineer': {
        'required': [
            'python', 'machine learning', 'tensorflow', 'pytorch', 'scikit-learn',
            'deep learning', 'model deployment', 'docker', 'git', 'api',
        ],
        'bonus': [
            'kubernetes', 'mlops', 'aws', 'gcp', 'azure', 'fastapi', 'spark',
            'cuda', 'transformer', 'bert', 'llm', 'mlflow',
        ],
    },
    'Data Engineer': {
        'required': [
            'python', 'sql', 'etl', 'spark', 'airflow', 'data pipeline',
            'aws', 'data warehouse', 'kafka', 'hadoop',
        ],
        'bonus': [
            'dbt', 'snowflake', 'bigquery', 'redshift', 'terraform',
            'docker', 'kubernetes', 'scala', 'databricks',
        ],
    },
    'Python Developer': {
        'required': [
            'python', 'django', 'flask', 'rest api', 'sql', 'git',
            'oop', 'unit testing', 'linux', 'json',
        ],
        'bonus': [
            'fastapi', 'celery', 'redis', 'postgresql', 'docker',
            'aws', 'microservices', 'pytest', 'asyncio',
        ],
    },
    'Backend Developer': {
        'required': [
            'python', 'sql', 'rest api', 'git', 'docker', 'linux',
            'database design', 'authentication', 'oop', 'json',
        ],
        'bonus': [
            'node.js', 'java', 'go', 'redis', 'rabbitmq', 'microservices',
            'kubernetes', 'aws', 'postgresql', 'mongodb',
        ],
    },
    'Frontend Developer': {
        'required': [
            'html', 'css', 'javascript', 'react', 'responsive design',
            'git', 'rest api', 'ui/ux', 'typescript', 'webpack',
        ],
        'bonus': [
            'vue', 'angular', 'nextjs', 'tailwind', 'sass', 'redux',
            'testing', 'accessibility', 'figma', 'graphql',
        ],
    },
    'Full Stack Developer': {
        'required': [
            'html', 'css', 'javascript', 'python', 'sql', 'react',
            'rest api', 'git', 'docker', 'database design',
        ],
        'bonus': [
            'node.js', 'typescript', 'nextjs', 'postgresql', 'mongodb',
            'redis', 'aws', 'ci/cd', 'kubernetes', 'graphql',
        ],
    },
}

# Fallback for any role not in the database
_DEFAULT_REQUIRED = [
    'python', 'sql', 'git', 'communication', 'problem solving',
    'data analysis', 'documentation', 'teamwork',
]
_DEFAULT_BONUS = ['docker', 'aws', 'agile', 'linux', 'api']

# =============================================================================
# SECTION DETECTION PATTERNS
# =============================================================================

_SECTION_PATTERNS = {
    'projects':        r'\b(project|projects|personal project|academic project|capstone|built|developed|implemented)\b',
    'experience':      r'\b(experience|internship|intern|worked at|work experience|employment|job|position|role)\b',
    'achievements':    r'\b(achievement|award|winner|rank|prize|honor|honour|distinction|scholarship|certificate of merit)\b',
    'certifications':  r'\b(certification|certified|certificate|credential|license|accreditation|coursera|udemy|aws certified|google certified|microsoft certified)\b',
}


# =============================================================================
# HELPERS
# =============================================================================

def _extract_skills_from_text(text: str, skill_list: list[str]) -> list[str]:
    """Return skills from skill_list that appear in the resume text (case-insensitive)."""
    text_lower = text.lower()
    found = []
    for skill in skill_list:
        # Use word-boundary-aware search to avoid 'r' matching 'or', etc.
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill.lower()) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def _section_present(text: str, section: str) -> bool:
    pattern = _SECTION_PATTERNS.get(section, '')
    if not pattern:
        return False
    return bool(re.search(pattern, text, re.IGNORECASE))


def _count_section_depth(text: str, section: str) -> int:
    """
    Rough count of how substantive a section is.
    Returns 0 (absent), 1 (shallow), or 2 (detailed).
    """
    pattern = _SECTION_PATTERNS.get(section, '')
    if not pattern:
        return 0
    matches = re.findall(pattern, text, re.IGNORECASE)
    if len(matches) == 0:
        return 0
    if len(matches) <= 2:
        return 1
    return 2


def _build_strengths(
    skills_found: list[str],
    section_scores: dict[str, float],
    ats_score: float,
    role: str,
) -> list[str]:
    strengths = []
    if len(skills_found) >= 8:
        strengths.append(f'Strong skill alignment with {len(skills_found)} role-relevant skills identified.')
    elif len(skills_found) >= 5:
        strengths.append(f'{len(skills_found)} required skills found — solid foundation for the {role} role.')

    if section_scores.get('projects', 0) >= 24:
        strengths.append('Well-documented project portfolio with strong implementation details.')
    if section_scores.get('experience', 0) >= 16:
        strengths.append('Relevant work or internship experience clearly presented.')
    if section_scores.get('certifications', 0) >= 4:
        strengths.append('Certifications listed — demonstrates commitment to continuous learning.')
    if ats_score >= 80:
        strengths.append('ATS-friendly resume format with good keyword density.')

    if not strengths:
        strengths.append('Resume submitted for analysis — add more relevant keywords to improve scoring.')

    return strengths


def _build_suggestions(
    missing_skills: list[str],
    section_scores: dict[str, float],
    role: str,
) -> list[str]:
    suggestions = []

    if missing_skills:
        top_missing = missing_skills[:3]
        suggestions.append(
            f'Add missing key skills to your resume: {", ".join(top_missing)}.'
        )

    if section_scores.get('projects', 0) < 18:
        suggestions.append(
            'Expand your Projects section — include 2–3 end-to-end projects with quantifiable outcomes.'
        )
    if section_scores.get('achievements', 0) < 3:
        suggestions.append(
            'Add measurable achievements (e.g. "Improved accuracy by 15%") to stand out to ATS systems.'
        )
    if section_scores.get('certifications', 0) < 3:
        suggestions.append(
            f'Consider adding role-relevant certifications for {role} to boost your credibility.'
        )
    if section_scores.get('experience', 0) < 10:
        suggestions.append(
            'Strengthen your Experience section with specific technologies used and impact delivered.'
        )

    suggestions.append('Include your LinkedIn profile URL in the contact section.')

    return suggestions


# =============================================================================
# MAIN ENGINE
# =============================================================================

def analyze_resume(resume_text: str, role: str) -> dict:
    """
    Score a resume against a target role using keyword matching and
    section detection.

    Returns:
        {
            "ats_score":        float,          # 0–100
            "role_match_score": float,          # 0–100
            "skills_found":     [str, ...],
            "missing_skills":   [str, ...],
            "strengths":        [str, ...],
            "suggestions":      [str, ...],
            "section_scores":   {
                "projects":        float,        # max 30
                "skills":          float,        # max 25
                "experience":      float,        # max 20
                "role_match":      float,        # max 15
                "achievements":    float,        # max 5
                "certifications":  float,        # max 5
            },
        }
    """
    role_data     = ROLE_SKILLS.get(role, {})
    required      = role_data.get('required', _DEFAULT_REQUIRED)
    bonus         = role_data.get('bonus',    _DEFAULT_BONUS)
    all_skills    = list(dict.fromkeys(required + bonus))   # preserve order, deduplicate

    skills_found   = _extract_skills_from_text(resume_text, all_skills)
    req_found      = [s for s in skills_found if s in required]
    missing_skills = [s for s in required if s not in skills_found]

    # ---- Section scores ----
    # Skills (25 pts): based on % of required skills found
    req_ratio   = len(req_found) / len(required) if required else 0
    skill_score = round(req_ratio * 25, 1)

    # Projects (30 pts)
    proj_depth  = _count_section_depth(resume_text, 'projects')
    proj_score  = {0: 0, 1: 16, 2: 28}.get(proj_depth, 0)
    # Add partial credit for having many skills (proxy for project richness)
    if len(skills_found) >= 6:
        proj_score = min(30, proj_score + 2)

    # Experience (20 pts)
    exp_depth  = _count_section_depth(resume_text, 'experience')
    exp_score  = {0: 0, 1: 10, 2: 18}.get(exp_depth, 0)
    if 'internship' in resume_text.lower() or 'intern' in resume_text.lower():
        exp_score = min(20, exp_score + 2)

    # Role match (15 pts): proportion of bonus skills found on top of required
    bonus_found = [s for s in skills_found if s in bonus]
    role_ratio  = (len(req_found) * 2 + len(bonus_found)) / (len(required) * 2 + len(bonus)) \
                  if (required or bonus) else 0
    role_score  = round(role_ratio * 15, 1)

    # Achievements (5 pts)
    ach_depth  = _count_section_depth(resume_text, 'achievements')
    ach_score  = {0: 0, 1: 3, 2: 5}.get(ach_depth, 0)

    # Certifications (5 pts)
    cert_depth = _count_section_depth(resume_text, 'certifications')
    cert_score = {0: 0, 1: 3, 2: 5}.get(cert_depth, 0)

    section_scores = {
        'projects':       proj_score,
        'skills':         skill_score,
        'experience':     exp_score,
        'role_match':     role_score,
        'achievements':   ach_score,
        'certifications': cert_score,
    }

    ats_score        = round(sum(section_scores.values()), 1)
    ats_score        = min(100.0, ats_score)
    role_match_score = round(role_ratio * 100, 1)

    strengths   = _build_strengths(skills_found, section_scores, ats_score, role)
    suggestions = _build_suggestions(missing_skills, section_scores, role)

    return {
        'ats_score':        ats_score,
        'role_match_score': role_match_score,
        'skills_found':     skills_found,
        'missing_skills':   missing_skills,
        'strengths':        strengths,
        'suggestions':      suggestions,
        'section_scores':   section_scores,
    }