from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser
from problems.models import Problem
from .models import Submission
from .api_helpers import submit_code
import json

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

            source_code = data.get("source_code", "")
            language = data.get("language", "python").lower()
            stdin = data.get("stdin", "")
            problem_id = data.get("problem_id")

            if not source_code:
                return JsonResponse({"error": "Source code cannot be empty."}, status=400)

            language_id = LANGUAGE_ID_MAP.get(language)
            if not language_id:
                return JsonResponse({"error": "Unsupported language."}, status=400)

            result = submit_code(source_code, language_id, stdin)

            verdict = "Failed"
            actual_output = result.get("stdout", "").strip() if result.get("stdout") else ""
            stderr = result.get("stderr", "")
            status_id = result.get("status", {}).get("id", 0)
            status_description = result.get("status", {}).get("description", "Error")

            problem = None
            try:
                problem = Problem.objects.get(id=problem_id)
            except Problem.DoesNotExist:
                return JsonResponse({"error": "Problem not found."}, status=404)

            if status_id == 3:  # Successfully Compiled & Executed
                expected_output = problem.expected_output.strip()
                if actual_output == expected_output:
                    verdict = "Accepted"
                else:
                    verdict = "Wrong Answer"
            else:
                verdict = status_description

            if request.user.is_authenticated:
                Submission.objects.create(
                    user=request.user,
                    problem=problem,
                    code=source_code,
                    language=language,
                    verdict=verdict
                )

            return JsonResponse({
                "stdout": actual_output,
                "stderr": stderr,
                "verdict": verdict
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed."}, status=405)
