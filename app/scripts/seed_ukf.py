import asyncio
import json
import os
from dataclasses import dataclass
from uuid import UUID

import firebase_admin
from firebase_admin import credentials, firestore
from sqlalchemy import select

from app.core.database.session import AsyncSessionLocal
from app.features.college.data.models.college_db import Batch, College, Department
from app.features.college.data.repositories.college_repository_impl import (
    create_department,
    seed_batches_for_department,
)

UKF_DEPARTMENTS = [
    {"slug": "cse", "name": "Computer Science", "code": "CSE"},
    {"slug": "ds", "name": "Data Science", "code": "DS"},
    {"slug": "ece", "name": "Electronics and Communication", "code": "ECE"},
    {"slug": "eee", "name": "Electrical and Electronics", "code": "EEE"},
    {"slug": "me", "name": "Mechanical Engineering", "code": "ME"},
    {"slug": "ce", "name": "Civil Engineering", "code": "CE"},
]


@dataclass(frozen=True)
class BatchInfo:
    department_id: UUID
    department_name: str
    batch_id: UUID
    label: str


def _get_firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        if not service_account_json:
            return None
        service_account_info = json.loads(service_account_json)
        credential = credentials.Certificate(service_account_info)
        return firebase_admin.initialize_app(credential)


def create_general_groups(batch_infos: list[BatchInfo]) -> int:
    app = _get_firebase_app()
    if app is None:
        print("Warning: FIREBASE_SERVICE_ACCOUNT_JSON is not set; skipping Firestore general group creation")
        return 0

    db = firestore.client(app=app)
    groups_ref = db.collection("colleges/ukf/groups")
    for doc in groups_ref.where("isGeneral", "==", True).stream():
        doc.reference.delete()

    created_count = 0
    for batch_info in batch_infos:
        group_id = f"{batch_info.batch_id}_general"
        group_ref = groups_ref.document(group_id)

        group_ref.set(
            {
                "id": group_id,
                "name": "General",
                "description": f"General group for {batch_info.label}",
                "collegeId": "ukf",
                "dept": batch_info.department_name,
                "batch": batch_info.label,
                "departmentId": str(batch_info.department_id),
                "batchId": str(batch_info.batch_id),
                "createdAt": firestore.SERVER_TIMESTAMP,
                "isGeneral": True,
                "archived": False,
                "members": [],
            }
        )
        created_count += 1
    return created_count


async def main() -> None:
    async with AsyncSessionLocal() as db:
        created_college = False
        created_departments = 0
        seeded_batches = 0
        batch_infos: list[BatchInfo] = []

        result = await db.execute(select(College).where(College.id == "ukf"))
        college = result.scalar_one_or_none()
        if college is None:
            college = College(id="ukf", name="UKF College of Engineering", code="UKF")
            db.add(college)
            await db.commit()
            created_college = True

        for item in UKF_DEPARTMENTS:
            result = await db.execute(
                select(Department).where(
                    Department.college_id == "ukf",
                    Department.slug == item["slug"],
                )
            )
            department = result.scalar_one_or_none()
            if department is None:
                department_entity = await create_department(
                    db,
                    "ukf",
                    item["slug"],
                    item["name"],
                    item["code"],
                    created_by=None,
                )
                department_id = department_entity.id
                created_departments += 1
            else:
                department_id = department.id

            result = await db.execute(select(Batch).where(Batch.department_id == department_id))
            existing_batches = result.scalars().all()
            if not existing_batches:
                batches = await seed_batches_for_department(db, department_id, start_year=2022, count=5)
                seeded_batches += len(batches)

            result = await db.execute(select(Batch).where(Batch.department_id == department_id))
            department_batches = result.scalars().all()
            batch_infos.extend(
                BatchInfo(
                    department_id=department_id,
                    department_name=item["name"],
                    batch_id=batch.id,
                    label=batch.label,
                )
                for batch in department_batches
            )

        general_groups_created = create_general_groups(batch_infos)

        print(
            "UKF seed complete: "
            f"college_created={created_college}, "
            f"departments_created={created_departments}, "
            f"batches_created={seeded_batches}, "
            f"general_groups_created={general_groups_created}"
        )


if __name__ == "__main__":
    asyncio.run(main())
