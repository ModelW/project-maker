# Generated by Django 4.2.13 on 2024-08-28 20:50

from django.db import migrations, models
import django.db.models.deletion
import wagtail.blocks
import wagtail.fields
import wagtail.images.models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0093_uploadedfile"),
        ("cms", "0002_homepage"),
    ]

    operations = [
        migrations.CreateModel(
            name="DemoPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
                (
                    "tagline",
                    models.CharField(
                        help_text="This is a required tagline", max_length=255
                    ),
                ),
                (
                    "description",
                    wagtail.fields.RichTextField(
                        blank=True, help_text="This is an optional description"
                    ),
                ),
                (
                    "blocks",
                    wagtail.fields.StreamField(
                        [
                            (
                                "DemoBlock",
                                wagtail.blocks.StructBlock(
                                    [
                                        (
                                            "tagline",
                                            wagtail.blocks.CharBlock(
                                                help_text="This is a required tagline",
                                                max_length=255,
                                                required=True,
                                            ),
                                        ),
                                        (
                                            "description",
                                            wagtail.blocks.RichTextBlock(
                                                help_text="This is an optional description",
                                                required=False,
                                            ),
                                        ),
                                        (
                                            "blocks",
                                            wagtail.blocks.StreamBlock(
                                                [
                                                    (
                                                        "DemoSubBlock",
                                                        wagtail.blocks.StructBlock(
                                                            [
                                                                (
                                                                    "tagline",
                                                                    wagtail.blocks.CharBlock(
                                                                        help_text="This is a required tagline",
                                                                        max_length=255,
                                                                        required=True,
                                                                    ),
                                                                ),
                                                                (
                                                                    "description",
                                                                    wagtail.blocks.RichTextBlock(
                                                                        help_text="This is an optional description",
                                                                        required=False,
                                                                    ),
                                                                ),
                                                                (
                                                                    "blocks",
                                                                    wagtail.blocks.StreamBlock(
                                                                        [
                                                                            (
                                                                                "Heading",
                                                                                wagtail.blocks.CharBlock(),
                                                                            )
                                                                        ],
                                                                        required=False,
                                                                    ),
                                                                ),
                                                            ]
                                                        ),
                                                    )
                                                ],
                                                required=False,
                                            ),
                                        ),
                                    ]
                                ),
                            )
                        ],
                        blank=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Demo Page",
                "verbose_name_plural": "Demo Pages",
            },
            bases=("wagtailcore.page",),
        ),
        migrations.AlterField(
            model_name="customrendition",
            name="file",
            field=wagtail.images.models.WagtailImageField(
                height_field="height",
                storage=wagtail.images.models.get_rendition_storage,
                upload_to=wagtail.images.models.get_rendition_upload_to,
                width_field="width",
            ),
        ),
    ]