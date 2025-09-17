# Development Credentials

## Admin User

For local development, use these credentials to access the admin panel:

- **Email:** `admin@manna.com`
- **Password:** `MannaAdmin2024!`

## Creating/Resetting Admin User

If you need to create or reset the admin user, run:

```bash
# From the backend directory
cd packages/backend
python scripts/create_admin_simple.py
```

This script will:
- Create the admin user if it doesn't exist
- Offer to reset the password if the user already exists

## Important Notes

- These credentials are for **development only**
- Change the password immediately in production environments
- Registration is disabled - only admin can create new users
- The admin user has full superuser privileges

## Database Access

For direct database access during development:

- **Host:** localhost
- **Port:** 5432
- **Database:** manna_dev
- **User:** manna
- **Password:** manna