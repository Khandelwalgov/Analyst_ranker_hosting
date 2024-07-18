from app import app,db, users

# Assuming 'users' is your SQLAlchemy model for the 'users' table
app.app_context().push()

# Query all users
all_users = users.query.all()

# Print all users
for user in all_users:
    print(user._id, user.name, user.username, user.email)
