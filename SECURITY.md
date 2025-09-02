# Security Guidelines

## 🔒 API Key Security

### ✅ Do's
- **Use environment variables** for API keys (`.env` file or system environment)
- **Never commit API keys** to version control
- **Use `.env.example`** to show required variables without exposing actual values
- **Keep `.env` in `.gitignore`** (already configured)
- **Rotate API keys** regularly
- **Use minimal permissions** for API keys when possible

### ❌ Don'ts
- **Never hardcode API keys** in source code
- **Never share API keys** in chat, email, or forums
- **Never commit `.env` files** to repositories
- **Never screenshot code** with visible API keys
- **Never push to public repos** with exposed credentials

## 🛡️ Workshop Security Setup

This workshop is configured to use environment variables securely:

1. **API keys are loaded from `.env` file** using python-dotenv
2. **`.env` is in `.gitignore`** to prevent accidental commits
3. **`.env.example` shows required format** without actual keys
4. **Error messages guide users** to proper setup

## 🚨 If You Accidentally Expose an API Key

1. **Immediately revoke/regenerate** the key in the provider dashboard
2. **Remove the key from git history** using tools like BFG Repo-Cleaner
3. **Update your local `.env`** with the new key
4. **Check for any unauthorized usage** in your API dashboard

## 📞 Contact

If you discover any security issues in this workshop, please report them responsibly by creating an issue or contacting the maintainer.
