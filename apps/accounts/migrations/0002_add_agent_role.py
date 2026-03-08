from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("farmer",   "Farmer"),
                    ("consumer", "Consumer"),
                    ("admin",    "Admin"),
                    ("agent",    "Delivery Agent"),
                ],
                default="consumer",
                max_length=10,
            ),
        ),
    ]
