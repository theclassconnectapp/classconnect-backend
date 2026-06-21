from uuid import uuid4

from app.scripts import seed_ukf


def test_create_general_groups_is_idempotent(monkeypatch):
    firestore_client = FakeFirestoreClient()
    monkeypatch.setattr(seed_ukf, "_get_firebase_app", lambda: object())
    monkeypatch.setattr(seed_ukf.firestore, "client", lambda app: firestore_client)

    batch_info = _batch_info(label="2025-2029")

    assert seed_ukf.create_general_groups([batch_info]) == 1
    assert seed_ukf.create_general_groups([batch_info]) == 0

    group_ref = firestore_client.collection("colleges/ukf/groups").document(
        f"{batch_info.batch_id}_general"
    )
    assert group_ref.set_count == 1
    assert group_ref.data["batchId"] == str(batch_info.batch_id)
    assert group_ref.data["isGeneral"] is True


def test_create_general_groups_leaves_existing_group_untouched(monkeypatch):
    firestore_client = FakeFirestoreClient()
    monkeypatch.setattr(seed_ukf, "_get_firebase_app", lambda: object())
    monkeypatch.setattr(seed_ukf.firestore, "client", lambda app: firestore_client)

    batch_info = _batch_info(label="2024-2028")
    group_id = f"{batch_info.batch_id}_general"
    group_ref = firestore_client.collection("colleges/ukf/groups").document(group_id)
    existing_data = {
        "id": group_id,
        "name": "General With Real Activity",
        "members": ["student-1"],
        "lastMessageText": "do not overwrite me",
    }
    group_ref.data = existing_data.copy()

    assert seed_ukf.create_general_groups([batch_info]) == 0

    assert group_ref.set_count == 0
    assert group_ref.delete_count == 0
    assert group_ref.data == existing_data


def _batch_info(label: str) -> seed_ukf.BatchInfo:
    return seed_ukf.BatchInfo(
        department_id=uuid4(),
        department_name="Computer Science",
        batch_id=uuid4(),
        label=label,
    )


class FakeFirestoreClient:
    def __init__(self):
        self.collections = {}

    def collection(self, path):
        if path not in self.collections:
            self.collections[path] = FakeCollectionReference()
        return self.collections[path]


class FakeCollectionReference:
    def __init__(self):
        self.documents = {}

    def document(self, document_id):
        if document_id not in self.documents:
            self.documents[document_id] = FakeDocumentReference()
        return self.documents[document_id]


class FakeDocumentReference:
    def __init__(self):
        self.data = None
        self.set_count = 0
        self.delete_count = 0

    def get(self):
        return FakeDocumentSnapshot(exists=self.data is not None)

    def set(self, data):
        self.data = data.copy()
        self.set_count += 1

    def delete(self):
        self.delete_count += 1
        self.data = None


class FakeDocumentSnapshot:
    def __init__(self, exists):
        self.exists = exists
