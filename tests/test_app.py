import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class", 
                             "Basketball Team", "Tennis Club", "Drama Club", 
                             "Art Studio", "Debate Team", "Science Club"]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        for activity in expected_activities:
            assert activity in data
    
    def test_get_activities_includes_participant_info(self, client):
        # Arrange & Act
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        chess_club = data["Chess Club"]
        assert "participants" in chess_club
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
        assert len(chess_club["participants"]) == 2
    
    def test_get_activities_includes_required_fields(self, client):
        # Arrange & Act
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        programming_class = data["Programming Class"]
        assert "description" in programming_class
        assert "schedule" in programming_class
        assert "max_participants" in programming_class
        assert "participants" in programming_class


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify participant was added
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
    
    def test_signup_duplicate_student_fails(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"
    
    def test_signup_nonexistent_activity_fails(self, client):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_multiple_students_to_same_activity(self, client):
        # Arrange
        activity_name = "Programming Class"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Act
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        for email in emails:
            assert email in participants
    
    def test_signup_student_to_multiple_activities(self, client):
        # Arrange
        email = "versatile@mergington.edu"
        activities_list = ["Chess Club", "Programming Class", "Drama Club"]
        
        # Act
        for activity_name in activities_list:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert
        activities_response = client.get("/activities")
        data = activities_response.json()
        for activity_name in activities_list:
            assert email in data[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]
    
    def test_unregister_nonparticipant_fails(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"
    
    def test_unregister_from_nonexistent_activity_fails(self, client):
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_and_resign_up(self, client):
        # Arrange
        activity_name = "Tennis Club"
        email = "james@mergington.edu"
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert unregister worked
        assert unregister_response.status_code == 200
        
        # Act - Sign up again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert signup worked
        assert signup_response.status_code == 200
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
    
    def test_unregister_one_of_many_participants(self, client):
        # Arrange
        activity_name = "Science Club"
        email_to_remove = "ethan@mergington.edu"
        email_to_keep = "ava@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email_to_remove not in participants
        assert email_to_keep in participants


class TestIntegrationScenarios:
    """Integration tests covering complex user scenarios"""
    
    def test_full_signup_and_unregister_workflow(self, client):
        # Arrange - new student wants to join and leave an activity
        activity_name = "Art Studio"
        email = "newartist@mergington.edu"
        
        # Act 1 - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert signup
        assert signup_response.status_code == 200
        activities_check1 = client.get("/activities").json()
        assert email in activities_check1[activity_name]["participants"]
        initial_count = len(activities_check1[activity_name]["participants"])
        
        # Act 2 - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert unregister
        assert unregister_response.status_code == 200
        activities_check2 = client.get("/activities").json()
        assert email not in activities_check2[activity_name]["participants"]
        assert len(activities_check2[activity_name]["participants"]) == initial_count - 1
    
    def test_concurrent_signups_dont_allow_duplicates(self, client):
        # Arrange
        activity_name = "Debate Team"
        email = "debater@mergington.edu"
        
        # Act - Try to sign up the same student twice
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 400
        assert response2.json()["detail"] == "Student already signed up for this activity"
        
        # Verify student is only in the list once
        activities_response = client.get("/activities").json()
        count = activities_response[activity_name]["participants"].count(email)
        assert count == 1
