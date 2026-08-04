
from django.db import migrations, models

CONVERT_SQL = """
    DO $$
    BEGIN
        IF (
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'day_shift'
              AND column_name = 'approved_late_min'
        ) = 'time without time zone' THEN
            ALTER TABLE "day_shift"
            ALTER COLUMN "approved_late_min" TYPE integer
            USING CASE
                WHEN "approved_late_min" IS NULL THEN 15
                ELSE (
                    EXTRACT(HOUR FROM "approved_late_min")::integer * 60 +
                    EXTRACT(MINUTE FROM "approved_late_min")::integer
                )
            END;
            ALTER TABLE "day_shift" ALTER COLUMN "approved_late_min" SET NOT NULL;
            ALTER TABLE "day_shift" ALTER COLUMN "approved_late_min" SET DEFAULT 15;
        END IF;
    END $$;
"""


def convert_approved_late_min(apps, schema_editor):
    # DO $$ bloki faqat PostgreSQL'da ishlaydi; SQLite (test) dinamik tipli,
    # unda konvertatsiya shart emas.
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(CONVERT_SQL)


class Migration(migrations.Migration):

    dependencies = [
        ('day', '0006_shift_approved_late_min'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(convert_approved_late_min, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='shift',
                    name='approved_late_min',
                    field=models.PositiveIntegerField(default=15),
                ),
            ],
        ),
    ]
