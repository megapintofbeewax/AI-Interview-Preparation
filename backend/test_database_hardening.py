import os
import sys
import unittest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, Base
from app.models import (
    User, Profile, Resume, ResumeAnalysis, JobRole, Skill,
    Interview, Question, Answer, Evaluation, Feedback, Recommendation
)
from app.auth import hash_password
from fastapi.testclient import TestClient
from app.main import app

class DatabaseHardeningTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_sqlite_pragmas(self):
        """Verify SQLite foreign_keys=ON and WAL mode are enforced."""
        with engine.connect() as conn:
            fk_res = conn.execute(text("PRAGMA foreign_keys;")).scalar()
            self.assertEqual(fk_res, 1, "Foreign key constraints must be active (PRAGMA foreign_keys=1)")

            jm_res = conn.execute(text("PRAGMA journal_mode;")).scalar()
            self.assertIn(str(jm_res).lower(), ["wal", "memory"], "Journal mode should be WAL for concurrent access")
        print("[PASS] test_01_sqlite_pragmas: SQLite PRAGMAs foreign_keys=ON and journal_mode=WAL verified.")

    def test_02_seed_catalogs_present(self):
        """Verify JobRole and Skill catalog tables are populated."""
        roles_count = self.db.query(JobRole).count()
        self.assertGreaterEqual(roles_count, 5, "At least 5 standard job roles must be seeded")

        skills_count = self.db.query(Skill).count()
        self.assertGreaterEqual(skills_count, 5, "At least 5 standard skills must be seeded")

        sw_dev = self.db.query(JobRole).filter(JobRole.name == "Software Developer").first()
        self.assertIsNotNone(sw_dev)

        python_skill = self.db.query(Skill).filter(Skill.name == "Python").first()
        self.assertIsNotNone(python_skill)
        print(f"[PASS] test_02_seed_catalogs_present: Catalogs seeded ({roles_count} roles, {skills_count} skills).")

    def test_03_full_entity_relational_graph(self):
        """Create a full entity graph: User -> Profile, Resume -> ResumeAnalysis, Interview -> Questions -> Answers -> Evaluations -> Feedback -> Recommendations."""
        # 1. User
        email = "hardening_test@example.com"
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            self.db.delete(existing)
            self.db.commit()

        user = User(
            name="Hardening Candidate",
            email=email,
            hashed_password=hash_password("HardeningPass123")
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # 2. Profile
        profile = Profile(
            user_id=user.id,
            education="B.Tech Computer Science",
            target_role="Software Developer",
            skills="Python, SQL, System Design"
        )
        self.db.add(profile)

        # 3. Resume
        resume = Resume(
            user_id=user.id,
            filename="candidate_resume.pdf",
            file_path="uploads/candidate_resume.pdf",
            file_type="application/pdf",
            file_size=2048,
            raw_text="Experienced Python developer with FastAPI and SQL skills."
        )
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)

        # 4. ResumeAnalysis
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            user_id=user.id,
            skills='["Python", "FastAPI", "SQL"]',
            projects='["Interview Platform"]',
            education="B.Tech CS",
            technologies='["Git", "Docker"]'
        )
        self.db.add(analysis)

        # 5. Interview
        interview = Interview(
            user_id=user.id,
            resume_id=resume.id,
            target_role="Software Developer",
            interview_type="Technical",
            difficulty="Medium",
            num_questions=2,
            status="completed",
            overall_score=85
        )
        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)

        # 6. Questions
        q1 = Question(
            interview_id=interview.id,
            question_index=1,
            question_text="Explain Python GIL and its concurrency implications.",
            category="Technical",
            difficulty="Medium"
        )
        q2 = Question(
            interview_id=interview.id,
            question_index=2,
            question_text="How do database indexes improve query performance?",
            category="Technical",
            difficulty="Medium"
        )
        self.db.add_all([q1, q2])
        self.db.commit()
        self.db.refresh(q1)
        self.db.refresh(q2)

        # 7. Answers
        a1 = Answer(
            interview_id=interview.id,
            question_id=q1.id,
            user_id=user.id,
            transcript="The GIL ensures only one thread executes Python bytecode at a time.",
            duration_seconds=35
        )
        a2 = Answer(
            interview_id=interview.id,
            question_id=q2.id,
            user_id=user.id,
            transcript="Indexes use B-trees to enable logarithmic lookup times instead of full table scans.",
            duration_seconds=42
        )
        self.db.add_all([a1, a2])
        self.db.commit()
        self.db.refresh(a1)
        self.db.refresh(a2)

        # 8. Evaluations
        e1 = Evaluation(
            interview_id=interview.id,
            question_id=q1.id,
            answer_id=a1.id,
            relevance_score=9,
            technical_accuracy_score=8,
            completeness_score=8,
            clarity_score=9,
            overall_score=8.5,
            feedback="Strong technical explanation of GIL locking."
        )
        e2 = Evaluation(
            interview_id=interview.id,
            question_id=q2.id,
            answer_id=a2.id,
            relevance_score=9,
            technical_accuracy_score=9,
            completeness_score=8,
            clarity_score=8,
            overall_score=8.5,
            feedback="Clear explanation of B-tree index structures."
        )
        self.db.add_all([e1, e2])

        # 9. Feedback
        fb = Feedback(
            interview_id=interview.id,
            overall_score=85,
            strong_areas='["Python", "Databases"]',
            weak_areas='["Async Concurrency"]',
            summary="Solid performance across core software engineering topics."
        )
        self.db.add(fb)

        # 10. Recommendations
        rec1 = Recommendation(
            interview_id=interview.id,
            step_number=1,
            title="Practice multiprocessing vs threading",
            description="Explore multiprocessing for CPU-bound tasks in Python.",
            category="Concurrency"
        )
        self.db.add(rec1)
        self.db.commit()

        # Verify bidirectional navigation across all entities
        self.db.refresh(user)
        self.assertEqual(user.profile.target_role, "Software Developer")
        self.assertEqual(len(user.resumes), 1)
        self.assertEqual(user.resumes[0].analysis.education, "B.Tech CS")
        self.assertEqual(len(user.interviews), 1)
        self.assertEqual(len(user.interviews[0].questions), 2)
        self.assertEqual(len(user.interviews[0].answers), 2)
        self.assertEqual(len(user.interviews[0].evaluations), 2)
        self.assertIsNotNone(user.interviews[0].feedback_report)
        self.assertEqual(len(user.interviews[0].recommendation_items), 1)

        print("[PASS] test_03_full_entity_relational_graph: All 11 entities created and bidirectional relationships verified.")

    def test_04_cascade_delete_question(self):
        """Deleting a Question must cascade-delete its Answer and Evaluation."""
        user = self.db.query(User).filter(User.email == "hardening_test@example.com").first()
        self.assertIsNotNone(user)
        interview = user.interviews[0]

        q2 = self.db.query(Question).filter(
            Question.interview_id == interview.id,
            Question.question_index == 2
        ).first()
        self.assertIsNotNone(q2)
        q2_id = q2.id

        ans_count_before = self.db.query(Answer).filter(Answer.question_id == q2_id).count()
        eval_count_before = self.db.query(Evaluation).filter(Evaluation.question_id == q2_id).count()
        self.assertEqual(ans_count_before, 1)
        self.assertEqual(eval_count_before, 1)

        # Delete question
        self.db.delete(q2)
        self.db.commit()

        # Verify cascade
        ans_count_after = self.db.query(Answer).filter(Answer.question_id == q2_id).count()
        eval_count_after = self.db.query(Evaluation).filter(Evaluation.question_id == q2_id).count()
        self.assertEqual(ans_count_after, 0, "Answers must cascade-delete when Question is deleted")
        self.assertEqual(eval_count_after, 0, "Evaluations must cascade-delete when Question is deleted")

        print("[PASS] test_04_cascade_delete_question: Question deletion correctly cascade-deleted Answer and Evaluation.")

    def test_05_resume_deletion_set_null_on_interview(self):
        """Deleting a Resume must cascade-delete ResumeAnalysis, but preserve Interview with resume_id=None."""
        user = self.db.query(User).filter(User.email == "hardening_test@example.com").first()
        self.assertIsNotNone(user)
        resume = user.resumes[0]
        resume_id = resume.id
        interview = user.interviews[0]
        interview_id = interview.id

        # Verify analysis exists
        self.assertIsNotNone(resume.analysis)
        analysis_id = resume.analysis.id

        # Delete resume
        self.db.delete(resume)
        self.db.commit()

        # Check ResumeAnalysis is cascade deleted
        deleted_analysis = self.db.query(ResumeAnalysis).filter(ResumeAnalysis.id == analysis_id).first()
        self.assertIsNone(deleted_analysis, "ResumeAnalysis must cascade delete when Resume is deleted")

        # Check Interview still exists and resume_id is null/None
        updated_interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        self.assertIsNotNone(updated_interview, "Interview must persist when Resume is deleted")
        self.assertIsNone(updated_interview.resume_id, "Interview resume_id must be set to NULL")

        print("[PASS] test_05_resume_deletion_set_null_on_interview: Resume cascade and SET NULL on Interview verified.")

    def test_06_cascade_delete_user(self):
        """Deleting a User must cascade-delete Profile, Resume, Interview, and all child session records."""
        user = self.db.query(User).filter(User.email == "hardening_test@example.com").first()
        self.assertIsNotNone(user)
        user_id = user.id
        interview_id = user.interviews[0].id

        self.db.delete(user)
        self.db.commit()

        # Verify all child entities are removed
        self.assertIsNone(self.db.query(User).filter(User.id == user_id).first())
        self.assertEqual(self.db.query(Profile).filter(Profile.user_id == user_id).count(), 0)
        self.assertEqual(self.db.query(Interview).filter(Interview.user_id == user_id).count(), 0)
        self.assertEqual(self.db.query(Question).filter(Question.interview_id == interview_id).count(), 0)
        self.assertEqual(self.db.query(Answer).filter(Answer.interview_id == interview_id).count(), 0)
        self.assertEqual(self.db.query(Evaluation).filter(Evaluation.interview_id == interview_id).count(), 0)
        self.assertEqual(self.db.query(Feedback).filter(Feedback.interview_id == interview_id).count(), 0)
        self.assertEqual(self.db.query(Recommendation).filter(Recommendation.interview_id == interview_id).count(), 0)

        print("[PASS] test_06_cascade_delete_user: User deletion cleanly cascaded to all 10 child tables.")

    def test_07_unique_constraint_and_rollback(self):
        """Verify duplicate unique constraint violation triggers IntegrityError and rolls back cleanly."""
        user1 = User(
            name="Unique Test 1",
            email="unique_constraint_test@example.com",
            hashed_password=hash_password("pass12345")
        )
        self.db.add(user1)
        self.db.commit()

        user2 = User(
            name="Unique Test 2",
            email="unique_constraint_test@example.com",
            hashed_password=hash_password("pass12345")
        )
        self.db.add(user2)
        with self.assertRaises(IntegrityError):
            self.db.commit()

        self.db.rollback()

        # Cleanup
        self.db.delete(user1)
        self.db.commit()
        print("[PASS] test_07_unique_constraint_and_rollback: IntegrityError raised and rollback succeeded.")

    def test_08_api_catalog_endpoints(self):
        """Verify API endpoints for roles and skills catalog."""
        # Roles endpoint
        res_roles = self.client.get("/api/interview/roles")
        self.assertEqual(res_roles.status_code, 200)
        data_roles = res_roles.json()
        self.assertIn("roles", data_roles)
        self.assertIn("Software Developer", data_roles["roles"])

        # Skills endpoint
        res_skills = self.client.get("/api/interview/skills")
        self.assertEqual(res_skills.status_code, 200)
        data_skills = res_skills.json()
        self.assertIn("skills", data_skills)
        skill_names = [s["name"] for s in data_skills["skills"]]
        self.assertIn("Python", skill_names)

        print("[PASS] test_08_api_catalog_endpoints: GET /api/interview/roles and GET /api/interview/skills returned seeded catalogs.")

if __name__ == "__main__":
    unittest.main()
