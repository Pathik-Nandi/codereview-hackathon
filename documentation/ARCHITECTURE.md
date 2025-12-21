# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATIONS                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │   GitHub     │  │   Dashboard  │  │   CI/CD      │  │   Webhook   ││
│  │   API Client │  │   UI         │  │   Pipeline   │  │   Events    ││
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘│
└─────────┼──────────────────┼──────────────────┼──────────────────┼──────┘
          │                  │                  │                  │
          └──────────────────┴──────────────────┴──────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FLASK REST API SERVER                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       API ENDPOINTS                              │   │
│  │  /api/analyze         /api/analytics/*     /api/auto-merge/*    │   │
│  │  /api/prs/*           /api/dashboard/*     /webhook/github      │   │
│  └───────────────────────────┬──────────────────────────────────────┘   │
│                              │                                           │
│  ┌───────────────────────────▼──────────────────────────────────────┐   │
│  │                    AGENT DISPATCHER                              │   │
│  │  • Route requests to appropriate agents                          │   │
│  │  • Strategy: file_based, round_robin, security_first            │   │
│  └───────────────────────────┬──────────────────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      MULTI-AGENT SYSTEM                                  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │              MAIN ORCHESTRATOR AGENT                           │    │
│  │  Coordinates all sub-agents and aggregates results             │    │
│  └─────┬──────────────────────────────────────────────────────────┘    │
│        │                                                                 │
│        ├─────────────────────────────────────────────────────────┐      │
│        │                                                         │      │
│  ┌─────▼─────────────┐  ┌──────────────────┐  ┌────────────────▼───┐  │
│  │ Static Analysis   │  │  Security Agent  │  │  Code Quality      │  │
│  │     Agent         │  │                  │  │     Agent          │  │
│  │  • Pylint         │  │  • Bandit        │  │  • Radon           │  │
│  │  • Flake8         │  │  • Safety        │  │  • Complexity      │  │
│  │  • ESLint         │  │  • Pattern scan  │  │  • Maintainability │  │
│  │  • Checkstyle     │  │  • Secret detect │  │  • Duplication     │  │
│  └───────────────────┘  └──────────────────┘  └────────────────────┘  │
│                                                                          │
│  ┌───────────────────┐  ┌──────────────────┐  ┌────────────────────┐  │
│  │  Context Agent    │  │  Coverage Agent  │  │  Auto-Merge Agent  │  │
│  │  • PR metadata    │  │  • Test coverage │  │  • Quality gates   │  │
│  │  • Best practices │  │  • Test patterns │  │  • Approval rules  │  │
│  │  • Patterns       │  │  • Test ratio    │  │  • Auto-approve    │  │
│  └───────────────────┘  └──────────────────┘  └────────────────────┘  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │            DATABASE PERSISTENCE AGENT                           │   │
│  │  • Save analysis results to PostgreSQL                          │   │
│  │  • Track historical data                                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │          ANALYTICS PROCESSING AGENT                             │   │
│  │  • Aggregate user statistics                                    │   │
│  │  • Generate insights and recommendations                        │   │
│  │  • Identify trends and patterns                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                                  │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────────────┐  │
│  │ GitHub Service │  │ Slack Service  │  │  Dashboard Service      │  │
│  │  • Fetch PRs   │  │  • Notify      │  │  • Submit metrics       │  │
│  │  • Post review │  │  • Alerts      │  │  • Visualizations       │  │
│  │  • Merge PRs   │  │  • Messages    │  │                         │  │
│  └────────────────┘  └────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA PERSISTENCE                                 │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    PostgreSQL Database                        │      │
│  │                                                               │      │
│  │  Tables:                                                      │      │
│  │  • pr_analysis      - Main PR analysis results                │      │
│  │  • pr_issues        - Individual code issues                 │      │
│  │  • pr_metrics       - Detailed metrics                       │      │
│  │  • user_statistics  - Aggregated user stats                  │      │
│  │  • user_analytics   - Time-series analytics                  │      │
│  │  • best_practices   - Recommendations catalog                │      │
│  └──────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Flask REST API Server

**Purpose**: Entry point for all requests  
**Technology**: Flask 3.0  
**Port**: 5000 (configurable)

**Responsibilities**:
- Request validation and authentication
- Route requests to appropriate agents
- Format and return responses
- Handle webhooks from GitHub

### 2. Agent Dispatcher

**Purpose**: Route requests to the appropriate agent based on strategy  

**Strategies**:
- `file_based` - Select agent based on file types changed
- `round_robin` - Cycle through agents evenly
- `security_first` - Prioritize security analysis
- `fixed` - Always use a specific agent

### 3. Main Orchestrator Agent

**Purpose**: Coordinate all sub-agents and aggregate results

**Workflow**:
1. Receive PR event/request
2. Fetch PR details from GitHub
3. Dispatch to all sub-agents in parallel
4. Aggregate and normalize results
5. Calculate overall scores
6. Return consolidated report

### 4. Specialized Agents

#### Static Analysis Agent
- **Languages**: Python, Java, Scala, JavaScript, TypeScript
- **Tools**: Pylint, Flake8, ESLint, Checkstyle
- **Output**: Code style issues, syntax errors, anti-patterns

#### Security Agent
- **Focus**: Security vulnerabilities
- **Tools**: Bandit, Safety, Custom pattern matching
- **Output**: Security issues, hardcoded secrets, injection risks

#### Code Quality Agent
- **Focus**: Code maintainability
- **Tools**: Radon, custom metrics
- **Output**: Complexity scores, duplication, code smells

#### Context Agent
- **Focus**: PR metadata and best practices
- **Analysis**: PR size, description quality, commit patterns
- **Output**: Context issues, recommendations

#### Coverage Agent
- **Focus**: Test coverage estimation
- **Analysis**: Test file ratio, test patterns
- **Output**: Coverage estimates, test quality metrics

#### Auto-Merge Agent
- **Focus**: Automated PR merging
- **Evaluation**: Quality gates, approval rules
- **Action**: Auto-merge qualified PRs

#### Database Persistence Agent
- **Focus**: Data storage
- **Operations**: Save PR analysis, issues, metrics
- **Database**: PostgreSQL with SQLAlchemy ORM

#### Analytics Processing Agent
- **Focus**: User insights
- **Processing**: Aggregate statistics, identify trends
- **Output**: Best practices, bad practices, recommendations

### 5. External Services

#### GitHub Service
- Fetch PR details and files
- Post review comments
- Create status checks
- Merge pull requests

#### Slack Service
- Send notifications
- Post alerts
- Integration with channels

#### Dashboard Service
- Submit analysis metrics
- Provide visualization data

### 6. Database Layer

**Database**: PostgreSQL 12+

**Schema**:
- **pr_analysis**: Main table for PR analysis results
- **pr_issues**: Individual issues found
- **pr_metrics**: Detailed code metrics
- **user_statistics**: Aggregated user performance
- **user_analytics**: Time-series analytics snapshots
- **best_practices**: Recommendations catalog

## Data Flow

### PR Analysis Flow

```
1. Client Request
   ↓
2. API Endpoint (/api/analyze)
   ↓
3. Validate Request
   ↓
4. Fetch PR from GitHub
   ↓
5. Create PR Event Object
   ↓
6. Dispatch to Main Orchestrator
   ↓
7. Parallel Agent Execution
   ├─→ Static Analysis
   ├─→ Security Analysis
   ├─→ Code Quality Analysis
   ├─→ Context Analysis
   └─→ Coverage Analysis
   ↓
8. Aggregate Results
   ↓
9. Calculate Scores
   ↓
10. Persist to Database (if enabled)
   ↓
11. Send Notifications (if configured)
   ↓
12. Return Response
```

### Analytics Flow

```
1. Analytics Request (/api/analytics/user)
   ↓
2. Query Historical Data
   ↓
3. Analytics Processing Agent
   ↓
4. Aggregate Statistics
   ↓
5. Identify Patterns
   ├─→ Best Practices
   ├─→ Bad Practices
   ├─→ Trends Analysis
   └─→ Recommendations
   ↓
6. Generate Insights
   ↓
7. Return Analytics Report
```

## Scalability Considerations

### Horizontal Scaling
- Multiple Flask instances behind load balancer
- Stateless API design
- Database connection pooling

### Async Processing
- Celery workers for long-running analysis
- Redis for job queue
- Background task processing

### Caching
- Redis for frequently accessed data
- Query result caching
- API response caching

## Security Architecture

### Authentication
- GitHub token authentication
- Webhook signature verification
- API key for dashboard

### Data Security
- Secure storage of credentials in environment variables
- PostgreSQL connection encryption
- No sensitive data in logs

### Input Validation
- Request validation middleware
- SQL injection prevention (parameterized queries)
- XSS prevention in API responses

## Deployment Architecture

### Development
```
Single Server
├── Flask Application (port 5000)
├── PostgreSQL (port 5433)
└── Redis (optional, port 6379)
```

### Production
```
Load Balancer
├── Flask App Instance 1
├── Flask App Instance 2
└── Flask App Instance N
         ↓
    PostgreSQL Cluster
    (Primary + Replicas)
         ↓
    Redis Cluster
    (Master + Replicas)
```

## Configuration Management

### Environment-Based
- `.env` file for local development
- Environment variables for production
- `config/settings.yaml` for agent configuration

### Hierarchical Configuration
1. Environment variables (highest priority)
2. YAML configuration file
3. Default values (lowest priority)

## Monitoring & Observability

### Logging
- Structured logging with `structlog`
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized log aggregation (recommended)

### Metrics
- API response times
- Agent execution times
- Database query performance
- Error rates

### Health Checks
- `/health` endpoint
- Database connectivity check
- External service availability

## Technology Choices

### Why Flask?
- Lightweight and flexible
- Easy to extend
- Great for REST APIs
- Large ecosystem

### Why PostgreSQL?
- ACID compliance
- Complex queries support
- JSON support for metadata
- Reliability and performance

### Why Multi-Agent Architecture?
- Separation of concerns
- Parallel execution
- Easy to add new agents
- Scalable and maintainable

---

**Next Steps**: 
- [Quick Start Guide](QUICK_START.md)
- [API Reference](API_REFERENCE.md)
- [Installation Guide](INSTALLATION.md)
