from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .api_helpers import submit_code

# Corrected language map
LANGUAGE_ID_MAP = {
    "c": 50,
    "cpp": 54,
    "python": 71,
    "java": 62,
    "javascript": 63
}

@csrf_exempt
def compile_code(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            source_code = data.get("source_code", "")  # Fixed key
            language = data.get("language", "python").lower()
            stdin = data.get("stdin", "")

            language_id = LANGUAGE_ID_MAP.get(language)
            if not language_id:
                return JsonResponse({"error": "Unsupported language"}, status=400)

            result = submit_code(source_code, language_id, stdin)
            return JsonResponse(result)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST method allowed"}, status=405)
