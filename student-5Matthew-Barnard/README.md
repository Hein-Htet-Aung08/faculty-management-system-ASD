# Performance & Professional Development Management

This microservice handles staff performance tracking, development planning, training enrolment, and personalised learning recommendations for the Faculty Management System.

## Purpose

The feature supports the management of:

- Performance reviews
- Development goals
- Training programs
- Staff training enrolments
- Development recommendations

This module is designed to help faculty managers and HR staff monitor staff growth, identify skills gaps, and plan suitable professional development activities.

## Planned API Functionality

The backend will eventually provide CRUD REST endpoints for:

- Performance Reviews
- Development Goals
- Training Programs
- Staff Training
- Development Recommendations

## Planned Database Tables

### PerformanceReviews
- reviewID
- staffID
- reviewDate
- reviewerID
- rating
- feedback
- status

### DevelopmentGoals
- goalID
- staffID
- title
- description
- targetDate
- progress
- status

### TrainingPrograms
- trainingID
- title
- description
- provider
- startDate
- endDate
- skillArea

### StaffTraining
- staffTrainingID
- staffID
- trainingID
- enrolmentDate
- completionDate
- status

### DevelopmentRecommendations
- recommendationID
- staffID
- goalID
- recommendationType
- recommendation
- rationale
- dateGenerated
- status

## Future Intelligence Layer

Later, this service may use an approved large language model (LLM) to analyse staff performance, skills, roles, and goals to recommend personalised training and development activities.

## Current Starter State

This folder currently contains:

- a Flask backend skeleton with placeholder API routes
- a SQLite database schema for the required tables
- a minimal frontend shell for future UI integration
- a Dockerfile for local containerisation

## Scope

This microservice is focused only on performance and professional development management within the broader faculty system.
