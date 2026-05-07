from google.cloud import vision
import cv2

def extract_text_with_confidence(image_np, gcp_key):

    client = vision.ImageAnnotatorClient.from_service_account_file(gcp_key)

    _, encoded = cv2.imencode('.png', image_np)
    image = vision.Image(content=encoded.tobytes())

    response = client.document_text_detection(image=image)

    text = response.full_text_annotation.text

    confidences = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            confidences.append(block.confidence)

    avg_conf = sum(confidences)/len(confidences) if confidences else 0

    return text, avg_conf