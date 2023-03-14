from squarelet_auth import model_from_setting


def get_organization_model():
    """
    Return the Organization model that is active in this project.
    """
    return model_from_setting("ORGANIZATION_MODEL")
