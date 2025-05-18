# Deployment Guide for CrimeVision-AI

This guide provides instructions for deploying the CrimeVision-AI application to various platforms.

## Local Deployment

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/PraTham-Patill/Safenity-AI-Project.git
   cd Safenity-AI-Project
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Download the model files:
   - Follow the instructions in `MODEL_DOWNLOAD.md` to download the required model files
   - Place them in the `models/` directory

5. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your Twilio credentials for SMS notifications (optional)

6. Run the application:
   ```
   python webapp/app.py
   ```

7. Access the application at `http://localhost:5000`

## Deployment to Heroku

### Prerequisites

- Heroku account
- Heroku CLI installed

### Steps

1. Login to Heroku:
   ```
   heroku login
   ```

2. Create a new Heroku app:
   ```
   heroku create Safenity-ai
   ```

3. Add a Procfile to the root directory with the following content:
   ```
   web: gunicorn -w 4 -k uvicorn.workers.UvicornWorker webapp.app:app
   ```

4. Add `gunicorn` and `uvicorn` to requirements.txt

5. Configure environment variables on Heroku:
   ```
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set TWILIO_ACCOUNT_SID=your-twilio-account-sid
   heroku config:set TWILIO_AUTH_TOKEN=your-twilio-auth-token
   heroku config:set TWILIO_PHONE_NUMBER=your-twilio-phone-number
   heroku config:set NOTIFICATION_PHONE_NUMBER=recipient-phone-number
   ```

6. Deploy to Heroku:
   ```
   git push heroku main
   ```

7. Note about model files: Since Heroku has an ephemeral filesystem and size limits, you have two options:
   - Use a smaller, optimized model that fits within Heroku's size limits
   - Store your models in a cloud storage service (like AWS S3) and modify the application to download them at startup

## Deployment to AWS

### Using AWS Elastic Beanstalk

1. Install the EB CLI:
   ```
   pip install awsebcli
   ```

2. Initialize your EB application:
   ```
   eb init -p python-3.8 Safenity-ai
   ```

3. Create an environment and deploy:
   ```
   eb create Safenity-ai-env
   ```

4. Configure environment variables:
   ```
   eb setenv SECRET_KEY=your-secret-key TWILIO_ACCOUNT_SID=your-sid ...
   ```

5. For model files, you can:
   - Include them in your deployment package
   - Store them in S3 and have your application download them at startup

## Deployment to Docker

1. Create a Dockerfile in the project root:
   ```dockerfile
   FROM python:3.8-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   EXPOSE 5000

   CMD ["python", "webapp/app.py"]
   ```

2. Build the Docker image:
   ```
   docker build -t Safenity-ai .
   ```

3. Run the container:
   ```
   docker run -p 5000:5000 --env-file .env Safenity-ai
   ```

## Continuous Deployment

You can set up continuous deployment using GitHub Actions or other CI/CD tools. A basic GitHub Actions workflow would look like this:

```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
        heroku_app_name: "Safenity-ai"
        heroku_email: ${{ secrets.HEROKU_EMAIL }}
```

## Security Considerations

1. Always use environment variables for sensitive information
2. Set up proper authentication for your application
3. Consider implementing rate limiting to prevent abuse
4. Regularly update dependencies to patch security vulnerabilities
5. Use HTTPS for all communications

## Troubleshooting

- If the application fails to start, check the logs:
  - Local: Check the console output
  - Heroku: `heroku logs --tail`
  - AWS EB: `eb logs`
  - Docker: `docker logs <container_id>`

- If models aren't loading, verify:
  - The model files are in the correct location
  - The model files have the correct format
  - The application has permission to read the files

- For SMS notification issues:
  - Verify your Twilio credentials
  - Check that the phone numbers are in the correct format (with country code)
  - Ensure your Twilio account has sufficient credit
