import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0002_homepage"),
    ]

    operations = [
        migrations.CreateModel(
            name="DemoSnippet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255, verbose_name="title")),
                (
                    "description",
                    wagtail.fields.RichTextField(blank=True, verbose_name="description"),
                ),
            ],
            options={
                "verbose_name": "demo snippet",
                "verbose_name_plural": "demo snippets",
            },
        ),
    ]
