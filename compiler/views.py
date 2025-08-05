from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from problems.models import Problem, TestCase
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
            problem_id = data.get("problem_id")

            if not source_code:
                return JsonResponse({"error": "Source code cannot be empty."}, status=400)

            language_id = LANGUAGE_ID_MAP.get(language)
            if not language_id:
                return JsonResponse({"error": "Unsupported language."}, status=400)

            # Get the problem and all its test cases
            problem = get_object_or_404(Problem, id=problem_id)
            test_cases = TestCase.objects.filter(problem=problem)

            if not test_cases.exists():
                return JsonResponse({"error": "No test cases found for this problem."}, status=404)

            results = []
            all_passed = True

            for test_case in test_cases:
                result = submit_code(source_code, language_id, test_case.input_data)

                actual_output = result.get("stdout", "").strip() if result.get("stdout") else ""
                stderr = result.get("stderr", "")
                status_id = result.get("status", {}).get("id", 0)
                status_description = result.get("status", {}).get("description", "Error")
                expected_output = test_case.expected_output.strip()

                if status_id != 3:  # Not successful
                    all_passed = False
                    results.append({
                        "input": test_case.input_data,
                        "expected_output": expected_output,
                        "actual_output": actual_output,
                        "stderr": stderr,
                        "status": status_description,
                        "verdict": status_description
                    })
                elif actual_output != expected_output:
                    all_passed = False
                    results.append({
                        "input": test_case.input_data,
                        "expected_output": expected_output,
                        "actual_output": actual_output,
                        "stderr": stderr,
                        "status": "Wrong Answer",
                        "verdict": "Wrong Answer"
                    })
                else:
                    results.append({
                        "input": test_case.input_data,
                        "expected_output": expected_output,
                        "actual_output": actual_output,
                        "stderr": stderr,
                        "status": "Accepted",
                        "verdict": "Accepted"
                    })

            final_verdict = "Accepted" if all_passed else "Wrong Answer"

            if request.user.is_authenticated:
                Submission.objects.create(
                    user=request.user,
                    problem=problem,
                    code=source_code,
                    language=language,
                    verdict=final_verdict
                )

            return JsonResponse({
                "verdict": final_verdict,
                "results": results
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed."}, status=405)


@login_required
def submission_history(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    submissions = Submission.objects.filter(user=request.user, problem=problem).order_by('-submitted_at')
    return render(request, 'compiler/submission_history.html', {
        'problem': problem,
        'submissions': submissions
    })


@login_required
def submission_detail(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    if submission.user != request.user and not request.user.is_staff:
        return render(request, "403.html", status=403)

    return render(request, "compiler/submission_detail.html", {
        "submission": submission
    })
