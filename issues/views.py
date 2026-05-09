import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from issues.models import Reporter, Issue, CriticalIssue, LowPriorityIssue
from issues import storage

REPORTERS_FILE = "reporters.json"
ISSUES_FILE = "issues.json"


# ---------------------------------------------------------------------------
# Reporters
# ---------------------------------------------------------------------------


@csrf_exempt
def reporters_view(request):
    if request.method == "GET":
        return _get_reporters(request)
    if request.method == "POST":
        return _create_reporter(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


def _get_reporters(request):
    reporters = storage.load(REPORTERS_FILE)
    reporter_id = request.GET.get("id")

    if reporter_id is not None:
        try:
            reporter_id = int(reporter_id)
        except ValueError:
            return JsonResponse({"error": "id must be an integer"}, status=400)
        for r in reporters:
            if r["id"] == reporter_id:
                return JsonResponse(r, status=200)
        return JsonResponse({"error": "Reporter not found"}, status=404)

    return JsonResponse(reporters, safe=False, status=200)


def _create_reporter(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required = ("id", "name", "email", "team")
    for field in required:
        if field not in data:
            return JsonResponse({"error": f"Missing field: {field}"}, status=400)

    reporter = Reporter(
        id=data["id"],
        name=data["name"],
        email=data["email"],
        team=data["team"],
    )

    try:
        reporter.validate()
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    reporters = storage.load(REPORTERS_FILE)
    if any(r["id"] == reporter.id for r in reporters):
        return JsonResponse(
            {"error": f"Reporter with id {reporter.id} already exists"}, status=400
        )

    reporters.append(reporter.to_dict())
    storage.save(REPORTERS_FILE, reporters)
    return JsonResponse(reporter.to_dict(), status=201)


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------


@csrf_exempt
def issues_view(request):
    if request.method == "GET":
        return _get_issues(request)
    if request.method == "POST":
        return _create_issue(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


def _get_issues(request):
    issues = storage.load(ISSUES_FILE)

    issue_id = request.GET.get("id")
    status_filter = request.GET.get("status")

    if issue_id is not None:
        try:
            issue_id = int(issue_id)
        except ValueError:
            return JsonResponse({"error": "id must be an integer"}, status=400)
        for issue in issues:
            if issue["id"] == issue_id:
                return JsonResponse(issue, status=200)
        return JsonResponse({"error": "Issue not found"}, status=404)

    if status_filter is not None:
        filtered = [i for i in issues if i["status"] == status_filter]
        return JsonResponse(filtered, safe=False, status=200)

    return JsonResponse(issues, safe=False, status=200)


def _create_issue(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    required = ("id", "title", "description", "status", "priority", "reporter_id")
    for field in required:
        if field not in data:
            return JsonResponse({"error": f"Missing field: {field}"}, status=400)

    priority = data["priority"]
    kwargs = {
        "id": data["id"],
        "title": data["title"],
        "description": data["description"],
        "status": data["status"],
        "priority": priority,
        "reporter_id": data["reporter_id"],
    }

    if priority == "critical":
        issue = CriticalIssue(**kwargs)
    elif priority == "low":
        issue = LowPriorityIssue(**kwargs)
    else:
        issue = Issue(**kwargs)

    try:
        issue.validate()
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    issues = storage.load(ISSUES_FILE)
    if any(i["id"] == issue.id for i in issues):
        return JsonResponse(
            {"error": f"Issue with id {issue.id} already exists"}, status=400
        )

    response_data = issue.to_dict()
    response_data["message"] = issue.describe()

    issues.append(issue.to_dict())
    storage.save(ISSUES_FILE, issues)
    return JsonResponse(response_data, status=201)
