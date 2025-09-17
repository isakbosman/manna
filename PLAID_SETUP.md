# Plaid Setup Instructions

This application uses Plaid to connect to real bank accounts and automatically import transactions for bookkeeping and financial reporting.

## Getting Started with Plaid

1. **Sign up for a Plaid account**
   - Go to https://dashboard.plaid.com/signup
   - Create a free account

2. **Get your Sandbox credentials**
   - After signing in, go to https://dashboard.plaid.com/team/keys
   - Copy your **Sandbox** credentials:
     - Client ID
     - Sandbox Secret

3. **Configure the application**
   - Open `docker-compose.yml`
   - Replace the Plaid environment variables in the backend service:
     ```yaml
     - PLAID_CLIENT_ID=YOUR_PLAID_CLIENT_ID  # Replace with your Client ID
     - PLAID_SECRET=YOUR_PLAID_SECRET        # Replace with your Sandbox Secret
     - PLAID_ENVIRONMENT=sandbox             # Keep as sandbox for testing
     ```

4. **Restart the backend**
   ```bash
   docker-compose restart backend
   ```

## Testing with Sandbox

In sandbox mode, you can use Plaid's test credentials:
- When connecting an account, use:
  - Username: `user_good`
  - Password: `pass_good`
- This will simulate a successful bank connection

## Important Notes

- The application is designed to work ONLY with real bank connections via Plaid
- There is no manual account creation - all accounts must be connected through Plaid
- Transactions are automatically imported from connected banks
- This ensures accurate, real-time financial data for bookkeeping and reporting

## Moving to Production

When ready for production:
1. Get your Production credentials from Plaid dashboard
2. Update `PLAID_ENVIRONMENT=production` in docker-compose.yml
3. Replace sandbox credentials with production credentials
4. Apply for Production access in Plaid dashboard (requires approval)