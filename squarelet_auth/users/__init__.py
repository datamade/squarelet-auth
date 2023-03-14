from squarelet_auth import model_from_setting


def get_user_model():
    return model_from_setting("USER_MODEL")
