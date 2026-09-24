from datetime import time, timedelta

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.social_accounts.models import SocialAccount, SocialAccountStatus, SocialPlatform

from .models import ContentIdea


class ContentPlannerAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="planner-owner@example.com", first_name="Planner", password="password")
        self.other_user = User.objects.create_user(email="planner-other@example.com", first_name="Other", password="password")
        self.organization = self.create_organization("OWNER", self.user)
        self.other_organization = self.create_organization("OTHER", self.other_user)
        self.account = self.create_account(self.organization, "owner-account")
        self.other_account = self.create_account(self.other_organization, "other-account")
        self.client.force_authenticate(self.user)

    def create_organization(self, suffix, user):
        return Organization.objects.create(
            organization_id=f"ORG-PLANNER-{suffix}", name=f"Planner Organization {suffix}",
            slug=f"planner-organization-{suffix.lower()}", industry="Testing", created_by=user,
        )

    def create_account(self, organization, suffix, **overrides):
        defaults = {
            "organization": organization, "platform": SocialPlatform.INSTAGRAM,
            "platform_account_id": suffix, "account_name": suffix,
            "status": SocialAccountStatus.CONNECTED, "is_valid": True,
        }
        defaults.update(overrides)
        return SocialAccount.objects.create(**defaults)

    def payload(self, **overrides):
        data = {
            "organization": str(self.organization.id), "caption": "A planned launch post",
            "description": "Launch details", "content_type": "POST",
            "target_publish_date": (timezone.localdate() + timedelta(days=1)).isoformat(),
            "target_publish_time": "09:30:00", "social_account_ids": [str(self.account.id)],
        }
        data.update(overrides)
        return data

    def create_idea(self, **overrides):
        response = self.client.post("/api/content-planner/", self.payload(**overrides), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response

    def test_owner_isolation_applies_to_list_detail_and_organizations(self):
        other_idea = ContentIdea.objects.create(
            organization=self.other_organization, caption="Private idea", content_type="POST",
            target_publish_date=timezone.localdate(), target_publish_time=time(9, 0),
        )
        other_idea.selected_social_accounts.add(self.other_account)

        response = self.client.get("/api/content-planner/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["ideas"], [])
        self.assertEqual(response.data["data"]["organizations"], [{
            "id": str(self.organization.id), "organization_id": self.organization.organization_id,
            "name": self.organization.name,
        }])
        self.assertEqual(self.client.get(f"/api/content-planner/{other_idea.id}/").status_code, 404)
        self.assertEqual(self.client.post(
            "/api/content-planner/", self.payload(organization=str(self.other_organization.id)), format="json",
        ).status_code, 400)

    def test_create_accepts_valid_selected_accounts_and_exposes_organization_code(self):
        data = self.create_idea().data["data"]

        self.assertEqual(data["caption"], "A planned launch post")
        self.assertEqual(data["organization_code"], self.organization.organization_id)
        self.assertEqual(data["target_publish_time"], "09:30:00")
        self.assertEqual(data["selected_social_accounts"][0]["id"], str(self.account.id))
        self.assertNotIn("title", data)
        self.assertNotIn("platform", data)
        self.assertNotIn("goal", data)

    def test_rejects_account_from_another_organization(self):
        response = self.client.post(
            "/api/content-planner/", self.payload(social_account_ids=[str(self.other_account.id)]), format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("social_account_ids", response.data)

    def test_rejects_deleted_disconnected_and_invalid_accounts(self):
        invalid_states = (
            {"is_deleted": True}, {"status": SocialAccountStatus.DISCONNECTED}, {"is_valid": False},
        )
        for index, state in enumerate(invalid_states):
            with self.subTest(state=state):
                account = self.create_account(self.organization, f"invalid-{index}", **state)
                response = self.client.post(
                    "/api/content-planner/", self.payload(social_account_ids=[str(account.id)]), format="json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("social_account_ids", response.data)

    def test_update_replaces_fields_and_selected_accounts(self):
        idea_id = self.create_idea().data["data"]["id"]
        second_account = self.create_account(self.organization, "second-account")
        response = self.client.patch(
            f"/api/content-planner/{idea_id}/",
            {"caption": "Updated caption", "content_type": "REEL", "target_publish_time": "11:45:00", "social_account_ids": [str(second_account.id)]},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        idea = ContentIdea.objects.get(id=idea_id)
        self.assertEqual(idea.caption, "Updated caption")
        self.assertEqual(idea.content_type, "REEL")
        self.assertEqual(idea.target_publish_time, time(11, 45))
        self.assertEqual(list(idea.selected_social_accounts.all()), [second_account])

    def test_delete_remains_a_soft_delete(self):
        idea_id = self.create_idea().data["data"]["id"]
        response = self.client.delete(f"/api/content-planner/{idea_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ContentIdea.objects.get(id=idea_id).is_deleted)
        self.assertEqual(self.client.get(f"/api/content-planner/{idea_id}/").status_code, 404)

    def test_only_new_content_types_are_accepted(self):
        for content_type in ("CAROUSEL", "SHORT", "VIDEO"):
            with self.subTest(content_type=content_type):
                response = self.client.post("/api/content-planner/", self.payload(content_type=content_type), format="json")
                self.assertEqual(response.status_code, 400)
                self.assertIn("content_type", response.data)

    def test_legacy_content_is_preserved_but_must_be_updated_to_a_supported_type(self):
        legacy_idea = ContentIdea.objects.create(
            organization=self.organization, caption="Pre-redesign title", description="Legacy record",
            platform="INSTAGRAM", campaign_goal="ENGAGEMENT", content_type="CAROUSEL",
            target_publish_date=timezone.localdate(),
        )
        legacy_idea.selected_social_accounts.add(self.account)
        detail = self.client.get(f"/api/content-planner/{legacy_idea.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["data"]["caption"], "Pre-redesign title")
        self.assertEqual(detail.data["data"]["content_type"], "CAROUSEL")
        update = self.client.patch(f"/api/content-planner/{legacy_idea.id}/", {"caption": "Still legacy"}, format="json")
        self.assertEqual(update.status_code, 400)
        self.assertIn("content_type", update.data)


class ContentIdeaMigrationTests(TransactionTestCase):
    reset_sequences = True
    migrate_from = ("content_planner", "0001_initial")
    migrate_to = ("content_planner", "0002_redesign_content_idea")

    def setUp(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate([self.migrate_from])
        self.old_apps = self.executor.loader.project_state([self.migrate_from]).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_migration_renames_title_to_caption_without_losing_legacy_metadata(self):
        organization_model = self.old_apps.get_model("organizations", "Organization")
        content_idea_model = self.old_apps.get_model("content_planner", "ContentIdea")
        user = User.objects.create_user(email="migration-owner@example.com", first_name="Migration", password="password")
        organization = organization_model.objects.create(
            organization_id="ORG-PLANNER-MIGRATION", name="Planner Migration Organization",
            slug="planner-migration-organization", industry="Testing", created_by_id=user.id,
        )
        legacy_idea = content_idea_model.objects.create(
            organization_id=organization.id, title="Preserved legacy title", description="Legacy description",
            platform="INSTAGRAM", content_type="CAROUSEL", campaign_goal="ENGAGEMENT",
            target_publish_date=timezone.localdate(),
        )

        self.executor = MigrationExecutor(connection)
        self.executor.migrate([self.migrate_to])
        new_apps = self.executor.loader.project_state([self.migrate_to]).apps
        migrated_idea = new_apps.get_model("content_planner", "ContentIdea").objects.get(id=legacy_idea.id)

        self.assertEqual(migrated_idea.caption, "Preserved legacy title")
        self.assertEqual(migrated_idea.platform, "INSTAGRAM")
        self.assertEqual(migrated_idea.campaign_goal, "ENGAGEMENT")
        self.assertEqual(migrated_idea.content_type, "CAROUSEL")
        self.assertIsNone(migrated_idea.target_publish_time)
