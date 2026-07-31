
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('day', '0006_shift_approved_late_min'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
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
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
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
