"""
AWS Elastic Beanstalk entry point for TCGA Co-Deletion Analysis application.

This file is required by AWS Elastic Beanstalk, which looks for:
- A file named 'application.py'
- A variable named 'application' (the WSGI server)
"""

from app import app

# Expose the Flask server for Elastic Beanstalk
application = app.server

if __name__ == "__main__":
    # For local testing with AWS configuration
    # Production will use the 'application' variable directly
    app.run(host="0.0.0.0", port=5000, debug=False)
