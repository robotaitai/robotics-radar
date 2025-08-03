# Robotics Radar

A robust, modular, and scalable Python-based pipeline that fetches, analyzes, stores, and delivers top robotics-related posts from the X (Twitter) API.

## 🚀 Features

- **Automated Tweet Fetching**: Regularly fetches tweets every 2 hours using configurable keywords
- **Smart Filtering**: YAML-based configuration for keywords, languages, and exclusion filters
- **Data Storage**: SQLite database for storing tweets, authors, feedback, and analytics
- **User Feedback Loop**: Telegram bot and email notifications with interactive feedback
- **Analytics Dashboard**: FastAPI + Streamlit dashboard for insights and trends
- **NLP Integration**: Keyword extraction and topic analysis using spaCy
- **Scoring System**: Dynamic scoring based on engagement metrics and user feedback

## 🏗️ Architecture

```
robotics-radar/
├── config/                 # Configuration files (YAML)
├── data/                  # Database storage
├── scraper/               # RSS feed fetching and scheduling
├── storage/               # Database operations
├── notifier/              # Telegram and email notifications
├── analytics/             # Dashboard and analytics
├── feedback/              # User feedback processing
├── nlp/                  # Natural language processing
├── scoring/              # Content scoring algorithms
├── scripts/              # Setup and deployment scripts
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── utilities/        # Test utilities
├── agent_integration/     # Future LLM agent integration
├── community_features/    # Future community features
└── logs/                 # Application logs
```

## 🛠️ Setup

### Prerequisites

- Python 3.11+
- Conda or virtual environment
- X (Twitter) API credentials
- Telegram Bot Token
- SMTP credentials for email notifications

### Quick Start

1. **Clone and setup environment:**
   ```bash
   ./scripts/install.sh
   ```

2. **Configure your credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

3. **Initialize the database:**
   ```bash
   ./scripts/bringup.sh
   ```

4. **Run the application:**
   ```bash
   ./scripts/run.sh
   ```

### Manual Setup

1. **Create virtual environment:**
   ```bash
   python -m venv robotics-radar-env
   source robotics-radar-env/bin/activate  # On Windows: robotics-radar-env\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download spaCy model:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **Set environment variables:**
   ```bash
   export TWITTER_API_KEY="your_api_key"
   export TWITTER_API_SECRET="your_api_secret"
   export TWITTER_ACCESS_TOKEN="your_access_token"
   export TWITTER_ACCESS_TOKEN_SECRET="your_access_token_secret"
   export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
   export SMTP_SERVER="smtp.gmail.com"
   export SMTP_PORT="587"
   export SMTP_USERNAME="your_email@gmail.com"
   export SMTP_PASSWORD="your_app_password"
   ```

## 📊 Usage

### Running the Pipeline

The main pipeline runs automatically every 2 hours:

```bash
python scraper/scheduler.py
```

### Analytics Dashboard

Start the analytics dashboard:

```bash
streamlit run analytics/dashboard.py
```

### Telegram Bot

The Telegram bot provides interactive feedback:

```bash
python notifier/telegram_bot.py
```

## 🔧 Configuration

### Keywords Configuration (`config/keywords.yaml`)

```yaml
domain: robotics
keywords:
  - robotics research
  - open-source robotics
  - robot announcement
  - autonomous systems
  - AI robotics
languages:
  - en
exclude_keywords:
  - hiring
  - webinar
  - job posting
```

### Scoring Weights

Adjust scoring parameters in `scoring/scoring_model.py`:

- Like weight: 1.0
- Retweet weight: 2.0
- Reply weight: 1.5
- User feedback weight: 3.0

## 🧪 Testing

Run the test suite:

```bash
./scripts/test.sh
```

Or manually:

```bash
pytest tests/ -v
```

## 📈 Future Phases

### Phase 2: AI Agent Integration
- LLM-based automatic commenting and reposting
- Advanced content analysis and summarization
- Intelligent content curation

### Phase 3: Community Features
- User-configurable management systems
- Community sharing and collaboration
- Advanced analytics and insights

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information

## 🔒 Security

- Never commit API credentials
- Use environment variables for sensitive data
- Regularly rotate API keys
- Monitor API usage limits # robotics-radar
# robotics-radar
