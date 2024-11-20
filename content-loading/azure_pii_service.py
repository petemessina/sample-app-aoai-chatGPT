from azure.ai.textanalytics import TextAnalyticsClient

def detect_pii_in_documents(text: str, client: TextAnalyticsClient) -> dict:
    response = client.detect_pii_entities([text])
    return response[0].to_dict()