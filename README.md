# OnlyFans Economic Index

OnlyFans-Economic-Index is a project aimed at creating an economic index based on the earnings of content creators on the OnlyFans platform. Inspired by the "Stripper Index," it seeks to observe and predict economic trends by analyzing revenue trends from OnlyFans creators, offering insights into economic cycles through unconventional indicators.

## Features

- **Profile Data Collection**: Automated collection of OnlyFans creator profile data including posts count, subscriber metrics, and pricing information
- **Database Storage**: Support for both SQLite (local) and Supabase (cloud) database storage
- **Batch Processing**: Process multiple profiles from a file with rate limiting (5-second pause every 10 profiles)
- **Browser Automation**: Headless browser automation using Selenium for data extraction
- **API Interception**: Advanced network request interception to capture real-time API data
- **Mock Testing**: Built-in mock service for development and testing
- **Async Support**: Fully asynchronous architecture for optimal performance

## Installation

### Prerequisites

- Python 3.12+
- Chrome/Chromium browser
- ChromeDriver (automatically managed)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/OnlyFans-Economic-Index.git
cd OnlyFans-Economic-Index
```

2. Install dependencies:

```bash
make dev
```

3. Configure environment variables (for Supabase):

```bash
# Create .env file
SUPA_BASE_PWD=your_supabase_password
SUPA_BASE_ID=your_project_id
```

## Usage

### Command Line Interface

The application provides a CLI tool accessible via the `oei` command:

```bash
# Test the application
oei --test

# Save a single profile snapshot
oei --save-profile USERNAME

# Process multiple profiles from a file
oei --save-all-from-file usernames.txt

# Use mock data for testing
oei --save-profile USERNAME --use-mock

# Use SQLite instead of Supabase
oei --save-profile USERNAME --use-sqlite

# Combine options
oei --save-all-from-file usernames.txt --use-mock --use-sqlite
```

### Profile Data Collection

The system collects comprehensive profile data including:

- Username and display name
- Verification status
- Avatar and header images
- Bio/about information
- Post counts (total, photos, videos)
- Subscription pricing
- Join date and last seen
- Favorites and tips information
- Subscriber metrics

### Rate Limiting

To avoid overwhelming servers, the application automatically:

- Pauses for 5 seconds after processing every 10 profiles
- Uses headless browser mode for reduced resource usage
- Implements smart retry mechanisms

### Database Schema

Profiles are stored with the following structure:

```sql
CREATE TABLE onlyfans_profiles_snapshots (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    profile_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Development

### Commands

```bash
# Run tests
make test

# Run linting
make lint

# Fix linting issues
make lint-fix

# Type checking
make type-check

# Format code
make format

# Run all checks
make check

# Build package
make build
```
