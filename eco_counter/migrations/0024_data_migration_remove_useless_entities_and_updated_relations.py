"""
Data migration that removes useless Year, Month, Week and Day rows after
station relationships are removed. Updates also the relationships in rows
that are kept. Note, might be take a while, if all counter data is imported.
"""

from django.db import migrations, transaction


def get_year_key(year):
    return str(year.year_number)


def get_month_key(month):
    return str(month.year.year_number) + "_" + str(month.month_number)


def get_week_key(week):
    return (
        "_".join([str(y.year_number) for y in week.years.all()])
        + "_"
        + str(week.week_number)
    )


def get_day_key(day):
    return (
        str(day.year.year_number)
        + "_"
        + str(day.month.month_number)
        + "_"
        + str(day.week.week_number)
        + "_"
        + str(day.date)
    )


class Migration(migrations.Migration):

    @transaction.atomic
    def fix_models(apps, schema_editor):
        YearModel = apps.get_model("eco_counter", "Year")
        YearDataModel = apps.get_model("eco_counter", "YearData")
        MonthModel = apps.get_model("eco_counter", "Month")
        MonthDataModel = apps.get_model("eco_counter", "MonthData")
        WeekModel = apps.get_model("eco_counter", "Week")
        WeekDataModel = apps.get_model("eco_counter", "WeekData")
        DayModel = apps.get_model("eco_counter", "Day")
        DayDataModel = apps.get_model("eco_counter", "DayData")
        HourDataModel = apps.get_model("eco_counter", "HourData")

        year_qs = YearModel.objects.all()
        month_qs = MonthModel.objects.all()
        week_qs = WeekModel.objects.all()
        day_qs = DayModel.objects.all()

        years_to_delete_ids = list(year_qs.values_list("id", flat=True))
        weeks_to_delete_ids = list(week_qs.values_list("id", flat=True))
        months_to_delete_ids = list(month_qs.values_list("id", flat=True))
        days_to_delete_ids = list(day_qs.values_list("id", flat=True))

        keep_years = {}
        keep_months = {}
        keep_weeks = {}
        keep_days = {}

        # Select rows to be kept
        for year in year_qs:
            key = get_year_key(year)
            if key not in keep_years:
                years_to_delete_ids.remove(year.id)
                keep_years[key] = year

        for month in month_qs:
            key = get_month_key(month)
            if key not in keep_months:
                keep_months[key] = month
                months_to_delete_ids.remove(month.id)

        for week in week_qs:
            key = get_week_key(week)
            if key not in keep_weeks:
                keep_weeks[key] = week
                weeks_to_delete_ids.remove(week.id)

        for day in day_qs:
            key = get_day_key(day)
            if key not in keep_days:
                keep_days[key] = day
                days_to_delete_ids.remove(day.id)

        # Update relationships in rows that are kept.
        for item in keep_months.items():
            year = keep_years[item[0].split("_")[0]]
            month = item[1]
            month.year = year
            month.save()

        for item in keep_weeks.items():
            week = item[1]
            year_numbers = item[0].split("_")[:-1]
            # Handle erroneous weeks without a year.
            if year_numbers == [""]:
                continue
            week.years.clear()
            for year_number in year_numbers:
                week.years.add(keep_years[year_number])

        for item in keep_days.items():
            year_number, month_number, week_number = item[0].split("_")[0:3]
            day = item[1]
            day.year = keep_years[year_number]
            day.month = keep_months[year_number + "_" + month_number]
            day.week = keep_weeks[year_number + "_" + week_number]
            day.save()

        # Update data models
        for year in year_qs:
            key = get_year_key(year)
            YearDataModel.objects.filter(year=year).update(year=keep_years[key])

        for month in month_qs:
            key = get_month_key(month)
            MonthDataModel.objects.filter(month=month).update(month=keep_months[key])

        for week in week_qs:
            key = get_week_key(week)
            WeekDataModel.objects.filter(week=week).update(week=keep_weeks[key])

        for day in day_qs:
            key = get_day_key(day)
            DayDataModel.objects.filter(day=day).update(day=keep_days[key])
            HourDataModel.objects.filter(day=day).update(day=keep_days[key])

        DayModel.objects.filter(id__in=days_to_delete_ids).delete()
        WeekModel.objects.filter(id__in=weeks_to_delete_ids).delete()
        MonthModel.objects.filter(id__in=months_to_delete_ids).delete()
        YearModel.objects.filter(id__in=years_to_delete_ids).delete()

    def revert_set_station_to_null(apps, schema_editor):
        pass

    dependencies = [
        ("eco_counter", "0023_alter_monthdata_options_remove_monthdata_year"),
    ]

    operations = [
        migrations.RunPython(fix_models, revert_set_station_to_null),
    ]
