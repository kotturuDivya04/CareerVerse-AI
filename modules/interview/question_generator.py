# =============================================================================
# modules/interview/question_generator.py  —  CareerVerse AI
# Interview Question Generator
#
# Generates 4 categories of interview questions personalised to the
# candidate's resume text and target role:
#   - Technical    (12 questions) — role-specific depth questions
#   - HR           (10 questions) — standard behavioural/fit questions
#   - Project      (10 questions) — resume project deep-dives
#   - Behavioral   ( 8 questions) — STAR-format situational questions
#
# Approach:
#   1. Extract skills, technologies, and project hints from resume text
#   2. Select role-specific technical questions from the question bank
#      and personalise them with detected skills/technologies
#   3. HR and Behavioral questions are partially personalised using
#      the detected role and experience signals
#   4. Project questions are built from resume project mentions
#
# No external AI API is called — all questions are generated from the
# structured question bank below, personalised via keyword injection.
# This keeps the module fast, offline-capable, and deterministic.
# =============================================================================

from __future__ import annotations
import re
import random


# =============================================================================
# ROLE-SPECIFIC TECHNICAL QUESTION BANKS
# Each role has a pool of 20+ questions; 12 are selected per run.
# {skill} placeholders are replaced with detected resume skills.
# =============================================================================

TECHNICAL_BANK: dict[str, list[str]] = {
    'Data Analyst': [
        'Explain the difference between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN in SQL with examples.',
        'How would you handle missing values in a large dataset before analysis?',
        'What is the difference between a measure and a dimension in data visualization tools like Tableau or Power BI?',
        'Walk me through how you would design a dashboard for tracking weekly sales performance.',
        'Explain the difference between correlation and causation with a real-world example.',
        'How do you validate the accuracy of a report before presenting it to stakeholders?',
        'What is data normalization, and when would you choose not to normalize data?',
        'Describe a situation where you had to clean a messy dataset. What steps did you take?',
        'What are window functions in SQL? Give an example using RANK() or ROW_NUMBER().',
        'How would you identify and handle outliers in a dataset?',
        'Explain the ETL process. What tools have you used for data extraction and transformation?',
        'What is the difference between OLAP and OLTP systems?',
        'How do you choose the right chart type for a given dataset and audience?',
        'Explain cohort analysis and when you would use it.',
        'What is a pivot table, and how does it help in data summarization?',
        'How would you measure the impact of a marketing campaign using data?',
        'Describe how you would build an automated reporting pipeline.',
        'What is A/B testing, and how do you interpret its results statistically?',
        'Explain what a KPI is and give examples of KPIs for an e-commerce business.',
        'How would you explain a complex data insight to a non-technical stakeholder?',
    ],
    'Data Scientist': [
        'Explain the bias-variance tradeoff and how it affects model performance.',
        'Walk me through how you would approach a binary classification problem end-to-end.',
        'What is cross-validation, and why is it important? Explain k-fold cross-validation.',
        'How do you handle class imbalance in a dataset?',
        'Explain the difference between bagging and boosting ensemble methods.',
        'What is regularization? Explain L1 (Lasso) and L2 (Ridge) regularization.',
        'How does a Random Forest decide which feature to split on at each node?',
        'Explain gradient descent. What are the differences between batch, mini-batch, and stochastic variants?',
        'What metrics would you use to evaluate a regression model vs. a classification model?',
        'How would you detect and handle multicollinearity in a linear regression model?',
        'Explain what precision, recall, and F1-score measure and when each is more important.',
        'How does Principal Component Analysis (PCA) work and when would you use it?',
        'What is the curse of dimensionality, and how do you address it?',
        'Explain how a Support Vector Machine (SVM) finds the optimal decision boundary.',
        'What is feature engineering? Give an example of a feature you created that improved model performance.',
        'How would you deploy a machine learning model to production?',
        'Explain what overfitting looks like and three techniques to prevent it.',
        'What is the difference between a generative model and a discriminative model?',
        'How do you interpret a confusion matrix?',
        'Explain the concept of transfer learning and when you would apply it.',
    ],
    'Machine Learning Engineer': [
        'What is the difference between model training and model inference? How do you optimise each?',
        'Explain how you would set up a CI/CD pipeline for a machine learning model.',
        'What is model drift, and how do you monitor and address it in production?',
        'How would you design a scalable feature store for a production ML system?',
        'Explain the differences between batch inference and real-time inference. When would you use each?',
        'What containerisation tools have you used for ML deployment, and what problems do they solve?',
        'How do you version control ML models and datasets?',
        'Explain how you would reduce the latency of a model serving endpoint.',
        'What is A/B testing in the context of ML model deployment?',
        'How does backpropagation work in a neural network?',
        'Explain the transformer architecture and the role of the attention mechanism.',
        'What is the difference between LSTM and GRU recurrent networks?',
        'How would you debug a model that performs well on validation data but poorly in production?',
        'What is quantization in deep learning, and why is it useful for deployment?',
        'Explain what MLOps is and the key components of an MLOps platform.',
        'How do you handle data preprocessing at scale for model training pipelines?',
        'What is the role of a message queue (like Kafka) in an ML pipeline?',
        'Explain how hyperparameter tuning works. What methods have you used?',
        'How would you explain model predictions to non-technical stakeholders using explainability tools?',
        'What is the difference between online learning and offline learning?',
    ],
    'Data Engineer': [
        'Explain the difference between a data lake, data warehouse, and data lakehouse.',
        'What is Apache Spark, and how does it differ from MapReduce?',
        'How would you design a scalable data ingestion pipeline for real-time streaming data?',
        'What is Apache Kafka, and what role does it play in a data architecture?',
        'Explain partitioning and bucketing in Spark/Hive. Why are they important for query performance?',
        'How do you ensure data quality in an ETL pipeline?',
        'What is dbt (data build tool), and how does it improve data transformation workflows?',
        'Explain the differences between row-based and columnar storage formats (e.g. Parquet vs CSV).',
        'How would you handle late-arriving data in a streaming pipeline?',
        'What is the difference between idempotent and non-idempotent pipeline operations?',
        'How do you optimise a slow SQL query on a large table?',
        'Explain change data capture (CDC) and how it is used in data pipelines.',
        'What are the trade-offs between using a managed cloud data warehouse vs. a self-hosted solution?',
        'How would you implement SCD (Slowly Changing Dimensions) Type 2 in a data warehouse?',
        'What is data lineage, and why is it important for data governance?',
        'Explain how you would orchestrate a complex multi-step pipeline using Apache Airflow.',
        'What is the CAP theorem, and how does it apply to distributed data systems?',
        'How do you handle schema evolution in a data pipeline without breaking downstream consumers?',
        'What strategies would you use to reduce storage and compute costs in a cloud data platform?',
        'Explain the concept of an ELT architecture versus a traditional ETL architecture.',
    ],
    'Python Developer': [
        'Explain Python\'s GIL (Global Interpreter Lock). How does it affect multi-threaded programs?',
        'What is the difference between a list and a tuple in Python? When would you use each?',
        'Explain decorators in Python with an example of a custom decorator you would write.',
        'What are Python generators, and how do they differ from regular functions?',
        'How does Python\'s memory management work? Explain garbage collection.',
        'What is the difference between @staticmethod, @classmethod, and instance methods?',
        'Explain context managers and the `with` statement. How do you implement a custom one?',
        'What are Python metaclasses, and when would you use them?',
        'Explain the difference between deep copy and shallow copy in Python.',
        'How do you handle exceptions in Python? Explain the try/except/else/finally pattern.',
        'What is the difference between `is` and `==` in Python?',
        'Explain list comprehensions, dictionary comprehensions, and generator expressions.',
        'How does async/await work in Python? When would you use asyncio?',
        'What are Python slots, and how do they optimise memory usage?',
        'Explain how Python\'s `collections` module helps write cleaner code.',
        'What is monkey patching, and when is it acceptable to use it?',
        'How do you write and run unit tests in Python using pytest?',
        'Explain the difference between pickling and JSON serialisation.',
        'What are type hints in Python, and how do they improve code quality?',
        'How would you profile a slow Python script to identify performance bottlenecks?',
    ],
    'Backend Developer': [
        'Explain the difference between REST and GraphQL APIs. When would you choose each?',
        'What is the CAP theorem, and how does it influence backend system design?',
        'How do you design a rate-limiting system for a public API?',
        'Explain database indexing. What types of indexes exist, and how do they affect query performance?',
        'What is the N+1 query problem, and how do you solve it?',
        'How would you implement JWT-based authentication in a backend service?',
        'Explain the difference between horizontal and vertical scaling.',
        'What is a message queue, and when would you use one instead of a direct API call?',
        'How do you handle database migrations in a production system with zero downtime?',
        'Explain ACID properties in database transactions.',
        'What is the difference between synchronous and asynchronous processing? Give use-case examples.',
        'How would you design a caching strategy using Redis for a high-traffic endpoint?',
        'Explain SQL vs NoSQL. When would you choose a document database over a relational one?',
        'What are microservices, and what challenges do they introduce compared to monoliths?',
        'How do you secure a REST API against common vulnerabilities (SQL injection, CSRF, XSS)?',
        'Explain the difference between optimistic locking and pessimistic locking in databases.',
        'How would you implement pagination in a REST API for large result sets?',
        'What is a reverse proxy, and how does Nginx help in backend deployments?',
        'Explain how you would design an idempotent API endpoint.',
        'What is eventual consistency, and when is it acceptable in a distributed system?',
    ],
    'Frontend Developer': [
        'Explain the difference between the DOM and the virtual DOM.',
        'How does React\'s reconciliation algorithm work?',
        'What is the difference between controlled and uncontrolled components in React?',
        'Explain CSS specificity and how conflicting styles are resolved.',
        'What is the difference between `let`, `const`, and `var` in JavaScript?',
        'Explain closures in JavaScript with a practical example.',
        'What is the event loop in JavaScript? How do Promises and async/await relate to it?',
        'How do you optimise the performance of a web application?',
        'What is the difference between `==` and `===` in JavaScript?',
        'Explain how `this` works in JavaScript across different contexts.',
        'What is CSS Flexbox, and how does it differ from CSS Grid?',
        'How would you implement lazy loading for images and components in a React app?',
        'What are React hooks? Explain useState, useEffect, and useCallback.',
        'How does browser caching work, and how do you manage cache invalidation?',
        'Explain the difference between server-side rendering (SSR) and client-side rendering (CSR).',
        'What is a service worker, and how does it enable Progressive Web Apps?',
        'How do you ensure a website is accessible (WCAG compliance)?',
        'Explain the concept of code splitting and tree shaking in modern bundlers.',
        'What is the difference between sessionStorage, localStorage, and cookies?',
        'How do you debug a performance issue on a web page using browser DevTools?',
    ],
    'Full Stack Developer': [
        'Explain the request lifecycle from when a user types a URL to when the page renders.',
        'How do you decide what logic goes on the frontend vs. the backend?',
        'What is CORS, and how do you configure it in a Flask or Node.js backend?',
        'Explain the difference between SSR, CSR, and SSG. When would you use each?',
        'How would you design a real-time feature (e.g. live notifications) in a full-stack app?',
        'Explain how sessions and JWT tokens differ for managing user authentication.',
        'What is GraphQL, and how does it solve the over-fetching problem of REST APIs?',
        'How do you structure a full-stack project for maintainability as it scales?',
        'What is the difference between SQL and NoSQL databases, and how do you choose?',
        'Explain how you would implement file uploads securely in a full-stack application.',
        'What is a WebSocket, and when would you prefer it over HTTP polling?',
        'How do you handle environment variables and secrets in development vs. production?',
        'Explain how CI/CD pipelines work and how you would set one up for a full-stack app.',
        'How do you manage state in a large React application?',
        'What is Docker, and how does containerisation help in full-stack deployments?',
        'How would you implement role-based access control (RBAC) across the full stack?',
        'Explain database indexing and how it affects full-stack application performance.',
        'How do you approach testing in a full-stack project (unit, integration, e2e)?',
        'What is an API gateway, and why is it useful in a microservices architecture?',
        'How would you optimise the performance of both the frontend and backend of a web app?',
    ],
}

# Default pool for roles not explicitly listed
_DEFAULT_TECHNICAL = [
    'How do you approach debugging a complex issue in a system you are unfamiliar with?',
    'What version control practices do you follow on a team project?',
    'Explain the software development lifecycle (SDLC) and the role of different team members.',
    'How do you write maintainable and readable code?',
    'What is the difference between unit testing, integration testing, and end-to-end testing?',
    'Explain what CI/CD is and describe a pipeline you have worked with.',
    'How do you handle technical debt in a project?',
    'What design patterns have you used, and in what situations were they helpful?',
    'How do you stay up to date with new technologies and best practices?',
    'Explain RESTful API design principles.',
    'What is the difference between synchronous and asynchronous operations?',
    'How would you estimate the effort required for a new feature?',
]


# =============================================================================
# HR QUESTION BANK
# Partially personalised with detected role and experience level.
# =============================================================================

HR_BANK = [
    'Tell me about yourself and what draws you to the {role} role specifically.',
    'Where do you see yourself professionally in the next 3 to 5 years?',
    'Why are you looking to leave your current position (or why are you entering the job market now)?',
    'What do you know about our company, and why do you want to work here?',
    'How would your teammates or professors describe you?',
    'What is your greatest professional strength, and how have you applied it recently?',
    'What is an area you are actively working to improve, and what steps are you taking?',
    'How do you prioritise tasks when you have multiple deadlines at the same time?',
    'Describe your ideal working environment and team culture.',
    'What are your salary expectations, and are you flexible on the start date?',
    'How do you handle constructive feedback from a manager or peer?',
    'Tell me about a time you had to learn a new technology or tool quickly. How did you approach it?',
    'What motivates you to produce your best work?',
    'How do you balance technical depth with meeting project deadlines?',
    'Do you have any questions for us about the role or team?',
]


# =============================================================================
# BEHAVIORAL QUESTION BANK (STAR format)
# =============================================================================

BEHAVIORAL_BANK = [
    'Describe a situation where you had to meet a tight deadline. How did you manage your time and deliver?',
    'Tell me about a time you disagreed with a team member or manager. How did you handle the conflict?',
    'Give an example of a project where something went wrong. What did you do to fix it, and what did you learn?',
    'Describe a time when you took initiative on a project without being asked.',
    'Tell me about a situation where you had to explain a complex technical concept to a non-technical audience.',
    'Describe a time you had to work with incomplete or ambiguous requirements. How did you proceed?',
    'Give an example of a time you received critical feedback. How did you respond and what changed?',
    'Tell me about a successful collaboration with a cross-functional team.',
    'Describe a situation where you identified a problem before it became critical. What action did you take?',
    'Give an example of a time you had to adapt quickly to an unexpected change in project requirements.',
    'Tell me about a time you mentored or helped a colleague grow in a technical area.',
    'Describe the most challenging technical problem you have solved. Walk me through your approach.',
]


# =============================================================================
# SKILL EXTRACTION FROM RESUME TEXT
# =============================================================================

_ALL_TECH_KEYWORDS = [
    'python', 'java', 'javascript', 'typescript', 'sql', 'r', 'scala', 'go',
    'react', 'angular', 'vue', 'node.js', 'flask', 'django', 'fastapi', 'spring',
    'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
    'spark', 'hadoop', 'kafka', 'airflow', 'dbt', 'snowflake', 'bigquery',
    'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'terraform',
    'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
    'git', 'linux', 'rest api', 'graphql', 'ci/cd', 'mlflow',
    'tableau', 'power bi', 'excel', 'looker',
]

_PROJECT_SIGNALS = [
    r'built\s+(?:a|an)?\s*([\w\s]+?)(?:\s+using|\s+with|\s+that|\.|,)',
    r'developed\s+(?:a|an)?\s*([\w\s]+?)(?:\s+using|\s+with|\s+that|\.|,)',
    r'implemented\s+(?:a|an)?\s*([\w\s]+?)(?:\s+using|\s+with|\s+that|\.|,)',
    r'created\s+(?:a|an)?\s*([\w\s]+?)(?:\s+using|\s+with|\s+that|\.|,)',
    r'designed\s+(?:a|an)?\s*([\w\s]+?)(?:\s+using|\s+with|\s+that|\.|,)',
]


def _extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for kw in _ALL_TECH_KEYWORDS:
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(kw) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, text_lower):
            found.append(kw)
    return found


def _extract_project_hints(text: str) -> list[str]:
    """Extract brief project descriptions from resume text for personalisation."""
    hints = []
    for pattern in _PROJECT_SIGNALS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            clean = m.strip()
            if 5 < len(clean) < 60:
                hints.append(clean)
    return list(dict.fromkeys(hints))[:5]   # deduplicate, cap at 5


# =============================================================================
# PROJECT QUESTION BUILDER
# =============================================================================

_PROJECT_Q_TEMPLATES = [
    'Walk me through the most technically complex project listed on your resume. What was your specific contribution?',
    'How did you decide on the tech stack for your {project} project, and what trade-offs did you consider?',
    'What was the biggest technical challenge you faced during your {project} project, and how did you solve it?',
    'How did you measure the success or impact of your {project} project?',
    'If you were to rebuild your {project} project today, what would you do differently?',
    'How did you handle testing and quality assurance in your {project} project?',
    'Describe the architecture of your {project} project. How did the components interact?',
    'What did you learn from working on your {project} project that you have applied to subsequent work?',
    'How did you manage version control and collaboration during your {project} project?',
    'What performance or scalability considerations did you keep in mind while building your {project} project?',
]

_GENERIC_PROJECT_QUESTIONS = [
    'Walk me through the most technically complex project on your resume. What was your role and what did you deliver?',
    'How do you approach breaking down a large project into manageable tasks?',
    'Describe a project where you had to balance quality with tight deadlines. What trade-offs did you make?',
    'How do you document a project so that another developer can pick it up easily?',
    'What is the project you are most proud of, and what made it successful?',
    'How do you handle scope creep in a project?',
    'Describe a time a project did not go as planned. What happened, and what did you learn?',
    'How do you estimate the time required for a new feature or module?',
    'What tools and workflows do you use to track progress on a project?',
    'How do you ensure code quality and maintainability in a team project?',
]


def _build_project_questions(project_hints: list[str], n: int = 10) -> list[str]:
    questions = []
    if project_hints:
        for i, hint in enumerate(project_hints[:3]):
            if i < len(_PROJECT_Q_TEMPLATES) - 1:
                q = _PROJECT_Q_TEMPLATES[i + 1].replace('{project}', hint)
                questions.append(q)
    # Always include the walk-me-through opener
    questions.insert(0, _PROJECT_Q_TEMPLATES[0])
    # Fill remaining slots with generic project questions
    for q in _GENERIC_PROJECT_QUESTIONS:
        if len(questions) >= n:
            break
        if q not in questions:
            questions.append(q)
    return questions[:n]


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_interview_questions(resume_text: str, role: str) -> dict:
    """
    Generate categorised interview questions personalised to the
    candidate's resume and target role.

    Returns:
        {
            "technical":  [str, ...],   # 12 questions
            "hr":         [str, ...],   # 10 questions
            "project":    [str, ...],   # 10 questions
            "behavioral": [str, ...]    #  8 questions
        }
    """
    detected_skills   = _extract_skills(resume_text)
    project_hints     = _extract_project_hints(resume_text)

    # ---- Technical questions ----
    pool = TECHNICAL_BANK.get(role, _DEFAULT_TECHNICAL)
    # Shuffle for variety across runs, then pick 12
    shuffled = pool.copy()
    random.shuffle(shuffled)
    technical = shuffled[:12]

    # ---- HR questions ----
    hr = [q.replace('{role}', role) for q in HR_BANK][:10]

    # ---- Project questions ----
    project = _build_project_questions(project_hints, n=10)

    # ---- Behavioral questions ----
    behavioral_pool = BEHAVIORAL_BANK.copy()
    random.shuffle(behavioral_pool)
    behavioral = behavioral_pool[:8]

    return {
        'technical':  technical,
        'hr':         hr,
        'project':    project,
        'behavioral': behavioral,
    }