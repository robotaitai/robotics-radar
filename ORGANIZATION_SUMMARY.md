# Robotics Radar - Folder Organization Summary

## 🗂️ **Main Directory Structure**

```
robotics-radar/
├── 📁 config/                 # Configuration files (YAML)
│   ├── keywords.yaml         # Search keywords and scoring
│   └── feeds.yaml            # RSS feed configurations
├── 📁 data/                  # Database storage
│   └── radar.db             # SQLite database
├── 📁 scraper/               # RSS feed fetching and scheduling
│   ├── rss_fetcher.py       # RSS feed processing
│   └── scheduler.py         # APScheduler orchestration
├── 📁 storage/               # Database operations
│   └── database.py          # SQLite database manager
├── 📁 notifier/              # Telegram and email notifications
│   └── telegram_bot.py      # Telegram bot implementation
├── 📁 analytics/             # Dashboard and analytics
│   └── dashboard.py         # Streamlit dashboard
├── 📁 feedback/              # User feedback processing
│   └── feedback_processor.py # Feedback handling
├── 📁 nlp/                  # Natural language processing
│   └── keyword_extraction.py # spaCy keyword extraction
├── 📁 scoring/              # Content scoring algorithms
│   └── scoring_model.py     # Scoring logic
├── 📁 scripts/              # Setup and deployment scripts
│   ├── install.sh           # Environment setup
│   ├── bringup.sh           # Database initialization
│   ├── run.sh               # Start/stop application
│   ├── test.sh              # Run test suite
│   ├── status.sh            # Check system status
│   ├── setup_scheduled_running.sh # Cron job setup
│   ├── import_90_days.py    # Historical data import
│   ├── historical_data_import.py # Bulk import utility
│   └── migrate_rating_system.py # Database migration
├── 📁 tests/                # Test suite (NEWLY ORGANIZED)
│   ├── README.md            # Test documentation
│   ├── 📁 unit/             # Unit tests
│   ├── 📁 integration/      # Integration tests (13 files)
│   └── 📁 utilities/        # Test utilities (6 files)
├── 📁 agent_integration/     # Future LLM agent integration
│   └── article_reader.py    # Article content reader
├── 📁 community_features/    # Future community features
├── 📁 logs/                 # Application logs
├── 📁 robotics-radar-env/   # Virtual environment
├── 📄 README.md             # Main project documentation
├── 📄 RUNNING_GUIDE.md      # Detailed running instructions
├── 📄 requirements.txt      # Python dependencies
├── 📄 env.example           # Environment variables template
└── 📄 .gitignore           # Git ignore rules
```

## 🧹 **Organization Changes Made**

### **Moved Files:**
- **Test Scripts**: Moved 13 test files from root to `tests/integration/`
- **Utility Scripts**: Moved 6 utility files from root to `tests/utilities/`
- **Removed**: Deleted old `test_env/` directory (unused virtual environment)

### **Created Structure:**
- `tests/unit/` - For future unit tests
- `tests/integration/` - For integration tests
- `tests/utilities/` - For test utilities and debugging scripts
- `tests/README.md` - Documentation for test structure

### **Benefits:**
✅ **Clean Root Directory**: No more orphan scripts cluttering the main folder  
✅ **Logical Organization**: Tests grouped by type and purpose  
✅ **Easy Navigation**: Clear structure for finding specific tests  
✅ **Scalable**: Easy to add new tests in appropriate categories  
✅ **Documentation**: Clear README explaining test structure  

## 🚀 **Current Status**

The Robotics Radar project now has a **clean, professional folder structure** that follows best practices:

- **Main application code** in dedicated modules
- **Configuration files** in `config/`
- **Scripts** in `scripts/`
- **Tests** properly organized in `tests/`
- **Documentation** clearly separated
- **No orphan files** in the root directory

The project is now ready for production use with a maintainable, scalable structure! 🎉 