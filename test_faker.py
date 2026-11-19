from faker import Faker
fake = Faker ("en_IN")
for i in range(5):
    print(fake.name(), "|", fake.phone_number(), "|", fake.email())
