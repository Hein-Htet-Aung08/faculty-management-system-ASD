RESOURCES = {
    "performance-reviews": {
        "table": "PerformanceReviews",
        "pk": "reviewID",
        "fields": (
            "staffID", "reviewDate", "reviewerID", "rating", "feedback", "status"
        ),
        "filters": ("staffID", "reviewerID", "status"),
        "order_by": "reviewDate DESC, reviewID DESC",
    },
    "development-goals": {
        "table": "DevelopmentGoals",
        "pk": "goalID",
        "fields": (
            "staffID", "title", "description", "targetDate", "progress", "status"
        ),
        "filters": ("staffID", "status"),
        "order_by": "targetDate IS NULL, targetDate, goalID",
    },
    "training-programs": {
        "table": "TrainingPrograms",
        "pk": "trainingID",
        "fields": (
            "title", "description", "provider", "startDate", "endDate", "skillArea"
        ),
        "filters": ("provider", "skillArea"),
        "order_by": "startDate IS NULL, startDate, trainingID",
    },
    "staff-training": {
        "table": "StaffTraining",
        "pk": "staffTrainingID",
        "fields": (
            "staffID", "trainingID", "enrolmentDate", "completionDate", "status"
        ),
        "filters": ("staffID", "trainingID", "status"),
        "order_by": "enrolmentDate DESC, staffTrainingID DESC",
    },
    "development-recommendations": {
        "table": "DevelopmentRecommendations",
        "pk": "recommendationID",
        "fields": (
            "staffID", "goalID", "recommendationType", "recommendation",
            "rationale", "dateGenerated", "status"
        ),
        "filters": ("staffID", "goalID", "recommendationType", "status"),
        "order_by": "dateGenerated DESC, recommendationID DESC",
    },
}


def get_resource(slug):
    return RESOURCES.get(slug)
