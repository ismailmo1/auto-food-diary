from super_gradients.training.models import SgModule


def predict(image_url: str, model: SgModule, conf_thresh: float = 0.2) -> list[str]:
    """predict food labels from image_url

    Args:
        image_url (str): absolute url (or path) to image
        model (SgModule): model to call `.predict` on
        conf_thresh (float, optional): minimum confidence to predict label. Defaults to 0.2.

    Returns:
        list[str]: _description_
    """
    pred = model.predict(image_url, conf=conf_thresh)
    labels = pred._images_prediction_lst[0].prediction.labels
    class_names = pred._images_prediction_lst[0].class_names
    return [class_names[int(x)] for x in labels]
