from csv import DictReader
from datetime import datetime
from io import TextIOWrapper

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile

from user.models import ContactGroup, Contacts

User = get_user_model()


def create_contacts_from_csv_file(file: InMemoryUploadedFile, user: User):
    text_file = TextIOWrapper(file.file, encoding='utf-8')
    reader = DictReader(text_file)
    errors = {}
    counter = 1
    contacts_objects = []
    for row in reader:
        data = dict(row)
        first_name = data.pop("First Name", "")
        middle_name = data.pop("Middle Name", "")
        last_name = data.pop("Last Name", "")
        if not any({first_name, middle_name, last_name}):
            errors[counter] = ["Name not found"]
            continue
        name = f"{first_name} {middle_name} {last_name}"
        data["pay_first_remarks"] = f"Imported on {datetime.now()}"
        data["row"] = counter
        contact_object = Contacts(
            name=name, owner=user, data=data
        )
        contacts_objects.append(contact_object)
        counter += 1
    contacts = Contacts.objects.bulk_create(contacts_objects)
    all_contacts = Contacts.objects.filter(
        owner=user
    ).exclude(data__Labels="")
    contact_groups_data = {}
    for contact in all_contacts:
        data = contact.data
        labels = data.pop("Labels", "")
        labels_list = labels.split(" ::: ")
        groups = []
        for label in labels_list:
            if label in contact_groups_data:
                groups.append(contact_groups_data[label])
                continue
            group, _ = ContactGroup.objects.get_or_create(
                name=label, owner=user
            )
            groups.append(group)
            contact_groups_data[label] = group
        contact.groups.set(groups)
        contact.data = data
        contact.save()
    return contacts, errors
