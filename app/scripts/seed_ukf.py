import asyncio

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


async def main() -> None:
    async with AsyncSessionLocal() as db:
        created_college = False
        created_departments = 0
        seeded_batches = 0

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

        print(
            "UKF seed complete: "
            f"college_created={created_college}, "
            f"departments_created={created_departments}, "
            f"batches_created={seeded_batches}"
        )


if __name__ == "__main__":
    asyncio.run(main())
