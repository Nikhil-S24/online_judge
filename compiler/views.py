from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from problems.models import Problem, TestCase
from .models import Submission
from django.conf import settings
import subprocess
import tempfile
import os
import json
 
# --- NEW, MULTI-LANGUAGE SUBPROCESS FUNCTION ---
def run_code_with_subprocess(source_code, language, stdin):
    """
    Saves source code to a temporary file and runs it using subprocess.
    Now supports Python, Java, C++, and JavaScript.
    WARNING: This remains a highly insecure method for demonstration only.
    """
    # Define language configurations
    # IDs match the values in your problem_detail.html template
    lang_config = {
        "71": { # Python
            "extension": ".py",
            "compile_cmd": None,
            "run_cmd": ["python", "{filepath}"]
        },
        "54": { # C++
            "extension": ".cpp",
            "compile_cmd": ["g++", "{filepath}", "-o", "{executablepath}"],
            "run_cmd": ["{executablepath}"]
        },
        "62": { # Java
            # Note: Java source file MUST be named Main.java
            "extension": ".java",
            "compile_cmd": ["javac", "{filepath}"],
            "run_cmd": ["java", "-classpath", "{dirpath}", "Main"]
        },
        "63": { # JavaScript
            "extension": ".js",
            "compile_cmd": None,
            "run_cmd": ["node", "{filepath}"]
        }
    }

    config = lang_config.get(language)
    if not config:
        return {"compile_output": "Language not supported.", "stderr": "", "stdout": ""}

    # Create a temporary directory to store all related files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Determine file paths
        filename = "Main.java" if language == "62" else f"script{config['extension']}"
        filepath = os.path.join(temp_dir, filename)
        executablepath = os.path.join(temp_dir, "a.out")

        # Write the source code to the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(source_code)

        # --- Compilation Step (if necessary) ---
        if config["compile_cmd"]:
            compile_command = [
                part.format(filepath=filepath, executablepath=executablepath)
                for part in config["compile_cmd"]
            ]
            try:
                compile_result = subprocess.run(
                    compile_command,
                    capture_output=True,
                    text=True,
                    timeout=10 # 10-second timeout for compilation
                )
                if compile_result.returncode != 0:
                    # Compilation failed
                    return {
                        "compile_output": compile_result.stderr,
                        "stderr": "",
                        "stdout": ""
                    }
            except subprocess.TimeoutExpired:
                return {"compile_output": "Compilation Timed Out", "stderr": "", "stdout": ""}
            except Exception as e:
                return {"compile_output": f"Compilation error: {str(e)}", "stderr": "", "stdout": ""}

        # --- Execution Step ---
        run_command = [
            part.format(filepath=filepath, executablepath=executablepath, dirpath=temp_dir)
            for part in config["run_cmd"]
        ]
        normalized_stdin = (stdin or "").replace('\r\n', '\n')
        
        try:
            run_result = subprocess.run(
                run_command,
                input=normalized_stdin,
                capture_output=True,
                text=True,
                timeout=5 # 5-second timeout for execution
            )
            return {
                "stdout": run_result.stdout,
                "stderr": run_result.stderr,
                "compile_output": "" # Compilation was successful if we reached this point
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Time Limit Exceeded", "compile_output": ""}
        except Exception as e:
            return {"stdout": "", "stderr": f"An unexpected error occurred: {str(e)}", "compile_output": ""}

# --- VIEWS (no major changes needed, they use the function above) ---

@login_required
def compile_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    try:
        data = json.loads(request.body)
        problem_id = data.get("problem_id")
        source_code = data.get("source_code")
        language = data.get("language")
        problem = get_object_or_404(Problem, id=problem_id)
        test_cases = TestCase.objects.filter(problem=problem)
        results = []
        verdict = "Accepted"
        for tc in test_cases:
            result = run_code_with_subprocess(source_code, language, tc.input_data or "")
            actual_output = (result.get("stdout") or "").strip()
            expected_output = (tc.expected_output or "").strip().replace('\r\n', '\n')
            stderr = (result.get("stderr") or "").strip()
            compile_output = (result.get("compile_output") or "").strip()
            if compile_output:
                verdict, status = "Compilation Error", "Compilation Error"
            elif "Time Limit Exceeded" in stderr:
                verdict, status = "Time Limit Exceeded", "Time Limit Exceeded"
            elif stderr:
                verdict, status = "Runtime Error", "Runtime Error"
            else:
                status = "Passed" if actual_output == expected_output else "Failed"
                if status == "Failed": verdict = "Wrong Answer"
            results.append({
                "input": tc.input_data or "", "expected_output": expected_output,
                "actual_output": actual_output, "stderr": stderr,
                "compile_output": compile_output, "status": status
            })
            if verdict != "Accepted": break
        return JsonResponse({"verdict": verdict, "results": results})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def submit_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    response = compile_code(request)
    if response.status_code == 200:
        data = json.loads(request.body)
        verdict_data = json.loads(response.content)
        Submission.objects.create(
            user=request.user,
            problem=get_object_or_404(Problem, id=data.get("problem_id")),
            code=data.get("source_code"),
            language=data.get("language"),
            verdict=verdict_data.get("verdict"),
            submitted_at=timezone.now()
        )
    return response

@login_required
def run_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    try:
        data = json.loads(request.body)
        source_code = data.get("source_code")
        language = data.get("language")
        custom_input = data.get("stdin", "")
        expected_output = data.get("expected_output", "").strip().replace('\r\n', '\n')
        result = run_code_with_subprocess(source_code, language, custom_input)
        stdout = (result.get("stdout") or "").strip()
        stderr = (result.get("stderr") or "").strip()
        compile_output = (result.get("compile_output") or "").strip()
        verdict = None
        if expected_output:
            if compile_output: verdict = "Compilation Error"
            elif "Time Limit Exceeded" in stderr: verdict = "Time Limit Exceeded"
            elif stderr: verdict = "Runtime Error"
            elif stdout == expected_output: verdict = "Accepted"
            else: verdict = "Wrong Answer"
        return JsonResponse({
            "stdout": stdout, "stderr": stderr,
            "compile_output": compile_output, "verdict": verdict
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