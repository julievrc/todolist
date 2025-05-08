import os
from dotenv import load_dotenv
from google.cloud import translate_v2 as translate

# Load environment variables from .env file
load_dotenv()

def test_translation():
    try:
        # Check environment variables
        credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        
        print(f"Using credentials: {credentials_path}")
        print(f"Project ID: {project_id}")
        
        # Initialize the Translation client
        translate_client = translate.Client()
        
        # Test text to translate
        text = "Hello world"
        target_language = "es"
        
        print(f"Translating: '{text}' to {target_language}")
        
        # Perform translation
        result = translate_client.translate(
            text,
            target_language=target_language
        )
        
        # Print results
        print(f"Source language: {result['detectedSourceLanguage']}")
        print(f"Translation: {result['translatedText']}")
        print("Translation successful!")
        return True
    except Exception as e:
        print(f"Error during translation: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_translation()
    print(f"Test {'PASSED' if success else 'FAILED'}")