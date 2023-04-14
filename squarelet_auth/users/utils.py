# Django
import django.dispatch
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError

# Standard Library
import logging

# SquareletAuth
from squarelet_auth import settings
from squarelet_auth.organizations import get_organization_model
from squarelet_auth.organizations.models import Membership
from squarelet_auth.organizations.utils import (
    squarelet_update_or_create as organization_update_or_create,
)

User = get_user_model()
Organization = get_organization_model()

logger = logging.getLogger(__name__)

user_update = django.dispatch.Signal()


@transaction.atomic
def squarelet_update_or_create(uuid, data):
    """Update or create users based on data from squarelet"""

    required_fields = {"preferred_username", "organizations"}
    missing = required_fields - (required_fields & set(data.keys()))
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    if data.get("is_agency") and settings.DISABLE_CREATE_AGENCY:
        # do not create agency users if they have been disabled
        return None, False

    user, created = _squarelet_update_or_create(uuid, data)
    print('user', user.__dict__)
    print('data', data)

    _update_organizations(user, data)

    user_update.send(sender=User, user=user, data=data)

    return user, created


def _squarelet_update_or_create(uuid, data):
    """Format user data and update or create the user"""
    user_map = {
        "preferred_username": "username",
        "email": "email",
        "name": "name",
        "picture": "avatar_url",
        "email_failed": "email_failed",
        "email_verified": "email_verified",
        "use_autologin": "use_autologin",
    }
    user_defaults = {
        "preferred_username": "",
        "email": "",
        "name": "",
        "picture": "",
        "email_failed": False,
        "email_verified": False,
        "use_autologin": True,
    }
    user_data = {user_map[k]: data.get(k, user_defaults[k]) for k in user_map}

    try:
        user, created = User.objects.update_or_create(uuid=uuid, defaults=user_data)
    except IntegrityError:
        # User already exists with this email, so use that to get the user
        # and treat the MuckRock uuid as the source of truth by updating
        # this application's user.uuid with the user's MuckRock uuid.
        user_data.update({"uuid": uuid})
        user, created = User.objects.update_or_create(
            username=user_data['username'], defaults=user_data
        )

    return user, created


def _update_organizations(user, data):
    """Update the user's organizations"""
    try:
        current_organizations = set(user.organizations.all())
    except AttributeError:
        current_organizations = set()
    new_memberships = []
    active = True

    print('current_organizations', current_organizations)

    # current_organizations=[<SquareletOrganization: SquareletOrganization object (8)>]
    # data={access_token: [Filtered], expires_in: 3600, id_token: [Filtered], name: 'joe doe', nickname: 'joedoe', picture: 'https://cdn.muckrock.com/static/images/avatars/profile.png', preferred_username: 'joedoe', refresh_token: [Filtered], sub: '100286', token_type: [Filtered]}
    # new_memberships=[<Membership: joedoe in SquareletOrganization object (10)>]
    # org_data={admin: True, card: '', entitlements: [], individual: True, max_users: 1, name: 'hancushland', plan: 'free', private: True, slug: 'joedoe', uuid: '7c5eb5a1-d13d-44db-be21-30613df6cb49'}
    # organization=<SquareletOrganization: SquareletOrganization object (10)>

    # process each organization
    for org_data in data.get("organizations", []):
        print('org_data', org_data)
        organization, _ = organization_update_or_create(
            uuid=org_data["uuid"], data=org_data
        )
        print('organization', organization)
        if organization in current_organizations:
            # remove organizations from our set as we see them
            # any that are left will need to be removed
            current_organizations.remove(organization)
            user.memberships.filter(organization=organization).update(
                admin=org_data["admin"]
            )
        else:
            # if not currently a member, create the new membership
            # automatically activate new organizations (only first one)
            new_memberships.append(
                Membership(
                    user=user,
                    organization=organization,
                    active=active,
                    admin=org_data["admin"],
                )
            )
            active = False

    print('new_memberships', new_memberships)
    if new_memberships:
        # first new membership will be made active, de-activate current
        # active org first
        user.memberships.filter(active=True).update(active=False)
        user.memberships.bulk_create(new_memberships)

    print('user.organization', user.organization)

    # user must have an active organization, if the current
    # active one is removed, we will activate the user's individual organization
    if user.organization in current_organizations:
        user.memberships.filter(organization__individual=True).update(active=True)

    for membership in user.memberships.all():
        print('membership', membership.__dict__)
    # never remove the user's individual organization
    individual_organization = user.memberships.get(organization__individual=True)
    if individual_organization in current_organizations:
        logger.error("Trying to remove a user's individual organization: %s", user)
        current_organizations.remove(individual_organization)

    user.memberships.filter(organization__in=current_organizations).delete()
