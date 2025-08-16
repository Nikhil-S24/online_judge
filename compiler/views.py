from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from problems.models import Problem, TestCase
from .models import Submission
from django.conf import settings
import requests
import json

JUDGE0_URL = "https://judge0-ce.p.rapidapi.com/submissions"
HEADERS = {
    "content-type": "application/json",
    "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
    "X-RapidAPI-Key": settings.RAPIDAPI_KEY
}

def run_code_with_judge0(source_code, language_id, stdin):
    payload = {
        "source_code": source_code,
        "language_id": int(language_id),
        "stdin": stdin
    }
    response = requests.post(
        JUDGE0_URL,
        json=payload,
        headers=HEADERS,
        params={"base64_encoded": "false", "wait": "true"}
    )
    return response.json()

@login_required
def compile_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    try:
        data = json.loads(request.body)
        problem_id = data.get("problem_id")
        source_code = data.get("source_code")
        language = int(data.get("language"))
        problem = get_object_or_404(Problem, id=problem_id)
        test_cases = TestCase.objects.filter(problem=problem)

        results = []
        verdict = "Accepted"

        for tc in test_cases:
            result = run_code_with_judge0(source_code, language, tc.input_data or "")
            actual_output = (result.get("stdout") or "").strip()
            expected_output = (tc.expected_output or "").strip()
            stderr = (result.get("stderr") or "").strip()
            compile_output = (result.get("compile_output") or "").strip()

            if compile_output:
                verdict = "Compilation Error"
                results.append({
                    "input": tc.input_data or "",
                    "expected_output": expected_output,
                    "actual_output": actual_output,
                    "stderr": stderr,
                    "compile_output": compile_output,
                    "status": "Compilation Error"
                })
                break

            status = "Passed" if actual_output == expected_output else "Failed"
            if status == "Failed":
                verdict = "Wrong Answer"

            results.append({
                "input": tc.input_data or "",
                "expected_output": expected_output,
                "actual_output": actual_output,
                "stderr": stderr,
                "compile_output": compile_output,
                "status": status
            })

        return JsonResponse({"verdict": verdict, "results": results})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def submit_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    try:
        data = json.loads(request.body)
        problem_id = data.get("problem_id")
        source_code = data.get("source_code")
        language = int(data.get("language"))
        problem = get_object_or_404(Problem, id=problem_id)
        test_cases = TestCase.objects.filter(problem=problem)

        results = []
        verdict = "Accepted"

        for tc in test_cases:
            result = run_code_with_judge0(source_code, language, tc.input_data or "")
            
            print("JUDGE0 RESPONSE:", result) 
            actual_output = (result.get("stdout") or "").strip()
            expected_output = (tc.expected_output or "").strip()
            stderr = (result.get("stderr") or "").strip()
            compile_output = (result.get("compile_output") or "").strip()

            if compile_output:
                verdict = "Compilation Error"
                # ... (rest of the function is the same)
                break

            status = "Passed" if actual_output == expected_output else "Failed"
            if status == "Failed":
                verdict = "Wrong Answer"

            results.append({
                "input": tc.input_data or "",
                "expected_output": expected_output,
                "actual_output": actual_output,
                "stderr": stderr,
                "compile_output": compile_output,
                "status": status
            })

        Submission.objects.create(
            user=request.user,
            problem=problem,
            code=source_code,
            language=language,
            verdict=verdict,
            submitted_at=timezone.now()
        )

        return JsonResponse({"verdict": verdict, "results": results})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def run_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    try:
        data = json.loads(request.body)
        source_code = data.get("source_code")
        language = int(data.get("language"))
        custom_input = data.get("stdin", "")
        expected_output = data.get("expected_output", "").strip()

        result = run_code_with_judge0(source_code, language, custom_input)

        stdout = (result.get("stdout") or "").strip()
        stderr = (result.get("stderr") or "").strip()
        compile_output = (result.get("compile_output") or "").strip()

        
        verdict = None
        if expected_output:
            if compile_output or stderr:
                verdict = "Runtime Error"
            elif stdout == expected_output:
                verdict = "Accepted"
            else:
                verdict = "Wrong Answer"

        return JsonResponse({
            "stdout": stdout,
            "stderr": stderr,
            "compile_output": compile_output,
            "verdict": verdict 
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@login_required
def view_all_submissions(request):
    submissions = Submission.objects.filter(user=request.user).order_by("-submitted_at")
    return render(request, "compiler/all_submissions.html", {"submissions": submissions})

@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(Submission, pk=pk, user=request.user)
    return render(request, "compiler/submission_detail.html", {"submission": submission})
