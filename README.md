# SquareletAuth

This Django application allows you to authenticate against the MuckRock user service

## Required config values
To use squarelet-auth in your app, you need to add these config values to your settings.py:
1. `BASE_URL` - The application's hostname.
2. `SOCIAL_AUTH_SQUARELET_KEY` - OAuth public key. This comes from MuckRock.
3. `SOCIAL_AUTH_SQUARELET_SECRET` - OAuth secret key. This comes from MuckRock.
4. `SQUARELET_USER_MODEL` - The user model you use in your application.
5. `SQUARELET_ORGANIZATION_MODEL` - The organization model in your application. This needs to work with the MuckRock organization models. In theory you can import the Organization model from this repo but your mileage may vary.
